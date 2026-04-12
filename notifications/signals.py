from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from orders.models import Order, OrderReview, HandymanOrder
from accounts.models import AssistantVerification

# Use synchronous version to avoid Redis dependency
from .services_sync import NotificationServiceSync as NotificationService

@receiver(pre_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    """
    Send notifications when order status changes
    """
    # Skip for new orders (they'll be handled by post_save)
    if not instance.pk:
        return
        
    try:
        # Get the old instance from the database
        old_instance = Order.objects.get(pk=instance.pk)
        
        # If status hasn't changed, do nothing
        if old_instance.status == instance.status:
            return
            
        # Get content type for generic relation
        content_type = ContentType.objects.get_for_model(Order)
        
        # Handle different status changes
        if instance.status == 'assigned':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_assigned',
                    title='Order Assigned',
                    message=f'Your order "{instance.title}" has been assigned to an assistant.',
                    content_object=instance
                )
                
            # Notify assistant
            if instance.assistant:
                NotificationService.create_notification(
                    recipient=instance.assistant,
                    notification_type='order_assigned',
                    title='New Order Assigned',
                    message=f'You have been assigned to order "{instance.title}".',
                    content_object=instance
                )
                
            # Update assigned_at timestamp
            if not instance.assigned_at:
                instance.assigned_at = timezone.now()
                
        elif instance.status == 'in_progress':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_started',
                    title='Order Started',
                    message=f'Your order "{instance.title}" is now in progress.',
                    content_object=instance
                )
                
            # Update started_at timestamp
            if not instance.started_at:
                instance.started_at = timezone.now()
                
        elif instance.status == 'completed':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_completed',
                    title='Order Completed',
                    message=f'Your order "{instance.title}" has been completed. Please leave a review!',
                    content_object=instance
                )
                
            # Notify assistant
            if instance.assistant:
                NotificationService.create_notification(
                    recipient=instance.assistant,
                    notification_type='order_completed',
                    title='Order Completed',
                    message=f'Order "{instance.title}" has been marked as completed.',
                    content_object=instance
                )
                
            # Update completed_at timestamp
            if not instance.completed_at:
                instance.completed_at = timezone.now()
                
        elif instance.status == 'cancelled':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_cancelled',
                    title='Order Cancelled',
                    message=f'Your order "{instance.title}" has been cancelled.',
                    content_object=instance
                )
                
            # Notify assistant if assigned
            if instance.assistant:
                NotificationService.create_notification(
                    recipient=instance.assistant,
                    notification_type='order_cancelled',
                    title='Order Cancelled',
                    message=f'Order "{instance.title}" has been cancelled.',
                    content_object=instance
                )
                
            # Update cancelled_at timestamp
            if not instance.cancelled_at:
                instance.cancelled_at = timezone.now()
                
    except Order.DoesNotExist:
        # This is a new order, will be handled by post_save
        pass

@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    """
    Send notification when a new order is created
    """
    if created:
        # Skip notification if this is a draft order
        if hasattr(instance, '_is_draft') and instance._is_draft:
            return
            
        # Notify client
        NotificationService.create_notification(
            recipient=instance.client,
            notification_type='order_created',
            title='Order Created',
            message=f'Your order "{instance.title}" has been created successfully.',
            content_object=instance
        )
        
        # Handlers are notified via frontend polling (useOrderNotifications hook)
        # This prevents duplicate notifications from backend signals
        # from django.contrib.auth import get_user_model
        # User = get_user_model()
        # handlers = User.objects.filter(user_type='handler')
        # for handler in handlers:
        #     NotificationService.create_notification(
        #         recipient=handler,
        #         notification_type='order_created',
        #         title='New Order',
        #         message=f'A new order "{instance.title}" has been created and needs assignment.',
        #         content_object=instance
        #     )

@receiver(post_save, sender=OrderReview)
def review_created(sender, instance, created, **kwargs):
    """
    Send notification when a review is submitted
    """
    if created and instance.order.assistant:
        # Notify assistant about the review
        NotificationService.create_notification(
            recipient=instance.order.assistant,
            notification_type='review',
            title='New Review',
            message=f'You received a {instance.rating}-star review for order "{instance.order.title}".',
            content_object=instance.order
        )

