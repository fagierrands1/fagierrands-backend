from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from .models import Order
from .models_updated import (
    OrderTracking, TrackingWaypoint, TrackingEvent, TrackingLocationHistory
)
from locations.models import UserLocation

logger = logging.getLogger(__name__)


def initialize_order_tracking(order):
    """
    Automatically initialize tracking for an order when it's assigned or goes in_progress.
    Creates OrderTracking object, waypoints, and initial location history if assistant has location.
    """
    try:
        # Get or create tracking object
        tracking, created = OrderTracking.objects.get_or_create(order=order)
        
        # Only initialize if tracking was just created or doesn't have location data
        if created or (not tracking.current_latitude or not tracking.current_longitude):
            # Try to get assistant's current location
            assistant_location = None
            if order.assistant:
                try:
                    user_location = UserLocation.objects.get(user=order.assistant)
                    assistant_location = user_location
                    
                    # Update tracking with current location
                    tracking.current_latitude = user_location.latitude
                    tracking.current_longitude = user_location.longitude
                    tracking.save()
                    
                    # Create initial location history entry
                    TrackingLocationHistory.objects.create(
                        tracking=tracking,
                        latitude=user_location.latitude,
                        longitude=user_location.longitude
                    )
                except UserLocation.DoesNotExist:
                    # Assistant location not available yet, but still create tracking
                    pass
            
            # Create waypoints from order locations
            if order.pickup_latitude and order.pickup_longitude:
                TrackingWaypoint.objects.get_or_create(
                    tracking=tracking,
                    waypoint_type='pickup',
                    defaults={
                        'latitude': order.pickup_latitude,
                        'longitude': order.pickup_longitude,
                        'name': order.pickup_address or 'Pickup Location',
                        'order_index': 0
                    }
                )
            
            if order.delivery_latitude and order.delivery_longitude:
                TrackingWaypoint.objects.get_or_create(
                    tracking=tracking,
                    waypoint_type='delivery',
                    defaults={
                        'latitude': order.delivery_latitude,
                        'longitude': order.delivery_longitude,
                        'name': order.delivery_address or 'Delivery Location',
                        'order_index': 1
                    }
                )
            
            # Create initial tracking event
            if assistant_location:
                TrackingEvent.objects.get_or_create(
                    tracking=tracking,
                    event_type='pickup_started',
                    defaults={
                        'description': 'Tracking automatically initialized when order was assigned',
                        'latitude': assistant_location.latitude,
                        'longitude': assistant_location.longitude
                    }
                )
    except Exception as e:
        # Log error but don't break the order status change
        logger.error(f"Error initializing tracking for order {order.id}: {str(e)}")


@receiver(pre_save, sender=Order)
def order_status_changed_tracking(sender, instance, **kwargs):
    """
    Automatically initialize tracking when order status changes to 'assigned' or 'in_progress'.
    This signal handler is separate from notifications to maintain separation of concerns.
    """
    # Skip for new orders
    if not instance.pk:
        return
    
    try:
        # Get the old instance from the database
        old_instance = Order.objects.get(pk=instance.pk)
        
        # If status hasn't changed, do nothing
        if old_instance.status == instance.status:
            return
        
        # Automatically initialize tracking when order is assigned or goes in_progress
        if instance.status in ['assigned', 'in_progress'] and instance.assistant:
            initialize_order_tracking(instance)
            
    except Order.DoesNotExist:
        # This is a new order, will be handled by post_save if needed
        pass
    except Exception as e:
        # Log error but don't break the order save
        logger.error(f"Error in order_status_changed_tracking for order {instance.id}: {str(e)}")

