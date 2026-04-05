from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Index, Q
from locations.models import Location
from decimal import Decimal

User = get_user_model()

class OrderType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    icon = models.ImageField(upload_to='order_types/', null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    
    def __str__(self):
        return self.name
        
    def calculate_price(self, distance_km):
        """
        Calculate price: KSh 200 flat rate for first 7km, then KSh 20 for every extra km
        """
        if distance_km is None:
            return self.base_price
            
        distance_decimal = Decimal(str(distance_km))
        
        if distance_decimal <= 7:
            # For distances up to 7km, just use the base price (200)
            calculated_price = self.base_price
        else:
            # For distances over 7km, add KSh 20 per extra km
            additional_distance = distance_decimal - 7
            calculated_price = self.base_price + (self.price_per_km * additional_distance)
            
        return max(calculated_price, self.min_price)

    def calculate_dynamic_price(self, distance_km):
        """
        Original dynamic pricing logic for internal reference and transparency
        """
        if distance_km is None:
            return self.base_price

        # Convert distance_km to Decimal to avoid type mismatch
        distance_decimal = Decimal(str(distance_km))

        # Apply the standardized pricing model
        if distance_decimal <= 7:
            # For distances up to 7km, just use the base price
            calculated_price = self.base_price
        else:
            # For distances over 7km, add the per-km charge for the additional distance
            additional_distance = distance_decimal - 7
            calculated_price = self.base_price + (self.price_per_km * additional_distance)

        return max(calculated_price, self.min_price)

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('payment_pending', 'Payment Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_orders', db_index=True)
    assistant = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assistant_orders', null=True, blank=True, db_index=True)
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='handled_orders', null=True, blank=True)
    order_type = models.ForeignKey(OrderType, on_delete=models.PROTECT)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    
    # Location details
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name='pickup_orders', null=True, blank=True)
    delivery_location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name='delivery_orders', null=True, blank=True)
    pickup_address = models.CharField(max_length=255, blank=True)
    delivery_address = models.CharField(max_length=255, blank=True)
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)
    
    # Contact details
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    alternative_contact_name = models.CharField(max_length=255, blank=True, null=True)
    alternative_contact_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Scheduling (for Cargo Delivery)
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    
    # Order details
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assistant_items_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Final items total from receipt, set by assistant")
    price_finalized = models.BooleanField(default=False)
    distance = models.FloatField(help_text="Distance in kilometers", null=True, blank=True)
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", null=True, blank=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Estimated value of items (for pickup/delivery orders)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            Index(fields=["client", "status", "-created_at"], name="idx_cli_stat_cra"),
            Index(fields=["assistant", "status", "-created_at"], name="idx_ast_stat_cra"),
            Index(fields=["client", "-created_at"], name="idx_cli_act_cra",
                  condition=Q(status__in=["pending", "assigned", "in_progress", "payment_pending"])),
            Index(fields=["assistant", "-created_at"], name="idx_ast_act_cra",
                  condition=Q(status__in=["pending", "assigned", "in_progress", "payment_pending"])),
            # Trigram GIN index is managed conditionally via migration 0022 so that
            # deployments without pg_trgm can still migrate successfully.
            # When pg_trgm is available, migration 0022 will create `idx_title_trgm`.
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """
        Override save method to add 10 points to the user's wallet and 20 points to the referrer when an order is completed.
        """
        super().save(*args, **kwargs)
        if self.status == 'completed':
            # Only add points if the order is completed
            from accounts.models import Profile  # Avoid circular import
            user_profile, created = Profile.objects.get_or_create(user=self.client)
            user_profile.wallet_points += 10
            user_profile.save()
            print(f"Added 10 points to user {self.client.username} for completed order {self.id}")

            # Also add 20 points to the referrer if exists
            if user_profile.user.referred_by:
                referrer_profile, created = Profile.objects.get_or_create(user=user_profile.user.referred_by)
                referrer_profile.wallet_points += 20
                referrer_profile.save()
                print(f"Added 20 points to referrer {user_profile.user.referred_by.username} for referred order {self.id}")
            else:
                print(f"No referrer found for user {self.client.username} and order {self.id}")
        
    def calculate_price(self):
        """Calculate price based on distance and order type"""
        from decimal import Decimal
        import math
        
        # Calculate service fee based on distance
        service_fee = self.order_type.calculate_price(self.distance)
        
        # 1. Calculate items price (used for Shopping and Banking)
        items_price = Decimal('0.00')
        if self.shopping_items.exists():
            items_price = sum(Decimal(str(item.price)) * item.quantity for item in self.shopping_items.all())
            
        # Also check BankingOrder for amount if it exists
        if hasattr(self, 'banking_orders') and self.banking_orders.exists():
            banking_amount = Decimal(str(self.banking_orders.first().amount))
            if banking_amount > 0 and items_price == 0:
                items_price = banking_amount

        # 2. Special handling for Banking orders - calculate fee based on amount
        if self.order_type.name.lower() in ['banking', 'banking service']:
            # Banking fee tiers:
            # 0 - 5,000 => 0
            # 5,001 - 10,000 => 50
            # Above 10,000 => 50 per additional 5,000 (or part)
            fee = Decimal('0.00')
            if items_price > 5000:
                extra_blocks = Decimal(str(math.ceil((items_price - 5000) / 5000.0)))
                fee = extra_blocks * Decimal('50.00')
            
            # Cap the fee at the calculated service fee for the distance
            if fee > service_fee:
                return service_fee
            return fee
            
        # 3. Special handling for Shopping orders
        if self.order_type.name.lower() in ['shopping']:
            # Total = Items price + calculated service fee
            return items_price + service_fee
            
        # 4. Standard distance-based errands (Pickup/Delivery, Cargo)
        return service_fee
        
    def update_price(self):
        """Update the price based on current distance and items"""
        self.price = self.calculate_price()
        self.save(update_fields=['price'])
        
    def update_price_with_real_time_locations(self):
        """
        Update the price based on the distance between pickup and delivery locations.
        This method now preserves frontend-provided prices and only updates legacy orders.
        """
        if self.status in ['assigned', 'in_progress'] and not self.price_finalized:
            # Only update for orders that are assigned or in progress and price not finalized
            try:
                # Only recalculate for legacy orders that don't have frontend-provided distance
                if not self.distance:
                    # Recalculate distance using pickup and delivery locations for legacy orders
                    new_distance = self.calculate_distance()
                    
                    if new_distance:
                        # Update the price based on the distance for legacy orders only
                        old_price = self.price
                        self.price = self.calculate_price()
                        self.price_finalized = True
                        self.save(update_fields=['price', 'price_finalized'])
                        
                        print(f"Order {self.id} price updated from {old_price} to {self.price} based on pickup/delivery distance (legacy order)")
                        return True
                else:
                    # Preserve frontend-provided price and distance
                    self.price_finalized = True
                    self.save(update_fields=['price_finalized'])
                    print(f"Order {self.id} preserving frontend-provided distance ({self.distance} km) and price ({self.price})")
                    return True
                    
            except Exception as e:
                print(f"Error updating price: {e}")
                
        return False
        
    def calculate_distance(self):
        """Calculate the distance between pickup and delivery locations"""
        # Always use the pickup and delivery locations for distance calculation
        # This ensures pricing is based on the actual service distance, not the assistant's location
        
        # Check if we have the required pickup and delivery coordinates
        if not (self.pickup_latitude and self.pickup_longitude and 
                self.delivery_latitude and self.delivery_longitude):
            return None
            
        import math
        # Haversine formula to calculate distance
        R = 6371  # Earth radius in kilometers
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(self.pickup_latitude)
        lon1_rad = math.radians(self.pickup_longitude)
        lat2_rad = math.radians(self.delivery_latitude)
        lon2_rad = math.radians(self.delivery_longitude)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c  # Distance in kilometers
        
        try:
            self.distance = round(distance, 2)
            
            # Calculate estimated duration (assuming average speed of 30 km/h in urban areas)
            self.estimated_duration = round(distance / 30 * 60)  # Duration in minutes
            
            self.save(update_fields=['distance', 'estimated_duration'])
            
            print(f"Distance calculated between pickup and delivery locations: {distance} km")
        except Exception as e:
            print(f"Warning: Could not save distance to database: {e}")
            # Just continue without saving if the fields don't exist
            pass
            
        return round(distance, 2)

class ShoppingItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shopping_items')
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional fields for Cargo Delivery
    weight = models.FloatField(null=True, blank=True)  # Weight in kg
    size = models.CharField(max_length=20, null=True, blank=True)  # medium, large, xlarge
    
    def __str__(self):
        return f"{self.name} ({self.quantity})"

class OrderImage(models.Model):
    STAGE_CHOICES = (
        ('before', 'Before'),
        ('after', 'After'),
    )
    TYPE_CHOICES = (
        ('generic', 'Generic'),
        ('receipt', 'Receipt'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='order_images/')
    description = models.CharField(max_length=255, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='before')
    image_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='generic')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class OrderAttachment(models.Model):
    """Attachment metadata for files stored in external storage (Cloudinary).

    Note: `file_path` stores the full public/secure URL returned by the
    storage provider (previously this contained a Supabase bucket path).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_attachments')
    file_path = models.CharField(max_length=500)  # full URL to the stored file
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField()  # bytes, enforce <= 5MB in API
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"Attachment {self.file_name} for order {self.order_id}"

class OrderReview(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.order.title}: {self.rating}/5"

class CargoDeliveryDetails(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='cargo_details')
    cargo_weight = models.FloatField()  # Weight in kg
    cargo_size = models.CharField(max_length=20)  # medium, large, xlarge
    need_helpers = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    
    def __str__(self):
        return f"Cargo details for {self.order.title}"


class Bank(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='bank_logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
class Banks(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='bank_logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class BankingOrder(models.Model):
    """Model for Cheque Deposit orders only"""
    TRANSACTION_TYPE_CHOICES = (
        ('cheque_deposit', 'Cheque Deposit'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='banking_orders', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_banking_orders')
    bank = models.ForeignKey(Banks, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_details = models.TextField(help_text="Cheque details: number, payee name, account to deposit into")
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"


class HandymanServiceType(models.Model):
    """Model for different types of handyman services offered"""
    
    SERVICE_CHOICES = (
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical Works'),
        ('landscaping', 'Landscaping'),
    )
    
    name = models.CharField(max_length=100, choices=SERVICE_CHOICES)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For storing icon name/class
    facilitation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    is_active = models.BooleanField(default=True)
    order_type = models.ForeignKey(OrderType, on_delete=models.SET_NULL, null=True, blank=True, related_name='handyman_service_types')
    
    def __str__(self):
        return self.get_name_display()
    
class HandymanServiceTypes(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For storing icon name/class
    price_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class HandymanOrder(models.Model):
    """Model for handyman service orders"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('quote_provided', 'Quote Provided'),
        ('quote_approved', 'Quote Approved'),
        ('quote_rejected', 'Quote Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    TIME_SLOT_CHOICES = (
        ('morning', 'Morning (8AM - 12PM)'),
        ('afternoon', 'Afternoon (12PM - 4PM)'),
        ('evening', 'Evening (4PM - 8PM)'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='handyman_orders', null=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_handyman_orders')
    assistant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_handyman_orders')
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_handyman_orders')
    
    service_type = models.ForeignKey(HandymanServiceType, on_delete=models.CASCADE)
    description = models.TextField()
    address = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    scheduled_date = models.DateField()
    scheduled_time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    alternative_contact = models.CharField(max_length=255, blank=True)
    
    # Payment and pricing fields
    facilitation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    facilitation_fee_paid = models.BooleanField(default=False)
    service_quote = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                       help_text="Quote provided by service provider after assessment")
    quote_notes = models.TextField(blank=True, help_text="Additional notes about the service quote")
    approved_service_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                               help_text="Final approved price for the service")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                    help_text="Total price including facilitation fee and service price")
    final_payment_complete = models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    quote_provided_at = models.DateTimeField(null=True, blank=True)
    quote_approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Handyman Order {self.id} - {self.client.username} - {self.service_type.get_name_display()}"
        
    def calculate_total_price(self):
        """Calculate the total price (facilitation fee + approved service price)
        This is for record-keeping only. The client will only be charged the approved_service_price
        at the end of the service, as they already paid the facilitation fee upfront."""
        if self.approved_service_price:
            self.total_price = self.facilitation_fee + self.approved_service_price
            return self.total_price
        return self.facilitation_fee
        
    def get_final_payment_amount(self):
        """Get the amount to be charged at the end of the service.
        This is only the approved service price, as the facilitation fee was already paid."""
        return self.approved_service_price if self.approved_service_price else Decimal('0.00')