@receiver(pre_save, sender=HandymanOrder)
def handyman_order_status_changed(sender, instance, **kwargs):
    """
    Send notifications when handyman order status changes
    """
    # Skip for new orders (they'll be handled by post_save)
    if not instance.pk:
        return
        
    try:
        # Get the old instance from the database
        old_instance = HandymanOrder.objects.get(pk=instance.pk)
        
        # If status hasn't changed, do nothing
        if old_instance.status == instance.status:
            return
            
        # Get content type for generic relation
        content_type = ContentType.objects.get_for_model(HandymanOrder)
        
        # Handle different status changes
        if instance.status == 'assigned':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_assigned',
                    title='Handyman Service Assigned',
                    message=f'Your {instance.service_type.name} service has been assigned to a professional.',
                    content_object=instance
                )
                
            # Notify assistant
            if instance.assistant:
                NotificationService.create_notification(
                    recipient=instance.assistant,
                    notification_type='order_assigned',
                    title='New Service Assigned',
                    message=f'You have been assigned to a {instance.service_type.name} service.',
                    content_object=instance
                )
                
            # Update assigned_at timestamp
            if not instance.assigned_at:
                instance.assigned_at = timezone.now()
                
        elif instance.status == 'in_progress':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_started',
                    title='Service Started',
                    message=f'Your {instance.service_type.name} service is now in progress.',
                    content_object=instance
                )
                
            # Update started_at timestamp
            if not instance.started_at:
                instance.started_at = timezone.now()
                
        elif instance.status == 'completed':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_completed',
                    title='Service Completed',
                    message=f'Your {instance.service_type.name} service has been completed. Please leave a review!',
                    content_object=instance
                )
                
            # Notify assistant
            if instance.assistant:
                NotificationService.create_notification(
                    recipient=instance.assistant,
                    notification_type='order_completed',
                    title='Service Completed',
                    message=f'The {instance.service_type.name} service has been marked as completed.',
                    content_object=instance
                )
                
            # Update completed_at timestamp
            if not instance.completed_at:
                instance.completed_at = timezone.now()
                
        elif instance.status == 'cancelled':
            # Notify client
            if instance.client:
                NotificationService.create_notification(
                    recipient=instance.client,
                    notification_type='order_cancelled',
                    title='Service Cancelled',
                    message=f'Your {instance.service_type.name} service has been cancelled.',
                    content_object=instance
                )
                
            # Notify assistant if assigned
            if instance.assistant:
                NotificationService.create_notification(
                    recipient=instance.assistant,
                    notification_type='order_cancelled',
                    title='Service Cancelled',
                    message=f'The {instance.service_type.name} service has been cancelled.',
                    content_object=instance
                )
                
            # Update cancelled_at timestamp
            if not instance.cancelled_at:
                instance.cancelled_at = timezone.now()
                
    except HandymanOrder.DoesNotExist:
        # This is a new order, will be handled by post_save
        pass

@receiver(post_save, sender=HandymanOrder)
def handyman_order_created(sender, instance, created, **kwargs):
    """
    Send notification when a new handyman order is created
    """
    if created:
        # Notify client
        NotificationService.create_notification(
            recipient=instance.client,
            notification_type='order_created',
            title='Service Request Created',
            message=f'Your {instance.service_type.name} service request has been created successfully.',
            content_object=instance
        )
        
        # Notify handlers (all users with handler role)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        handlers = User.objects.filter(user_type='handler')
        for handler in handlers:
            NotificationService.create_notification(
                recipient=handler,
                notification_type='order_created',
                title='New Service Request',
                message=f'A new {instance.service_type.name} service request has been created and needs assignment.',
                content_object=instance
            )

@receiver(pre_save, sender=AssistantVerification)
def verification_status_changed(sender, instance, **kwargs):
    """
    Send notification when verification status changes
    """
    # Skip for new verifications
    if not instance.pk:
        return
        
    try:
        # Get the old instance from the database
        old_instance = AssistantVerification.objects.get(pk=instance.pk)
        
        # If status hasn't changed, do nothing
        if old_instance.status == instance.status:
            return
            
        # Get content type for generic relation
        content_type = ContentType.objects.get_for_model(AssistantVerification)
        
        # Handle different status changes
        if instance.status == 'approved':
            # Notify assistant
            NotificationService.create_notification(
                recipient=instance.assistant,
                notification_type='verification_approved',
                title='Verification Approved',
                message='Your verification has been approved. You can now accept orders.',
                content_object=instance
            )
                
        elif instance.status == 'rejected':
            # Notify assistant
            NotificationService.create_notification(
                recipient=instance.assistant,
                notification_type='verification_rejected',
                title='Verification Rejected',
                message=f'Your verification has been rejected. Reason: {instance.rejection_reason or "Not specified"}',
                content_object=instance
            )
                
    except AssistantVerification.DoesNotExist:
        # This is a new verification
        pass