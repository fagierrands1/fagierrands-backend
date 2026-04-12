"""
Enhanced Order Creation with Pricing Breakdown
Handles simple parcel delivery with transparent pricing
"""
from rest_framework import status, generics, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal
from .models import Order, OrderType, ShoppingItem, OrderImage
from .serializers import PickupDeliveryOrderSerializer
import logging

logger = logging.getLogger(__name__)


class EnhancedPickupDeliveryOrderView(APIView):
    """
    Enhanced order creation with transparent pricing breakdown
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_type_id', 'title', 'pickup_address', 'delivery_address', 'distance', 'approximate_value', 'items'],
            properties={
                'order_type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order type ID (2 for Delivery)'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Order title'),
                'additional_description': openapi.Schema(type=openapi.TYPE_STRING, description='Optional notes'),
                'pickup_address': openapi.Schema(type=openapi.TYPE_STRING, description='Pickup address'),
                'delivery_address': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery address'),
                'pickup_latitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Pickup GPS latitude'),
                'pickup_longitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Pickup GPS longitude'),
                'delivery_latitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Delivery GPS latitude'),
                'delivery_longitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Delivery GPS longitude'),
                'recipient_name': openapi.Schema(type=openapi.TYPE_STRING, description='Recipient name'),
                'contact_number': openapi.Schema(type=openapi.TYPE_STRING, description='Contact phone number'),
                'distance': openapi.Schema(type=openapi.TYPE_NUMBER, description='Distance in km'),
                'approximate_value': openapi.Schema(type=openapi.TYPE_NUMBER, description='Estimated item value (KSh)'),
                'items': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    ),
                    description='List of items to deliver'
                ),
                'pickup_notes': openapi.Schema(type=openapi.TYPE_STRING, description='Optional pickup instructions'),
                'delivery_notes': openapi.Schema(type=openapi.TYPE_STRING, description='Optional delivery instructions'),
            }
        ),
        responses={
            201: openapi.Response(
                'Order created successfully',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'order_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'pricing_breakdown': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'base_fee': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'distance_fee': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'heavy_load_surcharge': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'total': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'distance_km': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        ),
                        'items': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'next_step': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Bad request'
        }
    )
    def post(self, request):
        """Create a pickup/delivery order with transparent pricing"""
        
        # Validate input
        serializer = PickupDeliveryOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Get order type
        order_type = data['order_type_id']
        distance = data.get('distance', 0)
        
        # Calculate pricing breakdown
        pricing = self.calculate_pricing_breakdown(distance, order_type)
        
        # Create order
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
            status='pending'
        )
        
        # Create shopping items
        items_created = []
        for item_data in data['items']:
            item = ShoppingItem.objects.create(
                order=order,
                name=item_data['name'],
                quantity=item_data.get('quantity', 1)
            )
            items_created.append({
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity
            })
        
        # Send SMS notification to client
        self.send_order_confirmation_sms(request.user, order, pricing)
        
        logger.info(f"Order {order.id} created by {request.user.username} - Price: KSh {pricing['total']}")
        
        return Response({
            'order_id': order.id,
            'title': order.title,
            'status': order.status,
            'pricing_breakdown': pricing,
            'items': items_created,
            'pickup_address': order.pickup_address,
            'delivery_address': order.delivery_address,
            'recipient_name': order.recipient_name,
            'contact_number': order.contact_number,
            'next_step': 'Upload item images (optional) at /api/orders/{order_id}/images/'
        }, status=status.HTTP_201_CREATED)
    
    def send_order_confirmation_sms(self, user, order, pricing):
        """Send SMS confirmation to client"""
        from accounts.services.sms_service import SMSService
        
        phone_number = user.phone_number
        if not phone_number:
            logger.warning(f"No phone number for user {user.username}, skipping SMS")
            return
        
        # Format SMS message
        message = (
            f"FagiErrands Order Confirmed!\n"
            f"Order ID: #{order.id}\n"
            f"Type: {order.order_type.name}\n"
            f"Price: KSh {pricing['total']:.0f}\n"
            f"From: {order.pickup_address[:30]}...\n"
            f"To: {order.delivery_address[:30]}...\n"
            f"Status: Pending\n"
            f"Track: fagierrands.com/orders/{order.id}"
        )
        
        try:
            # Send SMS using TextPie
            response = SMSService.send_sms(phone_number, message)
            if response.get('status_code') == '1000':
                logger.info(f"Order confirmation SMS sent to {phone_number}")
            else:
                logger.error(f"Failed to send SMS: {response.get('status_desc')}")
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
            # Don't fail order creation if SMS fails
    
    def calculate_pricing_breakdown(self, distance_km, order_type):
        """
        Calculate transparent pricing breakdown
        
        Rules:
        - Normal delivery (ID: 1): KSh 200 base (first 7km)
        - Cargo delivery (ID: 2): KSh 300 base (first 7km)
        - Cheque banking (ID: 3): KSh 200 base (first 7km)
        - Distance fee: KSh 20/km (after 7km)
        - Heavy load surcharge: KSh 100 (if >15kg) - future feature
        """
        distance = Decimal(str(distance_km)) if distance_km else Decimal('0')
        
        # Cargo Delivery (ID: 2) has higher base price
        if order_type.id == 2 or order_type.name == 'Cargo Delivery':
            base_fee = Decimal('300.00')
        else:
            base_fee = Decimal('200.00')
        
        distance_fee = Decimal('0.00')
        heavy_surcharge = Decimal('0.00')
        
        if distance > 7:
            extra_km = distance - Decimal('7')
            distance_fee = extra_km * Decimal('20.00')
        
        total = base_fee + distance_fee + heavy_surcharge
        
        return {
            'base_fee': float(base_fee),
            'distance_fee': float(distance_fee),
            'heavy_load_surcharge': float(heavy_surcharge),
            'total': float(total),
            'distance_km': float(distance)
        }


class PriceCalculationView(APIView):
    """
    Calculate price before order creation
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_type_id', 'distance'],
            properties={
                'order_type_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'distance': openapi.Schema(type=openapi.TYPE_NUMBER, description='Distance in km'),
                'is_heavy': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is cargo >15kg?', default=False)
            }
        ),
        responses={200: 'Price breakdown'}
    )
    def post(self, request):
        """Calculate price with breakdown"""
        order_type_id = request.data.get('order_type_id')
        distance = request.data.get('distance', 0)
        is_heavy = request.data.get('is_heavy', False)
        
        if not order_type_id:
            return Response({'error': 'order_type_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order_type = OrderType.objects.get(id=order_type_id)
        except OrderType.DoesNotExist:
            return Response({'error': 'Invalid order type'}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate pricing based on order type
        distance_decimal = Decimal(str(distance)) if distance else Decimal('0')
        
        # Cargo Delivery (ID: 2) has higher base price
        if order_type.id == 2 or order_type.name == 'Cargo Delivery':
            base_fee = Decimal('300.00')  # Cargo base price
            calculation_note = 'Cargo Delivery base price'
        else:
            base_fee = Decimal('200.00')  # Regular base price
            calculation_note = 'Regular delivery base price'
        
        # Calculate distance fee
        distance_fee = Decimal('0.00')
        if distance_decimal > 7:
            extra_km = distance_decimal - Decimal('7')
            distance_fee = extra_km * Decimal('20.00')
        
        # Heavy load surcharge (additional to cargo base)
        heavy_surcharge = Decimal('100.00') if is_heavy else Decimal('0.00')
        
        total = base_fee + distance_fee + heavy_surcharge
        
        return Response({
            'order_type': order_type.name,
            'pricing_breakdown': {
                'base_fee': float(base_fee),
                'distance_fee': float(distance_fee),
                'heavy_load_surcharge': float(heavy_surcharge),
                'total': float(total)
            },
            'distance_km': float(distance_decimal),
            'calculation_details': {
                'base_fee_rule': f'{calculation_note}: KSh {float(base_fee)} for first 7km',
                'distance_fee_rule': 'KSh 20 per km after 7km',
                'heavy_surcharge_rule': 'KSh 100 if cargo >15kg (additional)'
            }
        }, status=status.HTTP_200_OK)


class EnhancedOrderImageUploadView(APIView):
    """
    Upload order images with validation
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('order_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description='Order ID'),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Image file'),
            openapi.Parameter('stage', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Image stage: before, during, or after'),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Optional caption')
        ],
        responses={
            201: 'Image uploaded successfully',
            404: 'Order not found',
            403: 'Not authorized'
        }
    )
    def post(self, request, order_id):
        """Upload image for order"""
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check authorization
        if order.client != request.user and order.assistant != request.user:
            return Response({'error': 'Not authorized to upload images for this order'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        image = request.FILES.get('image')
        stage = request.data.get('stage', 'before')
        caption = request.data.get('caption', '')
        
        if not image:
            return Response({'error': 'Image file is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if stage not in ['before', 'during', 'after']:
            return Response({'error': 'Invalid stage. Must be: before, during, or after'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create image record
        order_image = OrderImage.objects.create(
            order=order,
            image=image,
            stage=stage,
            caption=caption,
            uploaded_by=request.user
        )
        
        logger.info(f"Image uploaded for order {order_id} - Stage: {stage}")
        
        return Response({
            'message': 'Image uploaded successfully',
            'image_id': order_image.id,
            'stage': order_image.stage,
            'caption': order_image.caption,
            'uploaded_at': order_image.uploaded_at
        }, status=status.HTTP_201_CREATED)