class ServiceQuote(models.Model):
    """Model for managing service provider quotes"""
    QUOTE_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revised', 'Revised'),
    )
    
    handyman_order = models.ForeignKey(HandymanOrder, on_delete=models.CASCADE, related_name='quotes')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_quotes')
    
    # Quote details
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2)
    breakdown = models.JSONField(default=dict, help_text="Detailed breakdown of costs")
    description = models.TextField(help_text="Detailed description of work to be done")
    estimated_duration = models.CharField(max_length=100, help_text="Estimated time to complete")
    materials_included = models.BooleanField(default=True, help_text="Whether materials are included in the quote")
    materials_list = models.TextField(blank=True, help_text="List of materials needed")
    
    # Additional terms
    warranty_period = models.CharField(max_length=100, blank=True, help_text="Warranty offered")
    additional_notes = models.TextField(blank=True)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=QUOTE_STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    # Rejection/revision details
    rejection_reason = models.TextField(blank=True)
    revision_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Quote {self.id} - {self.service_provider.username} - ${self.quoted_price}"
    
    def submit_quote(self):
        """Submit the quote for review"""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
        
        # Update handyman order status
        self.handyman_order.status = 'quote_provided'
        self.handyman_order.service_quote = self.quoted_price
        self.handyman_order.quote_notes = self.description
        self.handyman_order.quote_provided_at = timezone.now()
        self.handyman_order.save()
    
    def approve_quote(self):
        """Approve the quote"""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()
        
        # Update handyman order
        self.handyman_order.status = 'quote_approved'
        self.handyman_order.approved_service_price = self.quoted_price
        self.handyman_order.quote_approved_at = timezone.now()
        self.handyman_order.save()
    
    def reject_quote(self, reason=""):
        """Reject the quote"""
        self.status = 'rejected'
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Update handyman order status
        self.handyman_order.status = 'quote_rejected'
        self.handyman_order.save()

