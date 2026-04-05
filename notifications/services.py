import json
import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import Notification, PushToken

class NotificationService:
    """
    Service for creating and sending notifications
    """
    
    @staticmethod
    def create_notification(recipient, notification_type, title, message, content_object=None):
        """
        Create a notification in the database
        
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
        
        # Send push notification asynchronously if user has registered tokens
        from .tasks import send_push_notification
        send_push_notification.delay(notification.id)
        
        return notification
    
    @staticmethod
    def send_push_notification(notification):
        """
        Send push notification to all user devices
        
        Args:
            notification: Notification object
        """
        # Get all user push tokens
        push_tokens = PushToken.objects.filter(user=notification.recipient)
        
        if not push_tokens.exists():
            return
        
        # Prepare notification payload
        payload = {
            'title': notification.title,
            'message': notification.message,
            'notification_id': notification.id
        }
        
        # Add action URL if content object exists
        if notification.content_type and notification.object_id:
            model_name = notification.content_type.model
            
            if model_name == 'order':
                payload['action_url'] = f'/orders/{notification.object_id}'
            elif model_name == 'assistantverification':
                payload['action_url'] = '/verification-status'
        
        # Group tokens by device type
        web_tokens = [token.token for token in push_tokens if token.device_type == 'web']
        ios_tokens = [token.token for token in push_tokens if token.device_type == 'ios']
        android_tokens = [token.token for token in push_tokens if token.device_type == 'android']
        
        # Send to web tokens using Web Push protocol
        if web_tokens and hasattr(settings, 'VAPID_PRIVATE_KEY'):
            NotificationService._send_web_push(web_tokens, payload)
            
        # Send to iOS and Android using FCM
        if (ios_tokens or android_tokens) and hasattr(settings, 'FCM_SERVER_KEY'):
            if ios_tokens:
                NotificationService._send_fcm(ios_tokens, payload, 'ios')
            if android_tokens:
                NotificationService._send_fcm(android_tokens, payload, 'android')
    
    @staticmethod
    def _send_web_push(tokens, payload):
        """
        Send Web Push notifications
        
        Args:
            tokens: List of web push subscription objects (as strings)
            payload: Notification payload
        """
        try:
            from pywebpush import webpush, WebPushException
            
            for token_str in tokens:
                try:
                    # Parse the subscription info
                    subscription_info = json.loads(token_str)
                    
                    webpush(
                        subscription_info=subscription_info,
                        data=json.dumps(payload),
                        vapid_private_key=settings.VAPID_PRIVATE_KEY,
                        vapid_claims={
                            "sub": f"mailto:{settings.WEBPUSH_EMAIL}"
                        }
                    )
                except WebPushException as e:
                    # Handle expired tokens or other errors
                    print(f"Web Push failed: {e}")
                    if "pushsubscription is no longer valid" in str(e).lower():
                        # Delete the invalid token
                        PushToken.objects.filter(token=token_str).delete()
        except ImportError:
            print("pywebpush not installed. Web push notifications not sent.")
    
    @staticmethod
    def _send_fcm(tokens, payload, platform):
        """
        Send Firebase Cloud Messaging (FCM) notifications
        
        Args:
            tokens: List of FCM tokens
            payload: Notification payload
            platform: 'ios' or 'android'
        """
        try:
            fcm_api_url = "https://fcm.googleapis.com/fcm/send"
            
            # Prepare FCM message based on platform
            if platform == 'ios':
                message = {
                    "registration_ids": tokens,
                    "notification": {
                        "title": payload['title'],
                        "body": payload['message'],
                        "sound": "default"
                    },
                    "data": payload
                }
            else:  # android
                message = {
                    "registration_ids": tokens,
                    "data": payload
                }
            
            # Send to FCM
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"key={settings.FCM_SERVER_KEY}"
            }
            
            response = requests.post(fcm_api_url, headers=headers, data=json.dumps(message))
            
            # Handle response and invalid tokens
            if response.status_code == 200:
                result = response.json()
                
                # Check for failed tokens
                if 'results' in result:
                    for idx, item in enumerate(result['results']):
                        if 'error' in item:
                            if item['error'] in ['NotRegistered', 'InvalidRegistration']:
                                # Delete the invalid token
                                PushToken.objects.filter(token=tokens[idx]).delete()
            else:
                print(f"FCM request failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Error sending FCM notification: {e}")