# Enhanced Payment Model with better IntaSend integration

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),  # Added for refunds
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),  # Added for future expansion
    )
    
    # Core payment fields
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Transaction references
    transaction_id = models.CharField(max_length=255, blank=True, null=True)  # M-Pesa receipt
    transaction_reference = models.CharField(max_length=255, unique=True)  # Our internal ref
    
    # IntaSend specific fields
    intasend_checkout_id = models.CharField(max_length=255, blank=True, null=True)
    intasend_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    intasend_api_ref = models.CharField(max_length=255, blank=True, null=True)  # Added
    intasend_provider = models.CharField(max_length=50, blank=True, null=True)  # Added
    intasend_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added
    intasend_net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added
    
    # Contact information
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # For M-Pesa
    email = models.EmailField(blank=True, null=True)  # For card payments
    
    # Timestamps
    payment_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Added
    completed_at = models.DateTimeField(null=True, blank=True)  # Added
    
    # Failure tracking
    failure_reason = models.TextField(blank=True, null=True)  # Added
    failure_code = models.CharField(max_length=50, blank=True, null=True)  # Added
    retry_count = models.PositiveIntegerField(default=0)  # Added
    
    # Webhook tracking
    webhook_received_at = models.DateTimeField(null=True, blank=True)  # Added
    webhook_challenge = models.CharField(max_length=255, blank=True, null=True)  # Added
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['intasend_invoice_id']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def __str__(self):
        order_id = self.order.id if hasattr(self, 'order') and self.order else 'N/A'
        return f"Payment {self.transaction_reference} for Order {order_id}"
    
    def is_stuck(self, hours=2):
        """Check if payment is stuck in processing status"""
        if self.status != 'processing':
            return False
        
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        return self.payment_date < time_threshold
    
    def format_phone_number(self):
        """Format phone number for IntaSend (ensure 254 prefix)"""
        if not self.phone_number:
            return None
            
        phone = self.phone_number.strip()
        
        # Remove any non-digit characters except +
        import re
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Handle different formats
        if phone.startswith('+254'):
            return phone[1:]  # Remove +
        elif phone.startswith('254'):
            return phone
        elif phone.startswith('0'):
            return '254' + phone[1:]
        elif len(phone) == 9:  # Assume it's missing country code
            return '254' + phone
        else:
            return phone
    
    def update_from_intasend_webhook(self, webhook_data):
        """Update payment from IntaSend webhook data"""
        self.intasend_api_ref = webhook_data.get('api_ref')
        self.intasend_provider = webhook_data.get('provider')
        
        # Update charges and net amount if available
        if webhook_data.get('charges'):
            self.intasend_charges = Decimal(str(webhook_data['charges']))
        if webhook_data.get('net_amount'):
            self.intasend_net_amount = Decimal(str(webhook_data['net_amount']))
        
        # Update transaction ID (M-Pesa receipt or card reference)
        if webhook_data.get('account') and self.payment_method == 'mpesa':
            self.transaction_id = webhook_data['account']
        
        # Update failure information
        if webhook_data.get('failed_reason'):
            self.failure_reason = webhook_data['failed_reason']
        if webhook_data.get('failed_code'):
            self.failure_code = webhook_data['failed_code']
        
        # Update webhook tracking
        self.webhook_received_at = timezone.now()
        self.webhook_challenge = webhook_data.get('challenge')
        
        # Update timestamps
        self.updated_at = timezone.now()
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.save()