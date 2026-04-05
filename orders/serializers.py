from rest_framework import serializers
from django.utils import timezone
from .models import OrderType, Order, ShoppingItem, OrderImage, OrderReview, CargoDeliveryDetails, Payment, ServiceQuote, QuoteImage
from accounts.serializers import UserSerializer
from accounts.models import User
from locations.serializers import LocationSerializer
import uuid

class OrderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderType
        fields = ['id', 'name', 'description', 'icon']

class ShoppingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingItem
        fields = ['id', 'name', 'quantity', 'description', 'price', 'weight', 'size']
        
class OrderImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderImage
        fields = ['id', 'image', 'image_url', 'description', 'stage', 'uploaded_at']
        read_only_fields = ['uploaded_at', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            try:
                return request.build_absolute_uri(obj.image.url) if request else obj.image.url
            except Exception:
                return obj.image.url
        return None

class OrderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReview
        fields = ['id', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']

class CargoDeliveryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoDeliveryDetails
        fields = ['cargo_weight', 'cargo_size', 'need_helpers', 'special_instructions']

class OrderSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    assistant = UserSerializer(read_only=True)
    handler = UserSerializer(read_only=True)
    order_type = OrderTypeSerializer(read_only=True)
    order_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderType.objects.all(), 
        write_only=True,
        source='order_type'
    )
    shopping_items = ShoppingItemSerializer(many=True, read_only=True)
    images = OrderImageSerializer(many=True, read_only=True)
    review = OrderReviewSerializer(read_only=True)
    cargo_details = CargoDeliveryDetailsSerializer(read_only=True)
    price_finalized = serializers.BooleanField(read_only=True)
    
    # Custom fields for better location display
    pickup_location_details = LocationSerializer(source='pickup_location', read_only=True)
    delivery_location_details = LocationSerializer(source='delivery_location', read_only=True)
    pickup_location_display = serializers.SerializerMethodField()
    delivery_location_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'client', 'assistant', 'handler', 'order_type', 'order_type_id',
            'title', 'description', 'pickup_location', 'delivery_location',
            'pickup_location_details', 'delivery_location_details',
            'pickup_location_display', 'delivery_location_display',
            'pickup_address', 'delivery_address', 'pickup_latitude', 'pickup_longitude',
            'delivery_latitude', 'delivery_longitude', 'recipient_name', 'contact_number',
            'alternative_contact_name', 'alternative_contact_number', 'scheduled_date',
            'scheduled_time', 'price', 'status', 'created_at', 'updated_at', 
            'assigned_at', 'started_at', 'completed_at', 'cancelled_at', 
            'shopping_items', 'images', 'review', 'cargo_details', 'price_finalized'
        ]
        read_only_fields = [
            'id', 'client', 'assistant', 'handler', 'status', 'created_at', 
            'updated_at', 'assigned_at', 'started_at', 'completed_at', 'cancelled_at', 'price_finalized', 'price'
        ]
    
    def get_pickup_location_display(self, obj):
        """Return the best available pickup location information"""
        if obj.pickup_location:
            return obj.pickup_location.address or obj.pickup_location.name
        elif obj.pickup_address:
            return obj.pickup_address
        else:
            return "Not specified"
    
    def get_delivery_location_display(self, obj):
        """Return the best available delivery location information"""
        if obj.delivery_location:
            return obj.delivery_location.address or obj.delivery_location.name
        elif obj.delivery_address:
            return obj.delivery_address
        else:
            return "Not specified"


class HandlerOrderListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for lists. Avoids heavy nested serializers.
    """
    client_name = serializers.SerializerMethodField()
    assistant_name = serializers.SerializerMethodField()
    order_type_name = serializers.CharField(source='order_type.name', read_only=True)
    shopping_items = ShoppingItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'title', 'status', 'price', 'created_at',
            'pickup_address', 'delivery_address', 'client_name', 'assistant_name',
            'order_type_name', 'assigned_at', 'started_at', 'completed_at', 'shopping_items'
        ]
    
    def get_client_name(self, obj):
        c = obj.client
        if c:
            first = c.first_name or ''
            last = c.last_name or ''
            full = (first + ' ' + last).strip()
            return full or c.username or (c.email.split('@')[0] if c.email else f"User #{c.id}")
        return 'Unknown Customer'
    
    def get_assistant_name(self, obj):
        a = obj.assistant
        if a:
            first = a.first_name or ''
            last = a.last_name or ''
            full = (first + ' ' + last).strip()
            return full or a.username or (a.email.split('@')[0] if a.email else f"Assistant #{a.id}")
        return 'Not Assigned'

from rest_framework import serializers
from .models import OrderType, Order, ShoppingItem

class PickupDeliveryOrderSerializer(serializers.Serializer):
    order_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderType.objects.all(),
        error_messages={
            'does_not_exist': 'Invalid order type selected',
            'null': 'Order type is required'
        }
    )
    title = serializers.CharField(
        max_length=255,
        error_messages={
            'blank': 'Order title is required',
            'max_length': 'Order title cannot exceed 255 characters'
        }
    )
    additional_description = serializers.CharField(
        required=False, 
        allow_blank=True
    )
    
    # Location fields
    pickup_address = serializers.CharField(
        max_length=255,
        error_messages={
            'blank': 'Pickup address is required',
            'max_length': 'Pickup address cannot exceed 255 characters'
        }
    )
    delivery_address = serializers.CharField(
        max_length=255,
        error_messages={
            'blank': 'Delivery address is required',
            'max_length': 'Delivery address cannot exceed 255 characters'
        }
    )
    pickup_latitude = serializers.FloatField(required=False, allow_null=True)
    pickup_longitude = serializers.FloatField(required=False, allow_null=True)
    delivery_latitude = serializers.FloatField(required=False, allow_null=True)
    delivery_longitude = serializers.FloatField(required=False, allow_null=True)
    
    # Contact fields
    recipient_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    contact_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    
    # Distance field (from frontend calculation)
    distance = serializers.FloatField(required=False, allow_null=True)
    
    # Estimated price (from frontend calculation including surge)
    estimated_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    # Estimated value of items (for pickup/delivery orders)
    approximate_value = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=True, 
        allow_null=False,
        error_messages={
            'required': 'Approximate value of items is required',
            'null': 'Approximate value of items cannot be null',
            'invalid': 'Please enter a valid amount for approximate value'
        }
    )
    
    # Items to be delivered
    items = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        error_messages={
            'required': 'At least one item is required'
        }
    )
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required")
        
        for item in items:
            if not item.get('name'):
                raise serializers.ValidationError("Item name is required")
            
            try:
                quantity = int(item.get('quantity', 1))
                if quantity < 1:
                    raise serializers.ValidationError("Quantity must be at least 1")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Quantity must be a valid number")
        
        return items
    
    def validate(self, data):
        """
        Perform additional cross-field validation
        """
        # If we have latitude/longitude, make sure they are valid
        if data.get('pickup_latitude') is not None and data.get('pickup_longitude') is not None:
            if not (-90 <= data['pickup_latitude'] <= 90):
                raise serializers.ValidationError({"pickup_latitude": "Latitude must be between -90 and 90"})
            if not (-180 <= data['pickup_longitude'] <= 180):
                raise serializers.ValidationError({"pickup_longitude": "Longitude must be between -180 and 180"})
        
        if data.get('delivery_latitude') is not None and data.get('delivery_longitude') is not None:
            if not (-90 <= data['delivery_latitude'] <= 90):
                raise serializers.ValidationError({"delivery_latitude": "Latitude must be between -90 and 90"})
            if not (-180 <= data['delivery_longitude'] <= 180):
                raise serializers.ValidationError({"delivery_longitude": "Longitude must be between -180 and 180"})
        
        return data

class CargoDeliveryOrderSerializer(serializers.Serializer):
    order_type_id = serializers.PrimaryKeyRelatedField(queryset=OrderType.objects.all())
    cargoName = serializers.CharField(max_length=255)
    cargoDescription = serializers.CharField()
    cargoWeight = serializers.FloatField()
    cargoSize = serializers.CharField(max_length=20)
    needHelpers = serializers.BooleanField(default=False)
    scheduledDate = serializers.DateField()
    scheduledTime = serializers.TimeField()
    instructions = serializers.CharField(required=False, allow_blank=True)
    pickup_address = serializers.CharField(max_length=255)
    delivery_address = serializers.CharField(max_length=255)
    pickup_latitude = serializers.FloatField(required=False, allow_null=True)
    pickup_longitude = serializers.FloatField(required=False, allow_null=True)
    delivery_latitude = serializers.FloatField(required=False, allow_null=True)
    delivery_longitude = serializers.FloatField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    contact = serializers.CharField(required=False, allow_blank=True)
    photo = serializers.ImageField(required=True, help_text="Photo of the cargo to be delivered")

from rest_framework import serializers
from django.utils import timezone
from .models import Order

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the status of an order.
    """
    class Meta:
        model = Order
        fields = ['status']
    
    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        current_status = instance.status
        request_user = self.context['request'].user
        
        # Intercept Assistant marking as completed for specific order types
        # If work is done, it should go to payment_pending first
        if request_user.user_type == 'assistant' and new_status == 'completed':
            order_type_name = (instance.order_type.name or '').lower().strip() if instance.order_type else ''
            # All errands should go to payment_pending first so client can pay the final amount
            if any(name in order_type_name for name in ['pickup', 'delivery', 'cargo', 'banking', 'shopping']):
                new_status = 'payment_pending'
        
        # Update timestamp fields based on status change
        if new_status == 'assigned' and current_status != 'assigned':
            instance.assigned_at = timezone.now()
        elif new_status == 'in_progress' and current_status != 'in_progress':
            instance.started_at = timezone.now()
        elif new_status == 'payment_pending' and current_status != 'payment_pending':
            # When work is completed but payment is pending, don't set completed_at yet
            pass
        elif new_status == 'completed' and current_status != 'completed':
            instance.completed_at = timezone.now()
        elif new_status == 'cancelled' and current_status != 'cancelled':
            instance.cancelled_at = timezone.now()
        
        instance.status = new_status
        instance.save()
        return instance

class AssignOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning an assistant to an order.
    """
    assistant_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='assistant'),
        write_only=True,
        source='assistant'
    )
    
    class Meta:
        model = Order
        fields = ['assistant_id', 'status']
        
    def validate(self, data):
        # Ensure the order can only be assigned if it's pending
        if self.instance.status != 'pending':
            raise serializers.ValidationError("Only pending orders can be assigned")
        
        # Block assignment until required deposits are paid for Shopping and Handyman
        from django.db.models import Sum
        from decimal import Decimal
        order_type_name = (self.instance.order_type.name or '').lower().strip() if self.instance.order_type else ''
        if order_type_name in ['shopping', 'shopping order']:
            price = self.instance.price or Decimal('0')
            required = (price * Decimal('0.30')).quantize(Decimal('0.01'))
            paid = self.instance.payments.filter(status='completed').aggregate(total=Sum('final_amount'))['total'] or Decimal('0')
            if paid < required:
                raise serializers.ValidationError("Cannot assign: 30% deposit not paid for shopping order")
        if hasattr(self.instance, 'handyman_orders') and self.instance.handyman_orders.exists():
            if self.instance.handyman_orders.filter(facilitation_fee_paid=False).exists():
                raise serializers.ValidationError("Cannot assign: handyman facilitation fee not paid")
        
        # Always update status to 'assigned' when assigning an assistant
        data['status'] = 'assigned'
        return data
    
    def update(self, instance, validated_data):
        # Update the assistant
        instance.assistant = validated_data.get('assistant')
        instance.status = 'assigned'
        instance.assigned_at = timezone.now()
        instance.handler = self.context['request'].user  # Set current handler
        instance.save()
        
        # Preserve the frontend-provided price and distance
        # Only recalculate if the order doesn't have a distance (legacy orders)
        try:
            if not instance.distance:
                # Calculate distance between pickup and delivery locations for legacy orders
                new_distance = instance.calculate_distance()
                
                if new_distance:
                    # Update the price based on the distance for legacy orders only
                    instance.update_price()
                    print(f"Order {instance.id} price updated for legacy order: {instance.price}")
            else:
                print(f"Order {instance.id} preserving frontend-provided distance ({instance.distance} km) and price ({instance.price})")
        except Exception as e:
            print(f"Error in price handling: {e}")
        
        return instance

from rest_framework import serializers
from .models import Banks, BankingOrder

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banks
        fields = ['id', 'name', 'logo', 'description', 'is_active']

class BankingOrderSerializer(serializers.ModelSerializer):
    bank_name = serializers.ReadOnlyField(source='bank.name')
    
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderType.objects.all(),
        required=False,
        write_only=True
    )
    
    title = serializers.CharField(required=False, default="Banking Transaction")
    
    class Meta:
        model = BankingOrder
        fields = [
            'id', 'order_id', 'user', 'bank', 'bank_name', 'transaction_type', 
            'amount', 'transaction_details', 'scheduled_date', 'status', 
            'created_at', 'updated_at', 'completed_at', 'order_type_id', 'title'
        ]
        read_only_fields = ['user', 'status', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        # Automatically set the user from the request
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Extract title if provided
        title = validated_data.pop('title', f"Banking {validated_data.get('transaction_type', 'Transaction')}")
        
        # Get order_type_id if provided, otherwise get or create a banking order type
        order_type = None
        if 'order_type_id' in validated_data:
            order_type = validated_data.pop('order_type_id')
        else:
            order_type, created = OrderType.objects.get_or_create(
                name="Banking Service",
                defaults={
                    "description": "Banking and financial transaction services",
                    "base_price": 200.00,
                    "price_per_km": 20.00,
                    "min_price": 200.00
                }
            )
        
        # First create the main Order
        main_order = Order.objects.create(
            client=user,
            order_type=order_type,
            title=title,
            description=validated_data.get('transaction_details', ''),
            status='pending',
            price=validated_data.get('amount', 0)
        )
        
        # Then create the BankingOrder linked to the main Order
        validated_data['order'] = main_order
        return super().create(validated_data)

from rest_framework import serializers
from django.utils import timezone
from .models import HandymanServiceType, HandymanServiceTypes, HandymanOrder, HandymanOrderImage
from accounts.serializers import UserSerializer

class HandymanServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandymanServiceType
        fields = ['id', 'name', 'description', 'icon', 'facilitation_fee', 'is_active']

class HandymanServiceTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandymanServiceTypes
        fields = ['id', 'name', 'description', 'icon', 'price_estimate', 'is_active']

class HandymanOrderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandymanOrderImage
        fields = ['id', 'image', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class HandymanOrderSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    assistant = UserSerializer(read_only=True)
    service_type_name = serializers.SerializerMethodField()
    images = HandymanOrderImageSerializer(many=True, read_only=True)
    
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    
    class Meta:
        model = HandymanOrder
        fields = [
            'id', 'order_id', 'client', 'assistant', 'service_type', 'service_type_name',
            'description', 'address', 'latitude', 'longitude',
            'scheduled_date', 'scheduled_time_slot', 'alternative_contact',
            'facilitation_fee', 'facilitation_fee_paid', 'service_quote', 'quote_notes',
            'approved_service_price', 'total_price', 'final_payment_complete',
            'status', 'images', 'created_at', 'updated_at', 'assigned_at', 
            'started_at', 'quote_provided_at', 'quote_approved_at', 'completed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'client', 'assistant', 'facilitation_fee', 'total_price',
            'created_at', 'updated_at', 'assigned_at', 'started_at', 
            'quote_provided_at', 'quote_approved_at', 'completed_at', 'cancelled_at'
        ]
        
    def get_service_type_name(self, obj):
        """Return the display name for the service type"""
        if hasattr(obj.service_type, 'get_name_display'):
            return obj.service_type.get_name_display()
        return obj.service_type.name

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['client'] = request.user
        return super().create(validated_data)

class HandymanOrderCreateSerializer(serializers.Serializer):
    service_type_id = serializers.PrimaryKeyRelatedField(
        queryset=HandymanServiceType.objects.all(),
        source='service_type'
    )
    description = serializers.CharField()
    address = serializers.CharField(max_length=255)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    scheduled_date = serializers.DateField()
    scheduled_time_slot = serializers.ChoiceField(choices=HandymanOrder.TIME_SLOT_CHOICES)
    alternative_contact = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    # Read-only fields for display
    facilitation_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    title = serializers.CharField(required=False, default="Handyman Service Request")
    order_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderType.objects.all(),
        required=False
    )
    
    def create(self, validated_data):
        request = self.context.get('request')
        requester = request.user if request and hasattr(request, 'user') else None
        
        if not requester:
            raise serializers.ValidationError("User authentication required")
        
        # Get client_id from request data if provided (for handlers placing orders for clients)
        client_id = request.data.get('client_id') if request else None
        if client_id and requester.user_type in ['handler', 'admin']:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=client_id)
                # Verify handler has permission
                if requester.user_type == 'handler':
                    if user.account_manager != requester:
                        raise serializers.ValidationError("You can only place orders for clients assigned to you")
            except User.DoesNotExist:
                raise serializers.ValidationError(f"Client with id {client_id} not found")
        else:
            user = requester
        
        try:
            # Extract title if provided
            title = validated_data.pop('title', 'Handyman Service Request')
            service_type = validated_data.get('service_type')
            
            if not service_type:
                raise serializers.ValidationError("Service type is required")
            
            # Check if order_type_id was explicitly provided
            order_type = None
            if 'order_type_id' in validated_data:
                order_type = validated_data.pop('order_type_id')
            # Otherwise, try to get it from the service_type
            elif service_type and hasattr(service_type, 'order_type') and service_type.order_type:
                order_type = service_type.order_type
            # If still no order_type, get or create a default one
            else:
                order_type, created = OrderType.objects.get_or_create(
                    name="Handyman Service",
                    defaults={
                        "description": "General handyman and repair services",
                        "base_price": 200.00,
                        "price_per_km": 20.00,
                        "min_price": 200.00
                    }
                )
                
                # Update the service_type with this order_type if it doesn't have one
                if service_type and not service_type.order_type:
                    service_type.order_type = order_type
                    service_type.save()
            
            # Create the main Order first
            main_order = Order.objects.create(
                client=user,
                order_type=order_type,
                title=title,
                description=validated_data.get('description', ''),
                delivery_address=validated_data.get('address', ''),
                delivery_latitude=validated_data.get('latitude'),
                delivery_longitude=validated_data.get('longitude'),
                status='pending'
            )
            
            # Get the facilitation fee from the service type
            facilitation_fee = service_type.facilitation_fee if hasattr(service_type, 'facilitation_fee') and service_type.facilitation_fee else Decimal('500.00')
            
            # Set the main order price to the facilitation fee initially
            main_order.price = facilitation_fee
            main_order.save()
            
            # Then create the HandymanOrder linked to the main Order
            # Handle required fields with defaults if not provided
            scheduled_date = validated_data.get('scheduled_date')
            if not scheduled_date:
                from datetime import date, timedelta
                scheduled_date = date.today() + timedelta(days=1)  # Default to tomorrow
            
            scheduled_time_slot = validated_data.get('scheduled_time_slot', 'morning')
            
            handyman_order = HandymanOrder.objects.create(
                order=main_order,
                client=user,
                facilitation_fee=facilitation_fee,
                service_type=service_type,
                description=validated_data.get('description', ''),
                address=validated_data.get('address', ''),
                latitude=validated_data.get('latitude'),
                longitude=validated_data.get('longitude'),
                scheduled_date=scheduled_date,
                scheduled_time_slot=scheduled_time_slot,
                alternative_contact=validated_data.get('alternative_contact', '')
            )
            
            return handyman_order
            
        except Exception as e:
            import traceback
            raise serializers.ValidationError(f"Error creating handyman order: {str(e)} - {traceback.format_exc()}")

class HandymanOrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandymanOrder
        fields = ['status']
    
    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        current_status = instance.status
        
        # Update timestamp fields based on status change
        if new_status == 'assigned' and current_status != 'assigned':
            instance.assigned_at = timezone.now()
        elif new_status == 'in_progress' and current_status != 'in_progress':
            instance.started_at = timezone.now()
        elif new_status == 'completed' and current_status != 'completed':
            instance.completed_at = timezone.now()
        elif new_status == 'cancelled' and current_status != 'cancelled':
            instance.cancelled_at = timezone.now()
        
        instance.status = new_status
        instance.save()
        return instance

class AssignHandymanOrderSerializer(serializers.ModelSerializer):
    assistant_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='assistant'),
        write_only=True,
        source='assistant'
    )
    
    class Meta:
        model = HandymanOrder
        fields = ['assistant_id', 'status']
        
    def validate(self, data):
        # Ensure the order can only be assigned if it's pending
        if self.instance.status != 'pending':
            raise serializers.ValidationError("Only pending orders can be assigned")
        
        # Always update status to 'assigned' when assigning an assistant
        data['status'] = 'assigned'
        return data
    
    def update(self, instance, validated_data):
        # Update the assistant
        instance.assistant = validated_data.get('assistant')
        instance.status = 'assigned'
        instance.assigned_at = timezone.now()
        instance.handler = self.context['request'].user  # Set current handler
        instance.save()
        
        # If there's a main order associated, recalculate its price based on pickup/delivery distance
        if hasattr(instance, 'order') and instance.order:
            try:
                # Set the assistant on the main order too
                main_order = instance.order
                main_order.assistant = instance.assistant
                main_order.save()
                
                # Calculate distance between pickup and delivery locations
                new_distance = main_order.calculate_distance()
                
                if new_distance:
                    # Update the price based on the distance
                    main_order.update_price()
                    
                    # Update the handyman order price too
                    instance.price = main_order.price
                    instance.save(update_fields=['price'])
                    
                    print(f"Handyman Order {instance.id} price updated based on pickup/delivery distance: {instance.price}")
            except Exception as e:
                print(f"Error updating handyman order price: {e}")
        
        return instance

from rest_framework import serializers
from .models_updated import (
    OrderTracking, ClientFeedback, RiderFeedback, CargoPhoto, CargoValue,
    ReportIssue, Referral, OrderVideo
)

class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ['order', 'current_latitude', 'current_longitude', 'last_updated']

class ClientFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientFeedback
        fields = ['order', 'delivered_promptly', 'professionalism', 'service_quality', 'comments', 'created_at']
        read_only_fields = ['created_at']

class RiderFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiderFeedback
        fields = ['order', 'clear_communication', 'payment_timeliness', 'interaction_quality', 'comments', 'created_at']
        read_only_fields = ['created_at']

class CargoPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoPhoto
        fields = ['id', 'order', 'photo', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class CargoValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoValue
        fields = ['order', 'value', 'visible_to_handler_only']

class OrderVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVideo
        fields = ['id', 'order', 'video', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class ReportIssueSerializer(serializers.ModelSerializer):
    evidence_photos = CargoPhotoSerializer(many=True, read_only=True)
    evidence_videos = OrderVideoSerializer(many=True, read_only=True)

    class Meta:
        model = ReportIssue
        fields = ['id', 'order', 'description', 'incident_timestamp', 'evidence_photos', 'evidence_videos', 'reported_at']
        read_only_fields = ['reported_at']

class ReferralSerializer(serializers.ModelSerializer):
    referrer_username = serializers.CharField(source='referrer.username', read_only=True)
    referred_username = serializers.CharField(source='referred_user.username', read_only=True)
    
    class Meta:
        model = Referral
        fields = ['id', 'referrer', 'referrer_username', 'referred_user', 'referred_username', 
                 'discount_amount', 'points', 'created_at', 'redeemed', 'redeemed_at']
        read_only_fields = ['created_at', 'redeemed_at', 'points']

# Quote Management Serializers
class QuoteImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteImage
        fields = ['id', 'image', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class ServiceQuoteSerializer(serializers.ModelSerializer):
    images = QuoteImageSerializer(many=True, read_only=True)
    service_provider_name = serializers.CharField(source='service_provider.get_full_name', read_only=True)
    service_provider_username = serializers.CharField(source='service_provider.username', read_only=True)
    handyman_order_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceQuote
        fields = [
            'id', 'handyman_order', 'service_provider', 'service_provider_name', 
            'service_provider_username', 'quoted_price', 'breakdown', 'description',
            'estimated_duration', 'materials_included', 'materials_list', 
            'warranty_period', 'additional_notes', 'status', 'submitted_at',
            'reviewed_at', 'approved_at', 'rejected_at', 'rejection_reason',
            'revision_notes', 'created_at', 'updated_at', 'images',
            'handyman_order_details'
        ]
        read_only_fields = [
            'service_provider', 'submitted_at', 'reviewed_at', 'approved_at', 
            'rejected_at', 'created_at', 'updated_at', 'service_provider_name',
            'service_provider_username', 'handyman_order_details'
        ]
    
    def get_handyman_order_details(self, obj):
        """Get basic details about the handyman order"""
        order = obj.handyman_order
        return {
            'id': order.id,
            'service_type': order.service_type.get_name_display(),
            'description': order.description,
            'address': order.address,
            'scheduled_date': order.scheduled_date,
            'scheduled_time_slot': order.get_scheduled_time_slot_display(),
            'client_name': order.client.get_full_name(),
            'status': order.get_status_display()
        }
    
    def create(self, validated_data):
        # Set the service provider to the current user
        validated_data['service_provider'] = self.context['request'].user
        return super().create(validated_data)

class ServiceQuoteCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating quotes"""
    
    class Meta:
        model = ServiceQuote
        fields = [
            'id', 'handyman_order', 'quoted_price', 'breakdown', 'description',
            'estimated_duration', 'materials_included', 'materials_list',
            'warranty_period', 'additional_notes'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['service_provider'] = self.context['request'].user
        return super().create(validated_data)

class ServiceQuoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating quote status (approve/reject)"""
    
    class Meta:
        model = ServiceQuote
        fields = ['status', 'rejection_reason', 'revision_notes']
    
    def update(self, instance, validated_data):
        status = validated_data.get('status')
        
        if status == 'approved':
            instance.approve_quote()
        elif status == 'rejected':
            reason = validated_data.get('rejection_reason', '')
            instance.reject_quote(reason)
        elif status == 'submitted':
            instance.submit_quote()
        
        return instance

class HandymanOrderWithQuotesSerializer(serializers.ModelSerializer):
    """Enhanced handyman order serializer that includes quotes"""
    quotes = ServiceQuoteSerializer(many=True, read_only=True)
    latest_quote = serializers.SerializerMethodField()
    can_submit_quote = serializers.SerializerMethodField()
    
    class Meta:
        model = HandymanOrder
        fields = [
            'id', 'client', 'assistant', 'handler', 'service_type', 'description',
            'address', 'scheduled_date', 'scheduled_time_slot', 'status',
            'facilitation_fee', 'service_quote', 'approved_service_price',
            'created_at', 'assigned_at', 'quote_provided_at', 'quote_approved_at',
            'quotes', 'latest_quote', 'can_submit_quote'
        ]
        read_only_fields = [
            'client', 'handler', 'facilitation_fee', 'service_quote',
            'approved_service_price', 'created_at', 'assigned_at',
            'quote_provided_at', 'quote_approved_at', 'quotes',
            'latest_quote', 'can_submit_quote'
        ]
    
    def get_latest_quote(self, obj):
        """Get the latest quote for this order"""
        latest_quote = obj.quotes.first()
        if latest_quote:
            return ServiceQuoteSerializer(latest_quote).data
        return None
    
    def get_can_submit_quote(self, obj):
        """Check if the current user can submit a quote"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Only assigned service provider can submit quotes
        if obj.assistant != request.user:
            return False
        
        # Can only submit if status allows it
        allowed_statuses = ['assigned', 'quote_rejected']
        return obj.status in allowed_statuses

# orders/serializers.py
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'amount', 'final_amount', 'payment_method', 'status',
            'transaction_id', 'transaction_reference',
            'mpesa_checkout_request_id', 'mpesa_merchant_request_id',
            'mpesa_receipt_number', 'mpesa_transaction_date',
            'mpesa_phone_number', 'mpesa_transaction_id',
            'payment_date', 'phone_number', 'email'
        ]
        read_only_fields = [
            'transaction_id', 'mpesa_checkout_request_id', 'mpesa_merchant_request_id',
            'mpesa_receipt_number', 'mpesa_transaction_date',
            'mpesa_phone_number', 'mpesa_transaction_id', 'payment_date', 'status'
        ]

class InitiatePaymentSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD_CHOICES)
    phone_number = serializers.CharField(max_length=20, required=False)
    email = serializers.EmailField(required=False)
    redeem_points = serializers.IntegerField(required=False, min_value=0, help_text="Points to redeem (1 point = KSh1)")
    
    class Meta:
        model = Payment
        fields = ['order', 'payment_method', 'phone_number', 'email', 'redeem_points']
    
    def validate(self, data):
        # Validate that either phone_number or email is provided based on payment method
        if data['payment_method'] in ['ncba', 'mpesa'] and not data.get('phone_number'):
            raise serializers.ValidationError({"phone_number": "Phone number is required for NCBA payments"})
        elif data['payment_method'] == 'card' and not data.get('email'):
            raise serializers.ValidationError({"email": "Email is required for card payments"})
        
        # Check if order exists and has a valid status for payment
        order = data['order']
        valid_statuses = ['payment_pending', 'completed', 'in_progress', 'assigned', 'In Progress', 'pending']
        
        # Print debug information
        print(f"Order ID: {order.id}, Status: {order.status}, Valid statuses: {valid_statuses}")
        
        if order.status not in valid_statuses:
            raise serializers.ValidationError({"order": f"Payment can only be initiated for orders with valid status. Current status: {order.status}"})
            
        # Don't automatically mark order as completed when initiating payment
        # Order should only be marked as completed when payment is actually confirmed
        
        # Check if payment already exists and is completed
        existing_payment = Payment.objects.filter(order=order, status='completed').first()
        if existing_payment:
            raise serializers.ValidationError({"order": "Payment for this order has already been completed"})
        
        return data
    
    def create(self, validated_data):
        # Generate a unique transaction reference
        transaction_reference = f"FAGI-{uuid.uuid4().hex[:8].upper()}"
        
        # Get the order and calculate the amount
        order = validated_data['order']
        total_amount = order.price or order.calculate_price()
        # For shopping orders, require a 30% upfront payment
        try:
            from decimal import Decimal, ROUND_HALF_UP
            if order.order_type and order.order_type.name and order.order_type.name.lower() == 'shopping':
                amount = (Decimal(str(total_amount)) * Decimal('0.30')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                amount = total_amount
        except Exception:
            amount = total_amount
        
        # Apply wallet points redemption if requested
        redeem_points = self.initial_data.get('redeem_points')
        try:
            redeem_points = int(redeem_points) if redeem_points is not None else 0
        except ValueError:
            redeem_points = 0

        discount_amount = 0
        final_amount = amount

        if redeem_points and order.client and hasattr(order.client, 'profile'):
            available = order.client.profile.wallet_points
            use_points = max(0, min(redeem_points, available, int(amount)))  # cannot exceed amount or available
            if use_points > 0:
                # Deduct points and record transaction
                from accounts.models import WalletTransaction
                order.client.profile.wallet_points = available - use_points
                order.client.profile.save(update_fields=['wallet_points'])
                WalletTransaction.objects.create(
                    user=order.client,
                    points=-use_points,
                    amount_equivalent=use_points,
                    transaction_type='redeem',
                    reference=f'payment_redeem_order_{order.id}'
                )
                discount_amount = use_points
                final_amount = amount - discount_amount

        # Create the payment record
        payment = Payment.objects.create(
            order=order,
            amount=amount,
            points_used=int(discount_amount),
            discount_amount=discount_amount,
            final_amount=final_amount,
            payment_method=validated_data['payment_method'],
            transaction_reference=transaction_reference,
            phone_number=validated_data.get('phone_number'),
            email=validated_data.get('email'),
            status='pending'
        )
        
        return payment
