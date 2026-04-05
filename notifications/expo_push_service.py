"""
Expo Push Notification Service
Handles sending push notifications via Expo Push Notification API
"""
import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class ExpoPushService:
    """Service for sending push notifications via Expo"""
    
    @staticmethod
    def send_push_notification(
        push_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        sound: str = 'default',
        badge: Optional[int] = None,
        priority: str = 'high',
        channel_id: str = 'default'
    ) -> Dict:
        """
        Send push notification to multiple Expo push tokens
        
        Args:
            push_tokens: List of Expo push tokens
            title: Notification title
            body: Notification body/message
            data: Additional data to send with notification
            sound: Sound to play ('default' or None)
            badge: Badge count to display
            priority: 'default', 'normal', or 'high'
            channel_id: Android notification channel ID
            
        Returns:
            Dict with success status and results
        """
        if not push_tokens:
            logger.warning("No push tokens provided")
            return {
                'success': False,
                'error': 'No push tokens provided',
                'results': []
            }
        
        # Filter valid Expo push tokens
        valid_tokens = [
            token for token in push_tokens 
            if token and (token.startswith('ExponentPushToken[') or token.startswith('ExpoPushToken['))
        ]
        
        if not valid_tokens:
            logger.warning(f"No valid Expo push tokens found in: {push_tokens}")
            return {
                'success': False,
                'error': 'No valid Expo push tokens',
                'results': []
            }
        
        # Prepare messages
        messages = []
        for token in valid_tokens:
            message = {
                'to': token,
                'title': title,
                'body': body,
                'sound': sound,
                'priority': priority,
                'channelId': channel_id,
            }
            
            if data:
                message['data'] = data
            
            if badge is not None:
                message['badge'] = badge
            
            messages.append(message)
        
        try:
            # Send to Expo Push API
            response = requests.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse results
            success_count = 0
            error_count = 0
            errors = []
            
            if 'data' in result:
                for ticket in result['data']:
                    if ticket.get('status') == 'ok':
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(ticket.get('message', 'Unknown error'))
            
            logger.info(f"Push notification sent: {success_count} success, {error_count} errors")
            
            return {
                'success': success_count > 0,
                'total': len(valid_tokens),
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
                'results': result.get('data', [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending push notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    @staticmethod
    def send_to_user(user, title: str, body: str, data: Optional[Dict] = None) -> Dict:
        """
        Send push notification to a specific user
        
        Args:
            user: User object
            title: Notification title
            body: Notification body
            data: Additional data
            
        Returns:
            Dict with success status
        """
        from .models import PushToken
        
        # Get user's push tokens
        tokens = PushToken.objects.filter(user=user).values_list('token', flat=True)
        
        if not tokens:
            logger.warning(f"No push tokens found for user {user.username}")
            return {
                'success': False,
                'error': 'No push tokens found for user'
            }
        
        return ExpoPushService.send_push_notification(
            push_tokens=list(tokens),
            title=title,
            body=body,
            data=data
        )
    
    @staticmethod
    def send_broadcast(
        user_queryset,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        batch_size: int = 100
    ) -> Dict:
        """
        Send push notification to multiple users (broadcast)
        
        Args:
            user_queryset: QuerySet of User objects
            title: Notification title
            body: Notification body
            data: Additional data
            batch_size: Number of notifications to send per batch
            
        Returns:
            Dict with success status and statistics
        """
        from .models import PushToken
        
        # Get all push tokens for users in queryset
        user_ids = user_queryset.values_list('id', flat=True)
        tokens = PushToken.objects.filter(user_id__in=user_ids).values_list('token', flat=True)
        
        if not tokens:
            logger.warning("No push tokens found for broadcast")
            return {
                'success': False,
                'error': 'No push tokens found',
                'total_recipients': 0,
                'successful_sends': 0,
                'failed_sends': 0
            }
        
        # Send in batches
        token_list = list(tokens)
        total_success = 0
        total_errors = 0
        
        for i in range(0, len(token_list), batch_size):
            batch = token_list[i:i + batch_size]
            result = ExpoPushService.send_push_notification(
                push_tokens=batch,
                title=title,
                body=body,
                data=data
            )
            
            total_success += result.get('success_count', 0)
            total_errors += result.get('error_count', 0)
        
        return {
            'success': total_success > 0,
            'total_recipients': len(token_list),
            'successful_sends': total_success,
            'failed_sends': total_errors
        }