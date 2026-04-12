"""
3-Step Order Creation Process
Step 1: Create draft order (form data)
Step 2: Upload images (evidence capture)
Step 3: Confirm order (place errand)
"""
from rest_framework import status, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal
from django.utils import timezone
from .models import Order, OrderType, ShoppingItem, OrderImage
from .serializers import PickupDeliveryOrderSerializer
import logging

logger = logging.getLogger(__name__)


class CreateDraftOrderView(APIView):
    """
    Step 1: Create draft order with form data
    Returns order_id for next steps
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_type_id', 'title', 'pickup_address', 'delivery_address', 'distance', 'approximate_value', 'items'],
            properties={
                'order_type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order type ID'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Order title'),
                'additional_description': openapi.Schema(type=openapi.TYPE_STRING, description='Optional notes'),
                'pickup_address': openapi.Schema(type=openapi.TYPE_STRING, description='Pickup address'),
                'delivery_address': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery address'),
                'pickup_latitude': openapi.Schema(type=openapi.TYPE_NUMBER),
                'pickup_longitude': openapi.Schema(type=openapi.TYPE_NUMBER),
                'delivery_latitude': openapi.Schema(type=openapi.TYPE_NUMBER),
                'delivery_longitude': openapi.Schema(type=openapi.TYPE_NUMBER),
                'recipient_name': openapi.Schema(type=openapi.TYPE_STRING),
                'contact_number': openapi.Schema(type=openapi.TYPE_STRING),
                'distance': openapi.Schema(type=openapi.TYPE_NUMBER, description='Distance in km'),
                'approximate_value': openapi.Schema(type=openapi.TYPE_NUMBER, description='Item value'),
                'items': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                )
            }
        ),
        responses={
            201: openapi.Response(
                'Draft order created',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'order_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'pricing_breakdown': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'next_step': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def post(self, request):
        """Create draft order (Step 1)"""
        
        # Validate input
        serializer = PickupDeliveryOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        order_type = data['order_type_id']
        distance = data.get('distance', 0)
        
        # Calculate pricing
        pricing = self.calculate_pricing(distance, order_type)
        
        # Create DRAFT order (status = pending, not yet confirmed)
        # Use _skip_notification flag to prevent SMS during draft creation
        order = Order.objects.create(
            client=request.user,
            order_type=order_type,
            title=data['title'],
            description=data.get('additional_description', ''),
            pickup_address=data['pickup_address'],
            delivery_address=data['delivery_address'],
            pickup_latitude=data.get('pickup_latitude'),
            pickup_longitude=data.get('pickup_longitude'),
            delivery_latitude=data.get('delivery_latitude'),
            delivery_longitude=data.get('delivery_longitude'),
            recipient_name=data.get('recipient_name', ''),
            contact_number=data.get('contact_number', ''),
            distance=distance,
            price=pricing['total'],
            estimated_value=data['approximate_value'],
            status='pending'  # Draft status
        )
        
        # Mark as draft to skip notifications
        order._is_draft = True
        order.save()
        
        # Create items
        for item_data in data['items']:
            ShoppingItem.objects.create(
                order=order,
                name=item_data['name'],
                quantity=item_data.get('quantity', 1)
            )
        
        logger.info(f"Draft order {order.id} created by {request.user.username}")
        
        return Response({
            'order_id': order.id,
            'status': 'draft',
            'pricing_breakdown': pricing,
            'next_step': 'Upload images at /api/orders/v1/{order_id}/upload-image/',
            'message': 'Draft order created. Please upload images next.'
        }, status=status.HTTP_201_CREATED)
    
    def calculate_pricing(self, distance_km, order_type):
        """Calculate pricing breakdown"""
        distance = Decimal(str(distance_km)) if distance_km else Decimal('0')
        
        # Cargo (ID: 2) has higher base
        if order_type.id == 2 or order_type.name == 'Cargo Delivery':
            base_fee = Decimal('300.00')
        else:
            base_fee = Decimal('200.00')
        
        distance_fee = Decimal('0.00')
        if distance > 7:
            extra_km = distance - Decimal('7')
            distance_fee = extra_km * Decimal('20.00')
        
        total = base_fee + distance_fee
        
        return {
            'base_fee': float(base_fee),
            'distance_fee': float(distance_fee),
            'heavy_load_surcharge': 0.0,
            'total': float(total),
            'distance_km': float(distance)
        }


class UploadOrderImageView(APIView):
    """
    Step 2: Upload images for the order
    Can be called multiple times to upload multiple images
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('order_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description='Order ID'),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Image file'),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Optional description')
        ],
        responses={
            201: 'Image uploaded successfully',
            404: 'Order not found',
            403: 'Not authorized'
        }
    )
    def post(self, request, order_id):
        """Upload image for order (Step 2)"""
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check authorization
        if order.client != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        image = request.FILES.get('image')
        caption = request.data.get('caption', '')
        
        if not image:
            return Response({'error': 'Image file is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create image record (stage: before - client uploading before order confirmation)
        order_image = OrderImage.objects.create(
            order=order,
            image=image,
            stage='before',  # Client uploads are always "before"
            description=caption
        )
        
        logger.info(f"Image uploaded for order {order_id}")
        
        # Check if order has images now
        image_count = order.images.count()
        
        return Response({
            'message': 'Image uploaded successfully',
            'image_id': order_image.id,
            'description': order_image.description,
            'uploaded_at': order_image.uploaded_at,
            'total_images': image_count,
            'next_step': 'Confirm order at /api/orders/v1/{order_id}/confirm/'
        }, status=status.HTTP_201_CREATED)


class ConfirmOrderView(APIView):
    """
    Step 3: Confirm and place the order
    Sends SMS notification to client
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('order_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description='Order ID')
        ],
        responses={
            200: openapi.Response(
                'Order confirmed and placed',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'order_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: 'Order not found',
            403: 'Not authorized',
            400: 'Order already confirmed or no images uploaded'
        }
    )
    def post(self, request, order_id):
        """Confirm order and place errand (Step 3)"""
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check authorization
        if order.client != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if images uploaded
        if order.images.count() == 0:
            return Response({
                'error': 'Please upload at least one image before confirming order'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirm order (already pending, just mark as confirmed)
        order.status = 'pending'
        order.save()
        
        # Send notification (manually since we skipped it during draft creation)
        from notifications.services_sync import NotificationServiceSync as NotificationService
        NotificationService.create_notification(
            recipient=request.user,
            notification_type='order_created',
            title='Order Created',
            message=f'Your order "{order.title}" has been created successfully.',
            content_object=order
        )
        
        # Send SMS notification
        self.send_order_confirmation_sms(request.user, order)
        
        logger.info(f"Order {order.id} confirmed by {request.user.username}")
        
        return Response({
            'order_id': order.id,
            'status': order.status,
            'message': 'Order confirmed and placed successfully!',
            'pricing': {
                'total': float(order.price),
                'distance_km': float(order.distance)
            },
            'images_uploaded': order.images.count(),
            'next_step': 'Wait for assistant assignment'
        }, status=status.HTTP_200_OK)
    
    def send_order_confirmation_sms(self, user, order):
        """Send SMS confirmation to client"""
        from accounts.services.sms_service import SMSService
        
        phone_number = user.phone_number
        if not phone_number:
            return
        
        message = (
            f"FagiErrands Order Confirmed!\n"
            f"Order ID: #{order.id}\n"
            f"Type: {order.order_type.name}\n"
            f"Price: KSh {order.price:.0f}\n"
            f"From: {order.pickup_address[:30]}...\n"
            f"To: {order.delivery_address[:30]}...\n"
            f"Status: Pending\n"
            f"Track: fagierrands.com/orders/{order.id}"
        )
        
        try:
            response = SMSService.send_sms(phone_number, message)
            if response.get('status_code') == '1000':
                logger.info(f"Order confirmation SMS sent to {phone_number}")
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
