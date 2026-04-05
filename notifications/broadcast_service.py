"""
Broadcast Notification Service
Handles sending broadcast notifications to users
"""
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import BroadcastNotification, Notification
from .expo_push_service import ExpoPushService

User = get_user_model()
logger = logging.getLogger(__name__)


class BroadcastService:
    """Service for managing broadcast notifications"""
    
    @staticmethod
    def get_target_users(target_audience: str):
        """
        Get users based on target audience
        
        Args:
            target_audience: 'all', 'clients', 'assistants', 'handlers', 'admins'
            
        Returns:
            QuerySet of User objects
        """
        if target_audience == 'all':
            return User.objects.filter(is_active=True)
        elif target_audience == 'clients':
            return User.objects.filter(is_active=True, user_type='client')
        elif target_audience == 'assistants':
            return User.objects.filter(is_active=True, user_type='assistant')
        elif target_audience == 'handlers':
            return User.objects.filter(is_active=True, user_type='handler')
        elif target_audience == 'admins':
            return User.objects.filter(is_active=True, is_staff=True)
        else:
            return User.objects.none()
    
    @staticmethod
    def send_broadcast(broadcast_id: int) -> dict:
        """
        Send a broadcast notification
        
        Args:
            broadcast_id: ID of BroadcastNotification
            
        Returns:
            Dict with success status and statistics
        """
        try:
            broadcast = BroadcastNotification.objects.get(id=broadcast_id)
        except BroadcastNotification.DoesNotExist:
            logger.error(f"Broadcast notification {broadcast_id} not found")
            return {
                'success': False,
                'error': 'Broadcast notification not found'
            }
        
        # Check if already sent
        if broadcast.status == 'sent':
            logger.warning(f"Broadcast {broadcast_id} already sent")
            return {
                'success': False,
                'error': 'Broadcast already sent'
            }
        
        # Update status to sending
        broadcast.status = 'sending'
        broadcast.save()
        
        try:
            # Get target users
            users = BroadcastService.get_target_users(broadcast.target_audience)
            
            # Prepare notification data
            data = {
                'type': broadcast.notification_type,
                'broadcast_id': broadcast.id,
            }
            
            if broadcast.action_url:
                data['action_url'] = broadcast.action_url
            
            if broadcast.image_url:
                data['image_url'] = broadcast.image_url
            
            # Send push notifications
            push_result = ExpoPushService.send_broadcast(
                user_queryset=users,
                title=broadcast.title,
                body=broadcast.message,
                data=data
            )
            
            # Create in-app notifications for each user
            notifications_created = 0
            for user in users:
                try:
                    Notification.objects.create(
                        recipient=user,
                        notification_type=broadcast.notification_type,
                        title=broadcast.title,
                        message=broadcast.message
                    )
                    notifications_created += 1
                except Exception as e:
                    logger.error(f"Error creating notification for user {user.id}: {e}")
            
            # Update broadcast status
            broadcast.status = 'sent'
            broadcast.sent_at = timezone.now()
            broadcast.total_recipients = push_result.get('total_recipients', 0)
            broadcast.successful_sends = push_result.get('successful_sends', 0)
            broadcast.failed_sends = push_result.get('failed_sends', 0)
            broadcast.save()
            
            logger.info(
                f"Broadcast {broadcast_id} sent: "
                f"{broadcast.successful_sends} success, "
                f"{broadcast.failed_sends} failed, "
                f"{notifications_created} in-app notifications created"
            )
            
            return {
                'success': True,
                'total_recipients': broadcast.total_recipients,
                'successful_sends': broadcast.successful_sends,
                'failed_sends': broadcast.failed_sends,
                'notifications_created': notifications_created
            }
            
        except Exception as e:
            logger.error(f"Error sending broadcast {broadcast_id}: {e}")
            broadcast.status = 'failed'
            broadcast.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_and_send_broadcast(
        title: str,
        message: str,
        notification_type: str,
        target_audience: str,
        created_by,
        action_url: str = None,
        image_url: str = None,
        send_immediately: bool = True
    ) -> dict:
        """
        Create and optionally send a broadcast notification
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: 'app_update', 'promotion', or 'announcement'
            target_audience: 'all', 'clients', 'assistants', 'handlers', 'admins'
            created_by: User who created the broadcast
            action_url: Optional URL to open
            image_url: Optional image URL
            send_immediately: Whether to send immediately or save as draft
            
        Returns:
            Dict with success status and broadcast info
        """
        try:
            # Create broadcast
            broadcast = BroadcastNotification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                target_audience=target_audience,
                created_by=created_by,
                action_url=action_url,
                image_url=image_url,
                status='draft'
            )
            
            if send_immediately:
                # Send immediately
                result = BroadcastService.send_broadcast(broadcast.id)
                return {
                    'success': result['success'],
                    'broadcast_id': broadcast.id,
                    'broadcast': broadcast,
                    'send_result': result
                }
            else:
                # Save as draft
                return {
                    'success': True,
                    'broadcast_id': broadcast.id,
                    'broadcast': broadcast,
                    'status': 'draft'
                }
                
        except Exception as e:
            logger.error(f"Error creating broadcast: {e}")
            return {
                'success': False,
                'error': str(e)
            }