class QuoteImage(models.Model):
    """Images attached to quotes for better explanation"""
    quote = models.ForeignKey(ServiceQuote, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='quote_images/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quote Image for Quote {self.quote.id}"

class HandymanOrderImage(models.Model):
    """Model for storing images associated with handyman orders"""
    order = models.ForeignKey(HandymanOrder, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='handyman_images/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for Order {self.order.id}"
        

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('ncba', 'NCBA Till'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa (Legacy)'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='payments', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Wallet redemption fields
    points_used = models.IntegerField(default=0, help_text="Wallet points redeemed (1 point = KSh1)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount applied from points")
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount to charge after discounts")

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_reference = models.CharField(max_length=255, unique=True)
    
    # M-Pesa Daraja API fields
    mpesa_checkout_request_id = models.CharField(max_length=255, blank=True, null=True, help_text='M-Pesa CheckoutRequestID from STK Push')
    mpesa_merchant_request_id = models.CharField(max_length=255, blank=True, null=True, help_text='M-Pesa MerchantRequestID from STK Push')
    mpesa_receipt_number = models.CharField(max_length=255, blank=True, null=True, help_text='M-Pesa receipt number')
    mpesa_transaction_date = models.CharField(max_length=50, blank=True, null=True, help_text='M-Pesa transaction date')
    mpesa_phone_number = models.CharField(max_length=20, blank=True, null=True, help_text='Phone number used for M-Pesa payment')
    mpesa_transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text='M-Pesa Transaction ID from payment confirmation')

    payment_date = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # For M-Pesa
    email = models.EmailField(blank=True, null=True)  # For card payments (future use)
    
    def __str__(self):
        order_id = self.order.id if hasattr(self, 'order') and self.order else 'N/A'
        return f"Payment {self.transaction_reference} for Order {order_id}"

class OrderPrepayment(models.Model):
    """Temporary record to hold order details until 30% deposit is paid"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='order_prepayments')
    order_type = models.ForeignKey(OrderType, on_delete=models.PROTECT)

    # Basic details
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Addresses and coordinates (primarily delivery for shopping)
    pickup_address = models.CharField(max_length=255, blank=True)
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    delivery_address = models.CharField(max_length=255, blank=True)
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)

    # Shopping items payload
    items = models.JSONField(default=list, blank=True)

    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment
    payment_method = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_reference = models.CharField(max_length=255, unique=True)
    
    # M-Pesa Daraja API fields
    mpesa_checkout_request_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_merchant_request_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=255, blank=True, null=True)
    
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Resulting order once deposit completes
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_from_prepayment')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prepayment {self.transaction_reference} ({self.status})"

class EmergencyAlert(models.Model):
    """SOS alerts raised by assistants, tied only to active orders."""
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('resolved', 'Resolved'),
    )
    assistant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sos_alerts')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sos_alerts')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='resolved_sos_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['status', 'created_at'])]

    def __str__(self):
        return f"SOS {self.id} by {self.assistant_id} for order {self.order_id} ({self.status})"
