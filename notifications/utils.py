import json
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_web_push_notification(subscription_info, title, message, data=None):
    """
    Send a web push notification to a specific subscription
    
    Args:
        subscription_info: Web Push subscription info (dict or JSON string)
        title: Notification title
        message: Notification message
        data: Additional data to send with the notification
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if pywebpush is available
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            logger.warning("pywebpush not installed. Cannot send web push notifications.")
            return False
        
        # Parse subscription_info if it's a string
        if isinstance(subscription_info, str):
            subscription_info = json.loads(subscription_info)
        
        # Check if VAPID keys are configured
        vapid_keys = get_vapid_key()
        if not vapid_keys['private_key']:
            logger.warning("VAPID private key not configured. Cannot send web push notifications.")
            return False
        
        # Prepare payload
        payload = {
            'title': title,
            'message': message
        }
        
        # Add additional data if provided
        if data:
            payload.update(data)
        
        # Send notification
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_keys['private_key'],
            vapid_claims={
                "sub": f"mailto:{getattr(settings, 'WEBPUSH_EMAIL', 'admin@fagierrands.com')}"
            }
        )
        
        logger.info(f"Web push notification sent successfully: {title}")
        return True
        
    except WebPushException as e:
        logger.error(f"Web Push failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending web push notification: {e}")
        return False

def get_vapid_key():
    """
    Generate VAPID keys for Web Push if they don't exist
    
    Returns:
        dict: Dictionary with public and private keys
    """
    try:
        # Check if keys already exist in settings and are not empty
        if (hasattr(settings, 'VAPID_PRIVATE_KEY') and hasattr(settings, 'VAPID_PUBLIC_KEY') 
            and settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY):
            return {
                'public_key': settings.VAPID_PUBLIC_KEY,
                'private_key': settings.VAPID_PRIVATE_KEY
            }
        
        # Try to import and generate new keys
        try:
            from py_vapid import Vapid
            
            # Generate new keys
            vapid = Vapid()
            vapid.generate_keys()
            
            private_key = vapid.private_key.decode('utf-8')
            public_key = vapid.public_key.decode('utf-8')
            
            logger.info("Generated new VAPID keys")
            return {
                'public_key': public_key,
                'private_key': private_key
            }
            
        except ImportError:
            logger.warning("py_vapid not installed. Using fallback VAPID keys.")
            # Return fallback keys for development/testing
            return {
                'public_key': 'BEl62iUYgUivxIkv69yViEuiBIa40HI0DLLuxazjqyLSdkN-CgVPJe6lbT-WJC_MnZWgqaKdwn2-xV8JkpGOGzs',
                'private_key': 'nNEhEHGzwCe3uIXQnLAFHgFWqh-QkXfPdlVtdKyVS_s'
            }
        
    except Exception as e:
        logger.error(f"Error getting VAPID keys: {e}")
        # Return empty keys if everything fails
        return {
            'public_key': '',
            'private_key': ''
        }

def urlsafe_base64_encode(data):
    """
    URL-safe base64 encoding for VAPID keys
    
    Args:
        data: Data to encode
        
    Returns:
        str: URL-safe base64 encoded string
    """
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')