from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order_created', 'Order Created'),
        ('order_assigned', 'Order Assigned'),
        ('order_started', 'Order Started'),
        ('order_completed', 'Order Completed'),
        ('order_cancelled', 'Order Cancelled'),
        ('verification_approved', 'Verification Approved'),
        ('verification_rejected', 'Verification Rejected'),
        ('message', 'Message'),
        ('app_update', 'App Update'),
        ('promotion', 'Promotion'),
        ('announcement', 'Announcement'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    read = models.BooleanField(default=False)
    
    # For generic relations to any model (order, verification, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient.username}"

class PushToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20)  # 'ios', 'android', 'web'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'token')
    
    def __str__(self):
        return f"{self.user.username}'s {self.device_type} token"

class UserPushSubscription(models.Model):
    """
    Model to store Web Push subscriptions for VAPID notifications
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    subscription_data = models.JSONField()  # Stores the full subscription object
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user']
        
    def __str__(self):
        return f"Push subscription for {self.user.username}"

class BroadcastNotification(models.Model):
    """
    Model for broadcast notifications (app updates, promotions, announcements)
    """
    BROADCAST_TYPES = (
        ('app_update', 'App Update'),
        ('promotion', 'Promotion'),
        ('announcement', 'Announcement'),
    )
    
    TARGET_AUDIENCES = (
        ('all', 'All Users'),
        ('clients', 'Clients Only'),
        ('assistants', 'Assistants Only'),
        ('handlers', 'Handlers Only'),
        ('admins', 'Admins Only'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=BROADCAST_TYPES, default='announcement')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCES, default='all')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Optional fields
    action_url = models.URLField(blank=True, null=True, help_text="URL to open when notification is tapped")
    image_url = models.URLField(blank=True, null=True, help_text="Image to display in notification")
    
    # Scheduling
    scheduled_for = models.DateTimeField(blank=True, null=True, help_text="When to send the notification")
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_broadcasts')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    total_recipients = models.IntegerField(default=0)
    successful_sends = models.IntegerField(default=0)
    failed_sends = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type}: {self.title} ({self.status})"