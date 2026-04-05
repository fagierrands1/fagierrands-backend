import json
import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import Notification, PushToken

class NotificationServiceSync:
    """
    Synchronous version of NotificationService that doesn't use Celery
    """
    
    @staticmethod
    def create_notification(recipient, notification_type, title, message, content_object=None):
        """
        Create a notification in the database (synchronous version)
        
        Args:
            recipient: User object who will receive the notification
            notification_type: Type of notification (from Notification.NOTIFICATION_TYPES)
            title: Notification title
            message: Notification message
            content_object: Optional related object (Order, Verification, etc.)
            
        Returns:
            Notification object
        """
        notification = Notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message
        )
        
        if content_object:
            notification.content_object = content_object
            
        notification.save()
        
        # Skip sending push notifications to avoid Redis dependency
        # Just log that we would have sent a notification
        print(f"[NOTIFICATION] Would send push notification: {title} - {message} to {recipient}")
        
        return notification