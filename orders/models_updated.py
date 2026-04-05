from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from locations.models import Location

User = get_user_model()

class OrderTracking(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='tracking')
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Tracking for Order {self.order.id}"

class ClientFeedback(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='client_feedback')
    delivered_promptly = models.PositiveSmallIntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])
    professionalism = models.PositiveSmallIntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])
    service_quality = models.PositiveSmallIntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Client Feedback for Order {self.order.id}"

class RiderFeedback(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='rider_feedback')
    clear_communication = models.PositiveSmallIntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])
    payment_timeliness = models.PositiveSmallIntegerField(choices=[(1, 'Delayed'), (2, 'On Time')])
    interaction_quality = models.PositiveSmallIntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rider Feedback for Order {self.order.id}"

class CargoPhoto(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='cargo_photos')
    photo = models.ImageField(upload_to='cargo_photos/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cargo Photo for Order {self.order.id}"

class CargoValue(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='cargo_value')
    value = models.DecimalField(max_digits=12, decimal_places=2)
    visible_to_handler_only = models.BooleanField(default=True)

    def __str__(self):
        return f"Cargo Value for Order {self.order.id}"

class ReportIssue(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='issues_reported')
    description = models.TextField()
    incident_timestamp = models.DateTimeField()
    evidence_photos = models.ManyToManyField('OrderImage', blank=True)
    evidence_videos = models.ManyToManyField('OrderVideo', blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Ensure report is within 24 hours of order creation
        if (self.reported_at - self.order.created_at).total_seconds() > 86400:
            from django.core.exceptions import ValidationError
            raise ValidationError("Reports must be made within 24 hours of the order being placed.")

    def __str__(self):
        return f"Issue Report for Order {self.order.id}"

class OrderVideo(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='order_videos/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for Order {self.order.id}"

class Referral(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    points = models.PositiveIntegerField(default=2)  # Default 2 points per referral
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Referral from {self.referrer.username} to {self.referred_user.username}"

class TrackingWaypoint(models.Model):
    """
    Model for storing waypoints along the delivery route
    """
    WAYPOINT_TYPE_CHOICES = (
        ('pickup', 'Pickup Location'),
        ('delivery', 'Delivery Location'),
        ('intermediate', 'Intermediate Stop'),
        ('custom', 'Custom Waypoint'),
    )
    
    tracking = models.ForeignKey(OrderTracking, on_delete=models.CASCADE, related_name='waypoints')
    latitude = models.FloatField()
    longitude = models.FloatField()
    waypoint_type = models.CharField(max_length=20, choices=WAYPOINT_TYPE_CHOICES, default='intermediate')
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    arrival_time = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    order_index = models.PositiveSmallIntegerField(default=0)  # To maintain the order of waypoints
    
    class Meta:
        ordering = ['order_index']
    
    def __str__(self):
        return f"{self.get_waypoint_type_display()} for Order {self.tracking.order.id}"

class TrackingEvent(models.Model):
    """
    Model for storing significant events during the delivery process
    """
    EVENT_TYPE_CHOICES = (
        ('pickup_started', 'Pickup Started'),
        ('pickup_completed', 'Pickup Completed'),
        ('delivery_started', 'Delivery Started'),
        ('delivery_completed', 'Delivery Completed'),
        ('delay', 'Delay Reported'),
        ('detour', 'Detour Taken'),
        ('custom', 'Custom Event'),
    )
    
    tracking = models.ForeignKey(OrderTracking, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_event_type_display()} for Order {self.tracking.order.id}"

class TrackingLocationHistory(models.Model):
    """
    Model for storing the location history of the assistant/rider
    """
    tracking = models.ForeignKey(OrderTracking, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Location at {self.timestamp} for Order {self.tracking.order.id}"
