from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()

class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'is_default': self.is_default
        }

class UserLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='current_location')
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
    heading = models.FloatField(null=True, blank=True)  # Direction in degrees
    speed = models.FloatField(null=True, blank=True)    # Speed in km/h
    accuracy = models.FloatField(null=True, blank=True) # Accuracy in meters
    
    def __str__(self):
        return f"{self.user.username}'s Current Location"
    
    def to_dict(self):
        return {
            'user_id': self.user.id,
            'username': self.user.username,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'heading': self.heading,
            'speed': self.speed,
            'accuracy': self.accuracy,
            'last_updated': self.last_updated.isoformat()
        }

class Waypoint(models.Model):
    WAYPOINT_TYPES = (
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('stop', 'Stop'),
        ('checkpoint', 'Checkpoint'),
    )
    
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='waypoints', null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255)
    waypoint_type = models.CharField(max_length=20, choices=WAYPOINT_TYPES)
    order_index = models.IntegerField(default=0)  # For ordering waypoints
    is_visited = models.BooleanField(default=False)
    visited_at = models.DateTimeField(null=True, blank=True)
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order_index']
    
    def __str__(self):
        return f"{self.order.id} - {self.name} ({self.get_waypoint_type_display()})"
    
    def mark_as_visited(self):
        self.is_visited = True
        self.visited_at = timezone.now()
        self.save()
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order.id,
            'name': self.name,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'waypoint_type': self.waypoint_type,
            'order_index': self.order_index,
            'is_visited': self.is_visited,
            'visited_at': self.visited_at.isoformat() if self.visited_at else None,
            'estimated_arrival_time': self.estimated_arrival_time.isoformat() if self.estimated_arrival_time else None
        }

class RouteCalculation(models.Model):
    """Stores calculated routes between waypoints"""
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='routes', null=True)
    start_waypoint = models.ForeignKey(Waypoint, on_delete=models.CASCADE, related_name='routes_as_start')
    end_waypoint = models.ForeignKey(Waypoint, on_delete=models.CASCADE, related_name='routes_as_end')
    distance = models.FloatField(help_text="Distance in kilometers")
    duration = models.IntegerField(help_text="Estimated duration in seconds")
    route_data = models.JSONField(null=True, blank=True, help_text="Encoded route data")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Route from {self.start_waypoint.name} to {self.end_waypoint.name}"