# Use synchronous version to avoid Redis dependency
from .services_sync import NotificationServiceSync as NotificationService
from .models import Notification

# Define a dummy shared_task decorator
def dummy_shared_task(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.delay = lambda *a, **kw: None
    return wrapper

# Replace shared_task with our dummy version
shared_task = dummy_shared_task

@shared_task
def send_push_notification(notification_id):
    """
    Dummy task that doesn't actually send push notifications
    
    Args:
        notification_id: ID of the notification to send
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        print(f"[NOTIFICATION] Would send push notification for notification {notification_id}")
        return f"Push notification simulated for notification {notification_id}"
    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as e:
        return f"Error simulating push notification: {str(e)}"

@shared_task
def clean_old_notifications(days=30):
    """
    Celery task to clean old notifications
    
    Args:
        days: Number of days to keep notifications (default: 30)
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff_date).delete()
    
    return f"Deleted {deleted_count} old notifications"