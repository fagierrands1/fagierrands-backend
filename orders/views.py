from rest_framework import generics, permissions, status, filters, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Q
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from decimal import Decimal, InvalidOperation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
import json

logger = logging.getLogger(__name__)
from .models import (
    OrderType, Order, ShoppingItem, OrderImage, OrderReview, 
    CargoDeliveryDetails, HandymanServiceType, HandymanOrder, 
    HandymanOrderImage, HandymanServiceTypes, Payment, Banks, BankingOrder
)
from locations.models import Location
from .serializers import (
    OrderTypeSerializer, OrderSerializer, ShoppingItemSerializer,
    OrderImageSerializer, OrderReviewSerializer, PickupDeliveryOrderSerializer,
    CargoDeliveryOrderSerializer, CargoDeliveryDetailsSerializer, OrderStatusUpdateSerializer, AssignOrderSerializer,
    HandlerOrderListSerializer
)
from accounts.permissions import IsOwnerOrReadOnly, IsHandler, IsAssistant, IsClient, IsAdmin, IsAuthenticated

User = get_user_model()

def get_client_user(request):
    """
    Helper function to get the client user for order creation.
    If client_id is provided and the requester is a handler, return that client.
    Otherwise, return the requesting user.
    """
    client_id = request.data.get('client_id')
    requester = request.user
    
    # If client_id is provided and requester is a handler/admin
    if client_id and requester.user_type in ['handler', 'admin']:
        try:
            client = User.objects.get(id=client_id)
            # Verify the handler has permission (client is assigned to them)
            if requester.user_type == 'handler':
                if client.account_manager != requester:
                    raise PermissionDenied("You can only place orders for clients assigned to you")
            return client
        except User.DoesNotExist:
            raise ValidationError(f"Client with id {client_id} not found")
    
    # Default: return the requesting user
    return requester

def deployment_check_view(request):
    return render(request, 'deployment_check.html')

class AppVersionsView(APIView):
    """
    Lightweight endpoint for mobile app to check the latest published versions.
    Values are driven via environment variables to avoid code changes for each release.
      - APP_UPDATE_IOS_BUILD (string)
      - APP_UPDATE_ANDROID_CODE (number)
      - APP_UPDATE_URL_ANDROID (string, optional)
      - APP_UPDATE_URL_IOS (string, optional)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import os
        ios_build = os.environ.get('APP_UPDATE_IOS_BUILD') or os.environ.get('IOS_BUILD') or ''
        android_code = os.environ.get('APP_UPDATE_ANDROID_CODE') or os.environ.get('ANDROID_CODE') or '0'
        try:
            android_code_int = int(android_code)
        except Exception:
            android_code_int = 0
        update_url_android = os.environ.get('APP_UPDATE_URL_ANDROID') or 'market://details?id=com.fagierrand.fagitone'
        update_url_ios = os.environ.get('APP_UPDATE_URL_IOS') or 'itms-apps://itunes.apple.com/app/idYOUR_APP_ID'
        return Response({
            'iosBuild': str(ios_build),
            'androidCode': android_code_int,
            'updateUrlAndroid': update_url_android,
            'updateUrlIos': update_url_ios,
        })


class OrderTypeListView(generics.ListAPIView):
    """
    API endpoint that returns all order types.
    If no order types exist, returns an empty list rather than null.
    """
    queryset = OrderType.objects.all()
    serializer_class = OrderTypeSerializer
    permission_classes = [permissions.AllowAny]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # If no order types exist, ensure we return an empty list instead of null
        if not queryset.exists():
            return Response([])
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = HandlerOrderListSerializer  # lighter for lists
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'order_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'price']
    ordering = ['-created_at']  # Default ordering: most recent first
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset with optimized loading of related objects
        base_queryset = (
            Order.objects.select_related('client', 'assistant', 'order_type')
            .only(
                'id', 'title', 'status', 'price', 'created_at',
                'pickup_address', 'delivery_address',
                'assigned_at', 'started_at', 'completed_at',
                'client__id', 'client__first_name', 'client__last_name', 'client__username', 'client__email',
                'assistant__id', 'assistant__first_name', 'assistant__last_name', 'assistant__username', 'assistant__email',
                'order_type__name'
            )
            .prefetch_related('shopping_items')
        )
        
        if user.user_type == 'user':
            # Client: see own orders
            return base_queryset.filter(client=user)
        elif user.user_type == 'assistant':
            # Assistant: see assigned orders
            return base_queryset.filter(assistant=user)
        elif user.user_type in ['handler', 'admin']:
            # Handler/Admin: see all orders
            return base_queryset.all()
        
        return Order.objects.none()
    
    def get_serializer_class(self):
        # Use full serializer for creation/detail
        if self.request.method in ['POST']:
            return OrderSerializer
        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        # Set the client - can be the authenticated user or a client_id if handler is placing order
        client = get_client_user(self.request)
        serializer.save(client=client)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset with optimized loading of related objects
        base_queryset = Order.objects.select_related(
            'client', 'assistant', 'handler', 'order_type', 
            'pickup_location', 'delivery_location'
        ).prefetch_related(
            'shopping_items', 'images', 'review', 'cargo_details'
        )
        
        if user.user_type == 'user':
            # Client: see own orders
            return base_queryset.filter(client=user)
        elif user.user_type == 'assistant':
            # Assistant: see assigned orders
            return base_queryset.filter(assistant=user)
        elif user.user_type in ['handler', 'admin']:
            # Handler/Admin: see all orders
            return base_queryset.all()
        
        return Order.objects.none()
    
    def perform_destroy(self, instance):
        if instance.status not in ['pending', 'cancelled']:
            return Response(
                {"error": "Only pending or cancelled orders can be deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()

class OrderStatusUpdateView(generics.UpdateAPIView):
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'user':
            # Client: can only mark as completed or cancelled
            return Order.objects.filter(client=user, status__in=['in_progress', 'assigned'])
        elif user.user_type == 'assistant':
            # Assistant: can mark as in_progress or completed
            return Order.objects.filter(assistant=user, status__in=['assigned', 'in_progress'])
        elif user.user_type in ['handler', 'admin']:
            # Handler/Admin: can change any status
            return Order.objects.all()
        
        return Order.objects.none()
    
    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        
        # Check user permissions for status updates
        new_status = serializer.validated_data.get('status')
        
        if user.user_type == 'user' and new_status not in ['completed', 'cancelled']:
            return Response(
                {"error": "Clients can only mark orders as completed or cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif user.user_type == 'assistant' and new_status not in ['in_progress', 'completed']:
            return Response(
                {"error": "Assistants can only mark orders as in progress or completed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For assistants changing to in_progress, make sure they're assigned
        if user.user_type == 'assistant' and new_status == 'in_progress' and instance.assistant != user:
            return Response(
                {"error": "You can only change status of orders assigned to you"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If assistant is starting the order, allow setting pickup location from current coordinates
        try:
            pickup_lat = self.request.data.get('pickup_latitude')
            pickup_lon = self.request.data.get('pickup_longitude')
            pickup_addr = self.request.data.get('pickup_address')
            if user.user_type == 'assistant' and new_status in ['in_progress', 'assigned'] and pickup_lat is not None and pickup_lon is not None:
                try:
                    instance.pickup_latitude = float(pickup_lat)
                    instance.pickup_longitude = float(pickup_lon)
                    if pickup_addr:
                        instance.pickup_address = str(pickup_addr)
                    instance.save(update_fields=['pickup_latitude', 'pickup_longitude', 'pickup_address'])
                except Exception:
                    pass
        except Exception:
            pass
        
        # Special logic adjusted for Shopping: serializer handles computing final price and deciding payment_pending vs completed.
        # Keep generic fallback only for non-shopping where we need payment confirmation flows.
        
        serializer.save()
        
        # After status update, if we have both pickup and delivery coordinates, compute distance/price
        try:
            instance.refresh_from_db()
            if instance.status in ['assigned', 'in_progress'] \
               and instance.pickup_latitude is not None and instance.pickup_longitude is not None \
               and instance.delivery_latitude is not None and instance.delivery_longitude is not None:
                # Update distance and estimated duration
                instance.calculate_distance()
                # DISABLED: Recalculate price once initial distance is known (do not finalize, allow realtime updates later)
                pass
                # instance.update_price()
        except Exception:
            pass

class AssignOrderView(generics.UpdateAPIView):
    serializer_class = AssignOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]
    
    def get_queryset(self):
        return Order.objects.filter(status='pending')
    
    def update(self, request, *args, **kwargs):
        """Override to return rider details after assignment"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Get updated instance with rider details
        instance.refresh_from_db()
        rider = instance.assistant
        profile = getattr(rider, 'profile', None) if rider else None
        
        response_data = {
            'message': 'Rider assigned successfully',
            'order_id': instance.id,
            'status': instance.status,
            'rider': {
                'id': rider.id,
                'name': f"{rider.first_name} {rider.last_name}".strip() or rider.username,
                'phone_number': rider.phone_number or 'N/A',
                'plate_number': profile.plate_number if profile else None,
                'profile_picture': profile.profile_picture_url if profile else None,
            } if rider else None,
            'assigned_at': instance.assigned_at.isoformat() if instance.assigned_at else None,
        }
        
        return Response(response_data)

class ShoppingItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ShoppingItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        
        user = self.request.user
        if (user.user_type == 'user' and order.client == user) or \
           (user.user_type == 'assistant' and order.assistant == user) or \
           user.user_type in ['handler', 'admin']:
            return ShoppingItem.objects.filter(order_id=order_id)
        
        return ShoppingItem.objects.none()
    
    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        
        # Only client or handler can add shopping items
        user = self.request.user
        if user.user_type not in ['user', 'handler', 'admin'] or \
           (user.user_type == 'user' and order.client != user):
            return Response(
                {"error": "You don't have permission to add items to this order"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(order=order)
        
        # Recalculate order price when items are added
        order.update_price()

class OrderImageUploadView(generics.CreateAPIView):
    serializer_class = OrderImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return OrderImage.objects.filter(order_id=order_id)
    
    def list(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        user = request.user
        
        if not self._user_can_access_order(user, order):
            return Response(
                {"error": "You don't have permission to view images for this order"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = OrderImageSerializer(queryset, many=True, context={'request': request})
        return Response({"results": serializer.data})
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        
        user = self.request.user
        if self._user_can_access_order(user, order):
            serializer.save(order=order)
        else:
            return Response(
                {"error": "You don't have permission to upload images to this order"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def _user_can_access_order(self, user, order: Order) -> bool:
        if user.user_type in ['admin', 'handler']:
            return True
        if user.user_type == 'user' and order.client == user:
            return True
        if user.user_type == 'assistant' and order.assistant == user:
            return True
        return False

class OrderReviewCreateView(generics.CreateAPIView):
    serializer_class = OrderReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]
    
    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        
        # Check if the order is completed and belongs to the user
        if order.status != 'completed':
            return Response(
                {"error": "You can only review completed orders"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.client != self.request.user:
            return Response(
                {"error": "You can only review your own orders"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if a review already exists
        if hasattr(order, 'review'):
            return Response(
                {"error": "You have already reviewed this order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(order=order)

class PendingOrdersView(generics.ListAPIView):
    serializer_class = HandlerOrderListSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]
    
    def get_queryset(self):
        # Narrow fields and prefetch to avoid N+1
        return (
            Order.objects.filter(status='pending')
            .select_related('client', 'assistant', 'order_type')
            .only(
                'id', 'status', 'price', 'created_at', 'updated_at',
                'pickup_address', 'delivery_address',
                'assigned_at', 'started_at', 'completed_at',
                'client__id', 'client__first_name', 'client__last_name', 'client__username', 'client__email',
                'assistant__id', 'assistant__first_name', 'assistant__last_name', 'assistant__username', 'assistant__email',
                'order_type__name'
            )
            .prefetch_related('shopping_items')
            .order_by('-created_at')
        )

class AssistantOrdersView(generics.ListAPIView):
    serializer_class = HandlerOrderListSerializer  # lighter list payload
    permission_classes = [permissions.IsAuthenticated, IsAssistant]
    
    def get_queryset(self):
        # Orders assigned to this assistant
        return (
            Order.objects.filter(assistant=self.request.user)
            .select_related('client', 'assistant', 'order_type')
            .only(
                'id', 'status', 'price', 'created_at', 'updated_at',
                'pickup_address', 'delivery_address',
                'assigned_at', 'started_at', 'completed_at',
                'client__id', 'client__first_name', 'client__last_name', 'client__username', 'client__email',
                'assistant__id', 'assistant__first_name', 'assistant__last_name', 'assistant__username', 'assistant__email',
                'order_type__name'
            )
            .prefetch_related('shopping_items')
            .order_by('-created_at')
        )

class AvailableOrdersView(generics.ListAPIView):
    """
    API endpoint for assistants to view available orders (pending orders without assignment)
    """
    serializer_class = HandlerOrderListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistant]
    
    def get_queryset(self):
        # Return pending orders that are not assigned to any assistant
        return (
            Order.objects.filter(status='pending', assistant__isnull=True)
            .select_related('client', 'order_type')
            .only(
                'id', 'status', 'price', 'created_at', 'updated_at',
                'pickup_address', 'delivery_address',
                'client__id', 'client__first_name', 'client__last_name', 'client__username', 'client__email',
                'order_type__name'
            )
            .prefetch_related('shopping_items')
            .order_by('-created_at')
        )

class AcceptOrderView(APIView):
    """
    API endpoint for assistants to accept available orders
    """
    permission_classes = [permissions.IsAuthenticated, IsAssistant]
    
    def post(self, request, pk):
        try:
            # Get the order
            order = Order.objects.get(pk=pk, status='pending', assistant__isnull=True)
            
            # Assign the order to the current assistant and change status to assigned
            order.assistant = request.user
            order.status = 'assigned'
            order.save()
            
            # Return the updated order
            serializer = OrderSerializer(order, context={'request': request})
            return Response({
                'success': True,
                'message': 'Order accepted successfully',
                'order': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found or already assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error accepting order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# New views for shopping functionality
class ShoppingOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        try:
            # Extract order data
            order_type_id = request.data.get('order_type')
            title = request.data.get('title', 'Shopping Order')
            description = request.data.get('description', '')

            # Extract location data
            pickup_address = request.data.get('pickup_address', '')
            pickup_latitude = request.data.get('pickup_latitude')
            pickup_longitude = request.data.get('pickup_longitude')
            delivery_address = request.data.get('delivery_address', '')
            delivery_latitude = request.data.get('delivery_latitude')
            delivery_longitude = request.data.get('delivery_longitude')

            # Contact details
            contact_name = request.data.get('contact_name', '')
            contact_phone = request.data.get('contact_phone', '')

            # Shopping items
            items_data = request.data.get('items', [])
            if isinstance(items_data, str):
                try:
                    items_data = json.loads(items_data)
                except (json.JSONDecodeError, TypeError):
                    items_data = []
            
            # Mandatory item valuation check
            if not items_data:
                return Response({'error': 'Please add at least one item to your shopping list'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract names and prices to verify valuation
            total_items_val = 0
            for it in items_data:
                try:
                    total_items_val += float(it.get('price', 0)) * int(it.get('quantity', 1))
                except (ValueError, TypeError):
                    continue
            
            if total_items_val <= 0:
                return Response({'error': 'Approximate value is required for shopping items'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate that payment details are provided to auto-initiate
            payment_method = request.data.get('payment_method')
            phone_number = request.data.get('phone_number')
            email = request.data.get('email')
            if payment_method in ['mpesa', 'ncba'] and not phone_number:
                return Response({'error': 'phone_number is required for M-Pesa/NCBA deposit'}, status=status.HTTP_400_BAD_REQUEST)
            if payment_method == 'card' and not email:
                return Response({'error': 'email is required for card deposit'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Get the client user (can be different if handler is placing order for client)
                client = get_client_user(request)
                
                # Create the Order first
                order = Order.objects.create(
                    client=client,
                    order_type_id=order_type_id,
                    title=title,
                    description=description + (f"\nAlternative Contact: {contact_name}\nPhone: {contact_phone}" if contact_name or contact_phone else ''),
                    pickup_address=pickup_address,
                    pickup_latitude=pickup_latitude,
                    pickup_longitude=pickup_longitude,
                    delivery_address=delivery_address,
                    delivery_latitude=delivery_latitude,
                    delivery_longitude=delivery_longitude,
                    recipient_name=contact_name,
                    contact_number=contact_phone,
                    status='pending'
                )

                # Create shopping items
                total_items_price = 0
                for item_data in items_data:
                    try:
                        name = item_data.get('name', '')
                        quantity = int(item_data.get('quantity', 1))
                        price = float(item_data.get('price', 0))
                        ShoppingItem.objects.create(
                            order=order,
                            name=name,
                            description=item_data.get('description', ''),
                            quantity=quantity,
                            price=price
                        )
                        total_items_price += quantity * price
                    except Exception as e:
                        logger.error(f"Failed to create shopping item: {e}")
                        continue

                # Calculate order price on initial creation
                order.price = order.calculate_price()
                order.price_finalized = True
                order.save()

                # Ensure we have a valid total amount
                total_amount = order.price
                if total_amount is None or total_amount <= 0:
                    # Fallback: calculate from items if order.price is not set
                    # Use the order type's base_price instead of hardcoded value
                    base_price = order.order_type.base_price if order.order_type else Decimal('200.00')
                    total_amount = Decimal(str(total_items_price)) + base_price  # Items + base delivery fee
                    order.price = total_amount
                    order.price_finalized = True
                    order.save()

                # Handle attachments if provided
                if request.FILES:
                    from .attachments_views import AttachmentUploadView
                    from accounts.cloudinary_service import get_cloudinary_service
                    import os
                    import uuid

                    service = get_cloudinary_service()
                    if service:
                        for file_key, upload in request.FILES.items():
                            # Use similar logic as AttachmentUploadView
                            content_type = upload.content_type or 'application/octet-stream'
                            if content_type == 'image':
                                content_type = 'image/jpeg'

                            ALLOWED_CONTENT_TYPES = [
                                'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
                                'image/heic', 'image/heif', 'application/pdf', 'application/octet-stream'
                            ]

                            if content_type not in ALLOWED_CONTENT_TYPES:
                                file_name = upload.name.lower() if upload.name else ''
                                if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif']):
                                    if file_name.endswith(('.jpg', '.jpeg')):
                                        content_type = 'image/jpeg'
                                    elif file_name.endswith('.png'):
                                        content_type = 'image/png'
                                    elif file_name.endswith('.gif'):
                                        content_type = 'image/gif'
                                    elif file_name.endswith('.webp'):
                                        content_type = 'image/webp'
                                    elif file_name.endswith(('.heic', '.heif')):
                                        content_type = 'image/heic'
                                else:
                                    continue  # Skip invalid files

                            size = upload.size
                            MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
                            if size > MAX_FILE_SIZE_BYTES:
                                continue  # Skip large files

                            safe_name = os.path.basename(upload.name).replace('..', '')
                            file_id = uuid.uuid4().hex
                            path = f"orders/{order.id}/{file_id}_{safe_name}"

                            try:
                                data = upload.read()
                                upload_folder = f"orders/{order.id}"
                                success, url, error = service.upload_file(
                                    file_content=data,
                                    filename=f"{file_id}_{safe_name}",
                                    folder=upload_folder,
                                    content_type=content_type,
                                )
                                if success:
                                    from .models import OrderAttachment
                                    OrderAttachment.objects.create(
                                        order=order,
                                        uploaded_by=request.user,
                                        file_path=url,
                                        file_name=safe_name,
                                        content_type=content_type,
                                        file_size=size,
                                    )
                            except Exception as e:
                                logger.error(f"Failed to upload attachment: {e}")
                                continue

                # Compute deposit amount (30% of items price)
                items_amount = Decimal(str(total_items_price))
                deposit_amount = (items_amount * Decimal('0.30')).quantize(Decimal('0.01'))

                # Create prepayment record linked to the order
                from .models import OrderPrepayment
                import uuid
                transaction_reference = f"FAGI-{uuid.uuid4().hex[:8].upper()}"
                prepay = OrderPrepayment.objects.create(
                    client=request.user,
                    order=order,  # Link to the created order
                    order_type_id=order_type_id,
                    title=title,
                    description=description + (f"\nAlternative Contact: {contact_name}\nPhone: {contact_phone}" if contact_name or contact_phone else ''),
                    pickup_address=pickup_address,
                    pickup_latitude=pickup_latitude,
                    pickup_longitude=pickup_longitude,
                    delivery_address=delivery_address,
                    delivery_latitude=delivery_latitude,
                    delivery_longitude=delivery_longitude,
                    items=items_data,
                    total_amount=total_amount,  # Use the calculated total_amount
                    deposit_amount=deposit_amount,
                    payment_method=payment_method,
                    transaction_reference=transaction_reference,
                    phone_number=phone_number,
                    email=email,
                )

                # Initiate NCBA Till STK Push for the deposit
                from .ncba_service import NCBAService

                ncba_service = NCBAService()

                if payment_method in ['mpesa', 'ncba']:
                    # Initiate STK Push for M-Pesa via NCBA
                    phone = phone_number
                    if phone.startswith('0'):
                        phone = '254' + phone[1:]
                    elif not phone.startswith('254'):
                        phone = '254' + phone

                    try:
                        response = ncba_service.initiate_stk_push(
                            phone_number=phone,
                            amount=float(deposit_amount),
                            account_no=prepay.transaction_reference
                        )

                        # NCBA response contains TransactionID and ReferenceID
                        transaction_id = response.get('TransactionID')
                        reference_id = response.get('ReferenceID')
                        status_code = response.get('StatusCode')

                        # Update prepayment with NCBA transaction details
                        prepay.mpesa_checkout_request_id = transaction_id # Reusing field for TransactionID
                        prepay.status = 'processing' if status_code == '0' else 'failed'
                        prepay.save()

                        if prepay.status == 'failed':
                            response_desc = response.get('StatusDescription', 'Unknown error')
                            return Response({
                                'status': 'error',
                                'message': f'Failed to initiate NCBA payment: {response_desc}',
                                'manual_payment_details': {
                                    'paybill': ncba_service.paybill_no,
                                    'account': ncba_service.till_no if ncba_service.use_till_as_account else prepay.transaction_reference,
                                    'amount': float(deposit_amount)
                                }
                            }, status=status.HTTP_400_BAD_REQUEST)

                        return Response({
                            'status': 'pending',
                            'status_code': 202,
                            'message': 'NCBA STK push sent. Check your phone to complete payment.',
                            'prepayment_reference': prepay.transaction_reference,
                            'transaction_id': transaction_id,
                            'reference_id': reference_id,
                            'deposit_amount': float(deposit_amount),
                            'total_amount': float(order.price),
                            'order_id': order.id,
                            'manual_payment_details': {
                                'paybill': ncba_service.paybill_no,
                                'account': ncba_service.till_no if ncba_service.use_till_as_account else prepay.transaction_reference
                            }
                        }, status=status.HTTP_202_ACCEPTED)

                    except Exception as e:
                        logger.error(f"STK Push initiation failed: {str(e)}")
                        prepay.status = 'failed'
                        prepay.save()
                        return Response({
                            'status': 'error',
                            'message': f'Failed to initiate payment: {str(e)}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    # Card payment - not supported via M-Pesa Daraja API
                    prepay.status = 'failed'
                    prepay.save()
                    return Response({
                        'status': 'error',
                        'message': 'Card payments are currently not supported for shopping orders. Please use M-Pesa.'
                    }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            import traceback
            return Response({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PickupDeliveryOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_type_id', 'pickup_address', 'delivery_address'],
            properties={
                'order_type_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order type ID'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Order title'),
                'pickup_address': openapi.Schema(type=openapi.TYPE_STRING, description='Pickup address'),
                'pickup_latitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Pickup latitude'),
                'pickup_longitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Pickup longitude'),
                'delivery_address': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery address'),
                'delivery_latitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Delivery latitude'),
                'delivery_longitude': openapi.Schema(type=openapi.TYPE_NUMBER, description='Delivery longitude'),
                'additional_description': openapi.Schema(type=openapi.TYPE_STRING, description='Additional details'),
                'recipient_name': openapi.Schema(type=openapi.TYPE_STRING, description='Recipient name'),
                'contact_number': openapi.Schema(type=openapi.TYPE_STRING, description='Contact number'),
                'approximate_value': openapi.Schema(type=openapi.TYPE_NUMBER, description='Estimated value'),
            }
        ),
        responses={201: 'Order created', 400: 'Bad request'}
    )
    def post(self, request, *args, **kwargs):
        serializer = PickupDeliveryOrderSerializer(data=request.data)
        
        # Print debug info
        print(f"Request data: {request.data}")
        
        if not serializer.is_valid():
            print(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve required data
            order_type_id = serializer.validated_data.get('order_type_id')
            title = serializer.validated_data.get('title')
            description = serializer.validated_data.get('additional_description', '')
            items_data = serializer.validated_data.get('items', [])
            
            # Addresses and coordinates
            pickup_address = serializer.validated_data.get('pickup_address')
            delivery_address = serializer.validated_data.get('delivery_address')
            pickup_latitude = serializer.validated_data.get('pickup_latitude')
            pickup_longitude = serializer.validated_data.get('pickup_longitude')
            delivery_latitude = serializer.validated_data.get('delivery_latitude')
            delivery_longitude = serializer.validated_data.get('delivery_longitude')
            
            # Contact details
            recipient_name = serializer.validated_data.get('recipient_name', '')
            contact_number = serializer.validated_data.get('contact_number', '')
            
            with transaction.atomic():
                # Get the client user (can be different if handler is placing order for client)
                client = get_client_user(request)
                
                # Create pickup location if coordinates are provided
                pickup_location = None
                if pickup_latitude and pickup_longitude:
                    pickup_location = Location.objects.create(
                        user=client,
                        name=f"Pickup: {pickup_address}",
                        address=pickup_address,
                        latitude=pickup_latitude,
                        longitude=pickup_longitude
                    )
                
                # Create delivery location if coordinates are provided
                delivery_location = None
                if delivery_latitude and delivery_longitude:
                    delivery_location = Location.objects.create(
                        user=client,
                        name=f"Delivery: {delivery_address}",
                        address=delivery_address,
                        latitude=delivery_latitude,
                        longitude=delivery_longitude
                    )
                
                # Get estimated value if provided
                estimated_value = serializer.validated_data.get('approximate_value')
                print(f"[PickupDeliveryOrderCreateView] Received approximate_value from request: {request.data.get('approximate_value')}")
                print(f"[PickupDeliveryOrderCreateView] Validated approximate_value: {estimated_value}")
                print(f"[PickupDeliveryOrderCreateView] Type: {type(estimated_value)}")
                
                # Create the order
                order = Order.objects.create(
                    client=client,
                    order_type=order_type_id,
                    title=title,
                    description=description,
                    pickup_location=pickup_location,
                    delivery_location=delivery_location,
                    pickup_address=pickup_address,
                    delivery_address=delivery_address,
                    pickup_latitude=pickup_latitude,
                    pickup_longitude=pickup_longitude,
                    delivery_latitude=delivery_latitude,
                    delivery_longitude=delivery_longitude,
                    recipient_name=recipient_name,
                    contact_number=contact_number,
                    estimated_value=estimated_value,
                    status='pending',
                    created_at=timezone.now()
                )
                print(f"[PickupDeliveryOrderCreateView] Order {order.id} created with estimated_value: {order.estimated_value} (type: {type(order.estimated_value)})")
                
                # Use frontend-provided distance if available, otherwise calculate it
                if 'distance' in request.data and request.data['distance']:
                    order.distance = float(request.data['distance'])
                    order.save(update_fields=['distance'])
                    distance = float(request.data['distance'])
                else:
                    # Calculate distance and price
                    distance = order.calculate_distance()
                
                # Create items
                for item_data in items_data:
                    item_price = item_data.get('price', 0)
                    ShoppingItem.objects.create(
                        order=order,
                        name=item_data.get('name', ''),
                        description=item_data.get('description', ''),
                        quantity=item_data.get('quantity', 1),
                        price=item_price
                    )
                
                # Always recalculate price on backend to ensure consistency
                # Frontend price is only used as a reference, but backend calculation is authoritative
                try:
                    calculated_price = order.calculate_price()
                    if calculated_price and calculated_price > 0:
                        order.price = calculated_price
                    else:
                        # Fallback: use a default base price if calculation fails
                        order.price = Decimal('200.00')
                    order.price_finalized = True
                    order.save(update_fields=['price', 'price_finalized'])
                    
                    # Log if frontend price differs significantly from backend calculation
                    if 'estimated_price' in request.data and request.data['estimated_price']:
                        frontend_price = Decimal(str(request.data['estimated_price']))
                        price_diff = abs(frontend_price - calculated_price)
                        if price_diff > Decimal('1.00'):  # More than 1 KSh difference
                            logger.warning(
                                f"Order {order.id}: Frontend price ({frontend_price}) differs from "
                                f"backend calculation ({calculated_price}) by {price_diff}. Using backend price."
                            )
                except Exception as e:
                    # If calculation fails, use frontend price as fallback, or default
                    logger.error(f"Failed to calculate order price: {str(e)}")
                    if 'estimated_price' in request.data and request.data['estimated_price']:
                        order.price = Decimal(str(request.data['estimated_price']))
                        logger.warning(f"Order {order.id}: Using frontend price as fallback due to calculation error")
                    else:
                        order.price = Decimal('200.00')
                    order.price_finalized = True
                    order.save(update_fields=['price', 'price_finalized'])
                
                # Create waypoints for pickup and delivery
                from locations.models import Waypoint
                
                # Create pickup waypoint
                if pickup_latitude and pickup_longitude:
                    Waypoint.objects.create(
                        order=order,
                        name=f"Pickup: {pickup_address}",
                        description="Pickup location",
                        latitude=pickup_latitude,
                        longitude=pickup_longitude,
                        address=pickup_address,
                        waypoint_type='pickup',
                        order_index=0
                    )
                
                # Create delivery waypoint
                if delivery_latitude and delivery_longitude:
                    Waypoint.objects.create(
                        order=order,
                        name=f"Delivery: {delivery_address}",
                        description="Delivery location",
                        latitude=delivery_latitude,
                        longitude=delivery_longitude,
                        address=delivery_address,
                        waypoint_type='delivery',
                        order_index=1
                    )
            
            return Response({
                'message': 'Order created successfully',
                'order_id': order.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating order: {str(e)}")
            transaction.rollback()
            return Response({
                'error': f'Failed to create order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CargoDeliveryOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        try:
            # Extract data from request - handle both DRF and regular Django requests
            if hasattr(request, 'data'):
                data = request.data
            else:
                import json
                data = json.loads(request.body.decode('utf-8'))

            
            # Get order type
            order_type_id = data.get('order_type_id')
            if not order_type_id:
                return Response({
                    'status': 'error',
                    'message': 'order_type_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                order_type = OrderType.objects.get(id=order_type_id)
            except OrderType.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Invalid order type'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the client user (can be different if handler is placing order for client)
            client = get_client_user(request)
            
            # Get declared value - now required
            declared_value = data.get('declared_value')
            if not declared_value:
                return Response({
                    'status': 'error',
                    'message': 'Approximate value (declared_value) is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                declared_value_decimal = Decimal(str(declared_value))
                if declared_value_decimal <= 0:
                    return Response({
                        'status': 'error',
                        'message': 'Approximate value must be greater than zero'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, InvalidOperation):
                return Response({
                    'status': 'error',
                    'message': 'Invalid format for approximate value'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the order
            print(f"Creating order with user: {client}, order_type: {order_type}")
            order = Order.objects.create(
                client=client,
                order_type=order_type,
                title=data.get('title', 'Cargo Delivery Order'),
                description=data.get('description', ''),
                pickup_address=data.get('pickup_address', ''),
                delivery_address=data.get('delivery_address', ''),
                pickup_latitude=data.get('pickup_latitude'),
                pickup_longitude=data.get('pickup_longitude'),
                delivery_latitude=data.get('delivery_latitude'),
                delivery_longitude=data.get('delivery_longitude'),
                recipient_name=data.get('recipient_name', ''),
                contact_number=data.get('contact_number', ''),
                status='pending'
            )
            print(f"Order created successfully with ID: {order.id}")
            
            # Create CargoValue if declared_value is provided
            if declared_value:
                try:
                    from .models_updated import CargoValue
                    CargoValue.objects.create(
                        order=order,
                        value=Decimal(str(declared_value)),
                        visible_to_handler_only=True
                    )
                    print(f"CargoValue created for order {order.id}: {declared_value}")
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to create CargoValue: {str(e)}")
                    print(f"Failed to create CargoValue: {str(e)}")
                    # Don't fail the order creation if CargoValue creation fails
            
            # Process items if provided
            items_data = data.get('items', [])
            total_items_price = 0
            
            for item_data in items_data:
                name = item_data.get('name', 'Cargo Item')
                description = item_data.get('description', '')
                quantity = int(item_data.get('quantity', 1))
                # For cargo items, use 0 price since pricing is distance-based
                price = float(item_data.get('price', 0))
                
                ShoppingItem.objects.create(
                    order=order,
                    name=name,
                    description=description,
                    quantity=quantity,
                    price=price
                )
                total_items_price += quantity * price
            
            # Set distance from frontend if provided, otherwise calculate
            frontend_distance = data.get('distance')
            if frontend_distance:
                order.distance = float(frontend_distance)
                order.save()
            elif (order.pickup_latitude and order.pickup_longitude and 
                  order.delivery_latitude and order.delivery_longitude):
                distance = order.calculate_distance()
                order.distance = distance
                order.save()
            
            # Always recalculate price on backend to ensure consistency
            # Frontend price is only used as a reference, but backend calculation is authoritative
            try:
                calculated_price = order.calculate_price()
                if calculated_price and calculated_price > 0:
                    order.price = calculated_price
                else:
                    # Fallback: use a default base price if calculation fails
                    order.price = Decimal('200.00')
                order.price_finalized = True
                order.save(update_fields=['price', 'price_finalized'])
                
                # Log if frontend price differs significantly from backend calculation
                estimated_price = data.get('estimated_price')
                if estimated_price:
                    frontend_price = Decimal(str(estimated_price))
                    price_diff = abs(frontend_price - calculated_price)
                    if price_diff > Decimal('1.00'):  # More than 1 KSh difference
                        logger.warning(
                            f"Order {order.id}: Frontend price ({frontend_price}) differs from "
                            f"backend calculation ({calculated_price}) by {price_diff}. Using backend price."
                        )
            except Exception as e:
                # If calculation fails, use frontend price as fallback, or default
                logger.error(f"Failed to calculate order price: {str(e)}")
                estimated_price = data.get('estimated_price')
                if estimated_price:
                    order.price = Decimal(str(estimated_price))
                    logger.warning(f"Order {order.id}: Using frontend price as fallback due to calculation error")
                else:
                    order.price = Decimal('200.00')
                order.price_finalized = True
                order.save(update_fields=['price', 'price_finalized'])
            
            # Create waypoints for pickup and delivery if coordinates are provided
            try:
                from locations.models import Waypoint
                
                if order.pickup_latitude and order.pickup_longitude:
                    print(f"Creating pickup waypoint for order {order.id}")
                    Waypoint.objects.create(
                        order=order,
                        name=f"Pickup: {order.pickup_address}",
                        description="Pickup location",
                        latitude=order.pickup_latitude,
                        longitude=order.pickup_longitude,
                        address=order.pickup_address,
                        waypoint_type='pickup',
                        order_index=0
                    )
                
                if order.delivery_latitude and order.delivery_longitude:
                    print(f"Creating delivery waypoint for order {order.id}")
                    Waypoint.objects.create(
                        order=order,
                        name=f"Delivery: {order.delivery_address}",
                        description="Delivery location",
                        latitude=order.delivery_latitude,
                        longitude=order.delivery_longitude,
                        address=order.delivery_address,
                        waypoint_type='delivery',
                        order_index=1
                    )
            except Exception as waypoint_error:
                print(f"Error creating waypoints: {waypoint_error}")
                # Continue without waypoints if there's an error
                pass
            
            # Return the created order
            return Response({
                'status': 'success',
                'message': 'Cargo delivery order created successfully',
                'order_id': order.id,
                'price': float(order.price) if order.price else 0
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            return Response({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Bank, BankingOrder
from .serializers import BankSerializer, BankingOrderSerializer


class BankListView(generics.ListAPIView):
    """
    API endpoint that allows banks to be viewed.
    """
    queryset = Bank.objects.filter(is_active=True).order_by('name')
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]

class BankViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows banks to be viewed.
    """
    queryset = Bank.objects.filter(is_active=True).order_by('name')
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]

class BankingOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows banking orders to be viewed or created.
    """
    serializer_class = BankingOrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        This view returns a list of all banking orders
        for the currently authenticated user.
        """
        user = self.request.user
        return BankingOrder.objects.filter(user=user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a pending banking order
        """
        order = self.get_object()
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        else:
            return Response(
                {"detail": "Only pending orders can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )

from rest_framework import generics, status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import HandymanServiceTypes, HandymanOrder, HandymanOrderImage
from .serializers import (
    HandymanServiceTypeSerializer, 
    HandymanServiceTypesSerializer,
    HandymanOrderSerializer, 
    HandymanOrderCreateSerializer,
    HandymanOrderImageSerializer,
    HandymanOrderStatusUpdateSerializer,
    AssignHandymanOrderSerializer
)

class HandymanServiceTypeListView(generics.ListAPIView):
    """
    View to list all active handyman service types
    """
    queryset = HandymanServiceTypes.objects.filter(is_active=True)
    serializer_class = HandymanServiceTypesSerializer
    permission_classes = [permissions.AllowAny]

class HandymanOrderListCreateView(generics.ListCreateAPIView):
    """
    View to list all handyman orders for the authenticated user
    and create new handyman orders
    """
    serializer_class = HandymanOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # If user is staff or has admin role, they can see all orders
        if user.is_staff or user.user_type == 'admin':
            return HandymanOrder.objects.all().order_by('-created_at')
        # Regular users see only their orders
        return HandymanOrder.objects.filter(client=user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HandymanOrderCreateSerializer
        return HandymanOrderSerializer
    
    def create(self, request, *args, **kwargs):
        # Get the client user (can be different if handler is placing order for client)
        client = get_client_user(request)
        
        # Add client_id to request data for serializer context
        mutable_data = request.data.copy()
        mutable_data['client_id'] = client.id
        
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        
        # Create the order immediately; payment will only gate assignment
        order = serializer.save()
        response_serializer = HandymanOrderSerializer(order, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class HandymanOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update or delete a handyman order
    """
    serializer_class = HandymanOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # If user is staff or admin, they can see all orders
        if user.is_staff or user.user_type == 'admin':
            return HandymanOrder.objects.all()
        # Assistants can see orders assigned to them
        elif user.user_type == 'assistant':
            return HandymanOrder.objects.filter(assistant=user)
        # Regular users see only their orders
        return HandymanOrder.objects.filter(client=user)

class HandymanOrderStatusUpdateView(generics.UpdateAPIView):
    """
    View to update the status of a handyman order
    """
    serializer_class = HandymanOrderStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Admin can update any order
        if user.is_staff or user.user_type == 'admin':
            return HandymanOrder.objects.all()
        # Assistants can update orders assigned to them
        return HandymanOrder.objects.filter(assistant=user)

class AssignHandymanOrderView(generics.UpdateAPIView):
    """
    View to assign a handyman order to an assistant
    """
    serializer_class = AssignHandymanOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Only admin or handlers can assign orders
        if user.is_staff or user.user_type in ['admin', 'handler']:
            return HandymanOrder.objects.all()
        return HandymanOrder.objects.none()

class HandymanOrderImageUploadView(generics.CreateAPIView):
    """
    View to upload images for a handyman order
    """
    serializer_class = HandymanOrderImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        try:
            order = HandymanOrder.objects.get(id=order_id)
            # Check if user is authorized to add images
            user = self.request.user
            if user == order.client or user.is_staff or user.user_type in ['admin', 'assistant'] and user == order.assistant:
                serializer.save(order=order)
            else:
                raise PermissionError("You do not have permission to add images to this order")
        except HandymanOrder.DoesNotExist:
            raise NotFound("Order not found")

class PendingHandymanOrdersView(generics.ListAPIView):
    """
    View to list all pending handyman orders (for staff/admin/handlers)
    """
    serializer_class = HandymanOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Only admin, staff, or handlers can see pending orders
        if user.is_staff or user.user_type in ['admin', 'handler']:
            return HandymanOrder.objects.filter(status='pending').order_by('-created_at')
        return HandymanOrder.objects.none()

class AssistantHandymanOrdersView(generics.ListAPIView):
    """
    View to list all handyman orders assigned to the assistant
    """
    serializer_class = HandymanOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'assistant':
            return HandymanOrder.objects.filter(assistant=user).order_by('-created_at')
        return HandymanOrder.objects.none()

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from .models import Order
from .serializers import OrderSerializer

# Custom permission class to check if user is an assistant
class IsAssistantUser(permissions.BasePermission):
    """
    Custom permission to only allow assistants to access the view.
    """
    def has_permission(self, request, view):
        # Return False if user is not authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has the user_type attribute and is an assistant
        return hasattr(request.user, 'user_type') and request.user.user_type == 'assistant'

class AssistantOrdersAPIView(generics.ListAPIView):
    """
    API endpoint that returns all orders assigned to the logged-in assistant.
    Only accessible by users with assistant role.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistantUser]
        
    def get_queryset(self):
        """
        This view returns a list of all orders assigned to the
        currently authenticated assistant.
        """
        # Since we have the IsAssistantUser permission, we can safely
        # assume that the user is an assistant at this point
        return Order.objects.filter(assistant=self.request.user).order_by('-created_at')
    
    def handle_exception(self, exc):
        """
        Handle exceptions in a more user-friendly way
        """
        if isinstance(exc, permissions.exceptions.NotAuthenticated):
            return Response(
                {"detail": "Authentication required to access assistant orders."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, permissions.exceptions.PermissionDenied):
            return Response(
                {"detail": "Only assistants can access these orders."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().handle_exception(exc)


from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models_updated import (
    OrderTracking, ClientFeedback, RiderFeedback, CargoPhoto, CargoValue,
    ReportIssue, Referral
)
from .serializers_updated import (
    OrderTrackingSerializer, ClientFeedbackSerializer, RiderFeedbackSerializer,
    CargoPhotoSerializer, CargoValueSerializer, ReportIssueSerializer, ReferralSerializer
)
from accounts.permissions import IsClient, IsAssistant, IsHandler, IsAdmin

class OrderTrackingView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'user':
            return OrderTracking.objects.filter(order__client=user)
        elif user.user_type == 'assistant':
            return OrderTracking.objects.filter(order__assistant=user)
        elif user.user_type in ['handler', 'admin']:
            return OrderTracking.objects.all()
        return OrderTracking.objects.none()

class ClientFeedbackCreateView(generics.CreateAPIView):
    serializer_class = ClientFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.client != self.request.user:
            raise ValidationError("You can only submit feedback for your own orders.")
        serializer.save()

class ClientFeedbackDetailView(generics.RetrieveAPIView):
    serializer_class = ClientFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def get_queryset(self):
        user = self.request.user
        return ClientFeedback.objects.filter(order__client=user)

class RiderFeedbackCreateView(generics.CreateAPIView):
    serializer_class = RiderFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistant]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.assistant != self.request.user:
            raise ValidationError("You can only submit feedback for your assigned orders.")
        serializer.save()

class RiderFeedbackDetailView(generics.RetrieveAPIView):
    serializer_class = RiderFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistant]

    def get_queryset(self):
        user = self.request.user
        return RiderFeedback.objects.filter(order__assistant=user)

class CargoPhotoUploadView(generics.CreateAPIView):
    serializer_class = CargoPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    
class PriceCalculationView(APIView):
    """
    API endpoint for calculating order prices based on distance and order type.
    This ensures consistent pricing between frontend and backend.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Get data from request
            distance_km = request.data.get('distance_km')
            order_type_id = request.data.get('order_type_id')
            items = request.data.get('items', [])
            
            # Validate required fields
            if not order_type_id:
                return Response({
                    'error': 'order_type_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get order type
            try:
                order_type = OrderType.objects.get(id=order_type_id)
            except OrderType.DoesNotExist:
                return Response({
                    'error': 'Invalid order_type_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate distance
            if distance_km is not None:
                try:
                    distance_km = float(distance_km)
                    if distance_km < 0:
                        distance_km = 0
                except (ValueError, TypeError):
                    distance_km = 0
            else:
                distance_km = 0
            
            # Calculate items price
            from decimal import Decimal
            items_price = Decimal('0.00')
            if items:
                for item in items:
                    try:
                        item_price = Decimal(str(item.get('price', 0)))
                        quantity = int(item.get('quantity', 1))
                        items_price += item_price * quantity
                    except (ValueError, TypeError):
                        continue
            
            # Standard service fee calculation: 200 for first 7km + 20 per extra km
            base_price = Decimal('200.00')
            price_per_km = Decimal('20.00')
            distance_decimal = Decimal(str(distance_km))
            
            if distance_decimal <= 7:
                service_fee = base_price
            else:
                additional_distance = distance_decimal - 7
                service_fee = base_price + (additional_distance * price_per_km)
            
            # Special handling for Banking orders
            if order_type.name.lower() in ['banking', 'banking service']:
                # Banking fee tiers:
                # 0 - 5,000 => 0
                # 5,001 - 10,000 => 50
                # Above 10,000 => 50 per additional 5,000 (or part)
                amount = items_price
                fee = Decimal('0.00')
                if amount > 5000:
                    import math
                    extra_blocks = Decimal(str(math.ceil((amount - 5000) / 5000.0)))
                    fee = extra_blocks * Decimal('50.00')
                
                # Cap the banking fee at the distance-based service fee
                total_price = min(fee, service_fee)
                distance_price = Decimal('0.00')
                base_price_display = Decimal('0.00')
            elif order_type.name.lower() in ['shopping']:
                # Shopping = items price + service fee
                total_price = items_price + service_fee
                distance_price = service_fee
                base_price_display = base_price
            else:
                # Standard distance-based errands (Pickup/Delivery, Cargo)
                total_price = service_fee
                distance_price = service_fee
                base_price_display = base_price
            
            # Calculate breakdown
            free_distance = 7  # First 7km included
            chargeable_distance = max(0, distance_km - free_distance)
            additional_distance_price = Decimal(str(chargeable_distance)) * price_per_km
            
            return Response({
                'success': True,
                'data': {
                    'base_price': float(base_price_display),
                    'distance_price': float(distance_price),
                    'items_price': float(items_price),
                    'total_price': float(total_price),
                    'distance': distance_km,
                    'free_distance': free_distance,
                    'chargeable_distance': float(chargeable_distance),
                    'breakdown': {
                        'base_price': float(base_price_display),
                        'additional_distance': float(chargeable_distance),
                        'additional_distance_price': float(additional_distance_price),
                        'items_price': float(items_price),
                        'discount_amount': 0.0,
                        'discount_percent': 0
                    },
                    'discount_applied': False,
                    'discount_amount': 0.0,
                    'promo': None,
                    'promo_expires': None,
                    'order_type': {
                        'id': order_type.id,
                        'name': order_type.name,
                        'base_price': float(order_type.base_price),
                        'price_per_km': float(order_type.price_per_km),
                        'min_price': float(order_type.min_price)
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error in price calculation: {str(e)}")
            return Response({
                'error': f'Failed to calculate price: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderPriceRealtimeUpdateView(APIView):
    """
    API endpoint for updating order price based on the distance between pickup and delivery locations.
    This endpoint should be called periodically during order execution.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            # Get the order
            order = Order.objects.get(pk=pk)
            
            # Check permissions - only the assigned assistant or admin/handler can update
            user = request.user
            if not ((user.user_type == 'assistant' and order.assistant == user) or 
                    user.user_type in ['handler', 'admin']):
                return Response(
                    {"detail": "You don't have permission to update this order's price."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Only update for orders that are assigned or in progress
            if order.status not in ['assigned', 'in_progress']:
                return Response(
                    {"detail": "Price can only be updated for assigned or in-progress orders."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prevent update if price is finalized
            if order.price_finalized:
                return Response(
                    {"detail": "Price has already been finalized and cannot be updated."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # DISABLED: Update the price based on pickup/delivery distance
            # updated = order.update_price_with_real_time_locations()
            updated = False
            
            # Compute delay penalty: 1% of base price per minute after 30-minute grace beyond ETA
            from django.utils import timezone
            try:
                base_price_value = float(order.order_type.base_price) if order.order_type else 180.0
            except Exception:
                base_price_value = 180.0
            estimated_minutes = order.estimated_duration or 0
            # Prefer started_at, then assigned_at, then created_at as a fallback
            start_time = order.started_at or order.assigned_at or order.created_at
            penalty_minutes = 0
            if start_time and estimated_minutes:
                elapsed_minutes = max(0, (timezone.now() - start_time).total_seconds() / 60)
                grace = 30
                threshold = estimated_minutes + grace
                penalty_minutes = int(max(0, elapsed_minutes - threshold))
            penalty_amount = round((base_price_value * 0.01) * penalty_minutes, 2)
            try:
                current_price_val = float(order.price or 0)
            except Exception:
                current_price_val = 0.0
            total_with_penalty = round(current_price_val + penalty_amount, 2)

            if updated:
                return Response({
                    "detail": "Price updated successfully based on pickup/delivery distance.",
                    "new_price": order.price,
                    "penalty": {
                        "penalty_minutes": penalty_minutes,
                        "penalty_amount": penalty_amount,
                        "base_price_used": base_price_value,
                        "grace_minutes": 30,
                        "estimated_minutes": estimated_minutes,
                    },
                    "total_with_penalty": total_with_penalty
                })
            else:
                return Response({
                    "detail": "Could not update price. Real-time locations may not be available.",
                    "current_price": order.price,
                    "penalty": {
                        "penalty_minutes": penalty_minutes,
                        "penalty_amount": penalty_amount,
                        "base_price_used": base_price_value,
                        "grace_minutes": 30,
                        "estimated_minutes": estimated_minutes,
                    },
                    "total_with_penalty": total_with_penalty
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error updating price: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        user = self.request.user
        if user.user_type == 'user' and order.client == user:
            serializer.save()
        elif user.user_type in ['handler', 'admin']:
            serializer.save()
        else:
            raise ValidationError("You do not have permission to upload cargo photos for this order.")

class CargoValueView(generics.RetrieveUpdateAPIView):
    serializer_class = CargoValueSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]

    def get_queryset(self):
        return CargoValue.objects.all()

class ReportIssueCreateView(generics.CreateAPIView):
    serializer_class = ReportIssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.client != self.request.user:
            raise ValidationError("You can only report issues for your own orders.")
        # Validate 24-hour report window
        if (timezone.now() - order.created_at).total_seconds() > 86400:
            raise ValidationError("Reports must be made within 24 hours of the order being placed.")
        serializer.save()

class ReportIssueListView(generics.ListAPIView):
    serializer_class = ReportIssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]

    def get_queryset(self):
        return ReportIssue.objects.all()

class ReferralCreateView(generics.CreateAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        referrer = self.request.user
        referred_user = serializer.validated_data['referred_user']
        if referrer == referred_user:
            raise ValidationError("You cannot refer yourself.")
        serializer.save(referrer=referrer)

class ReferralListView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)
        
    def get(self, request, *args, **kwargs):
        # Get the referrals for this user
        referrals = self.get_queryset()
        
        # Calculate statistics
        total_referrals = referrals.count()
        completed_referrals = referrals.filter(redeemed=True).count()
        pending_referrals = total_referrals - completed_referrals
        
        # Calculate points (2 points per referral)
        try:
            # Try to sum the points field from the database
            total_points = referrals.aggregate(total_points=models.Sum('points'))['total_points'] or 0
        except:
            # If the points field doesn't exist, calculate it dynamically
            total_points = total_referrals * 2
        
        # Get the user's referral code (username or custom code if implemented)
        referral_code = request.user.username
        
        # Prepare the response data
        response_data = {
            'referral_code': referral_code,
            'total_referrals': total_referrals,
            'pending_referrals': pending_referrals,
            'completed_referrals': completed_referrals,
            'earned_credits': total_points,
            'available_credits': total_points,
            'history': ReferralSerializer(referrals, many=True).data
        }
        
        return Response(response_data)


class HandymanServiceQuoteView(generics.UpdateAPIView):
    """API view for service providers to submit quotes for handyman services"""
    serializer_class = HandymanOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only allow assistants to update their assigned orders
        return HandymanOrder.objects.filter(
            assistant=self.request.user,
            status='in_progress'
        )
    
    def update(self, request, *args, **kwargs):
        """Handle the quote submission"""
        instance = self.get_object()
        
        # Get the quote amount from the request
        service_quote = request.data.get('service_quote')
        quote_notes = request.data.get('quote_notes', '')
        
        if not service_quote:
            return Response(
                {'error': 'Service quote amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert to decimal and validate
            service_quote = Decimal(service_quote)
            if service_quote <= 0:
                raise ValueError("Quote must be greater than zero")
        except (ValueError, InvalidOperation):
            return Response(
                {'error': 'Invalid quote amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the order with the quote
        instance.service_quote = service_quote
        instance.quote_notes = quote_notes
        instance.status = 'quote_provided'
        instance.quote_provided_at = timezone.now()
        instance.save()
        
        # Calculate the total value for record-keeping
        total_value = instance.facilitation_fee + service_quote
        
        # Return the updated order with additional information
        serializer = self.get_serializer(instance)
        response_data = serializer.data
        response_data.update({
            'message': 'Quote submitted successfully. Awaiting admin approval.',
            'payment_info': {
                'facilitation_fee_already_paid': instance.facilitation_fee,
                'service_quote': service_quote,
                'total_value': total_value,
                'client_will_pay': service_quote,
                'note': 'The client will only be charged the service quote amount if approved, as they have already paid the facilitation fee.'
            }
        })
        return Response(response_data)


class HandlerAllOrdersView(generics.ListAPIView):
    """
    Handler-specific view that returns ALL orders without pagination.
    Updated to include full order details (locations, shopping items, images, cargo details)
    so handlers can see everything needed to manage orders.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'order_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'price']
    ordering = ['-created_at']  # Default ordering by newest first
    pagination_class = None  # Disable pagination for this view
    
    def get_serializer_class(self):
        # Use the full serializer so handlers see all details
        from .serializers import OrderSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Only allow handlers and admins to access this view
        if user.user_type not in ['handler', 'admin']:
            return Order.objects.none()
        
        # Return all orders with full related details
        return (
            Order.objects.select_related(
                'client', 'assistant', 'handler', 'order_type',
                'pickup_location', 'delivery_location'
            ).prefetch_related(
                'shopping_items', 'images', 'review', 'cargo_details'
            ).order_by('-created_at')
        )
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # If no orders exist, ensure we return an empty list
        if not queryset.exists():
            return Response([])
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class GenerateQRView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        narration = request.data.get('narration')
        
        from .ncba_service import NCBAService
        ncba_service = NCBAService()
        
        try:
            response = ncba_service.generate_qr(amount=amount, narration=narration)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"QR Generation failed: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
