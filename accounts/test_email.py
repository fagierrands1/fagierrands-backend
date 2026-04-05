"""
Email configuration test utilities
Run this to verify email settings are correct
"""

from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def test_email_configuration():
    """Test if email configuration is working"""
    try:
        print("=" * 60)
        print("EMAIL CONFIGURATION TEST")
        print("=" * 60)
        
        print(f"Email Backend: {settings.EMAIL_BACKEND}")
        print(f"Email Host: {settings.EMAIL_HOST}")
        print(f"Email Port: {settings.EMAIL_PORT}")
        print(f"Email Use TLS: {settings.EMAIL_USE_TLS}")
        print(f"Email Use SSL: {settings.EMAIL_USE_SSL}")
        print(f"Email Host User: {settings.EMAIL_HOST_USER}")
        print(f"Email Host Password: {'*' * 10 if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
        print(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")
        print("=" * 60)
        
        # Check if credentials are set
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("❌ ERROR: Email credentials not configured!")
            print("\nTo fix:")
            print("1. Set EMAIL_HOST_USER environment variable")
            print("2. Set EMAIL_HOST_PASSWORD environment variable")
            print("3. Verify the sender email is verified in Brevo/Gmail")
            return False
        
        print("✓ Email configuration looks valid")
        return True
        
    except Exception as e:
        logger.error(f"Email configuration test failed: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return False


def send_test_email(recipient_email):
    """Send a test email to verify SMTP is working"""
    try:
        print(f"\nSending test email to: {recipient_email}")
        
        send_mail(
            subject='Fagi Errands - Email Test',
            message='If you received this email, your email configuration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message='<p>If you received this email, your email configuration is working correctly!</p>',
            fail_silently=False,
        )
        
        print("✓ Test email sent successfully!")
        logger.info(f"Test email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}", exc_info=True)
        print(f"❌ Failed to send test email: {str(e)}")
        return False


if __name__ == '__main__':
    # Run tests
    config_ok = test_email_configuration()
    
    if config_ok:
        # Uncomment to send a test email
        # send_test_email('your-email@example.com')
        pass
