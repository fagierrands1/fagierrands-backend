from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import OTPVerification, User
import logging

logger = logging.getLogger(__name__)


def send_otp_email(user, request=None):
    """
    Send OTP verification email to user
    """
    try:
        # Delete any existing unused OTP verifications for this user
        OTPVerification.objects.filter(user=user, is_used=False).delete()
        
        # Create new OTP verification
        otp_verification = OTPVerification.objects.create(user=user)
        
        logger.info(f"Created OTP {otp_verification.otp_code} for user {user.email}")
        
        # Prepare email context
        context = {
            'user': user,
            'otp_code': otp_verification.otp_code,
            'expires_in_minutes': 10,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'https://fagierrands-x9ow.vercel.app'),
        }
        
        try:
            # Render email templates
            html_message = render_to_string('otp_verification.html', context)
            plain_message = render_to_string('otp_verification.txt', context)
        except Exception as template_error:
            logger.error(f"Template rendering error: {str(template_error)}")
            # Fallback if templates don't exist
            plain_message = f"Your verification code is: {otp_verification.otp_code}\n\nThis code expires in 10 minutes."
            html_message = f"<p>Your verification code is: <strong>{otp_verification.otp_code}</strong></p><p>This code expires in 10 minutes.</p>"
        
        logger.info(f"Email config - HOST: {settings.EMAIL_HOST}, USER: {settings.EMAIL_HOST_USER}, FROM: {settings.DEFAULT_FROM_EMAIL}")
        
        # Send email
        send_mail(
            subject='Your Verification Code - Fagi Errands',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"OTP verification email sent successfully to {user.email} with code {otp_verification.otp_code}")
        return True, "OTP sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {str(e)}", exc_info=True)
        return False, f"Failed to send OTP email: {str(e)}"


def verify_otp(email, otp_code):
    """
    Verify OTP code for email
    Returns tuple (success, message, user)
    """
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            return False, "No user found with this email address.", None
        
        # Get the latest unused OTP verification for this user
        otp_verification = OTPVerification.objects.filter(
            user=user, 
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp_verification:
            return False, "No valid OTP found. Please request a new one.", None
        
        # Check if OTP has expired
        if otp_verification.is_expired():
            return False, "OTP has expired. Please request a new one.", None
        
        # Check if maximum attempts reached
        if otp_verification.is_max_attempts_reached():
            return False, "Maximum verification attempts reached. Please request a new OTP.", None
        
        # Increment attempts
        otp_verification.increment_attempts()
        
        # Check if OTP matches
        if otp_verification.otp_code != otp_code:
            remaining_attempts = otp_verification.max_attempts - otp_verification.attempts
            if remaining_attempts > 0:
                return False, f"Invalid OTP. {remaining_attempts} attempts remaining.", None
            else:
                return False, "Invalid OTP. Maximum attempts reached. Please request a new OTP.", None
        
        # OTP is valid - mark as used and verify user email
        otp_verification.is_used = True
        otp_verification.save()
        
        user.email_verified = True
        user.save()
        
        logger.info(f"OTP verified successfully for user {user.email}")
        return True, "Email verified successfully!", user
    except Exception as e:
        logger.error(f"Error verifying OTP for {email}: {str(e)}")
        return False, "An error occurred while verifying OTP.", None


def resend_otp_email(email, request=None):
    """
    Resend OTP verification email to user
    """
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            return False, "No user found with this email address."
        
        if user.email_verified:
            return False, "Email is already verified."
        
        # Check if user has too many recent OTP requests (rate limiting)
        recent_otps = OTPVerification.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
        ).count()
        
        if recent_otps >= 3:
            return False, "Too many OTP requests. Please wait a minute before requesting again."
        
        # Send new OTP email
        success, message = send_otp_email(user, request)
        
        if success:
            return True, "New OTP sent successfully."
        else:
            return False, message
    except Exception as e:
        logger.error(f"Error resending OTP email to {email}: {str(e)}")
        return False, "An error occurred while sending the OTP email."


def get_otp_status(email):
    """
    Get OTP verification status for a user
    """
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            return {
                'success': False,
                'email_verified': False,
                'message': 'No user found with this email address'
            }
        
        if user.email_verified:
            return {
                'success': True,
                'email_verified': True,
                'message': 'Email is already verified'
            }
        
        # Get latest OTP verification
        otp_verification = OTPVerification.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp_verification:
            return {
                'success': True,
                'email_verified': False,
                'has_pending_otp': False,
                'message': 'No pending OTP verification'
            }
        
        return {
            'success': True,
            'email_verified': False,
            'has_pending_otp': True,
            'otp_expired': otp_verification.is_expired(),
            'attempts_remaining': max(0, otp_verification.max_attempts - otp_verification.attempts),
            'expires_at': otp_verification.expires_at.isoformat(),
            'message': 'OTP verification pending'
        }
    except Exception as e:
        logger.error(f"Error getting OTP status for {email}: {str(e)}")
        return {
            'success': False,
            'email_verified': False,
            'message': 'An error occurred while checking OTP status'
        }


def send_password_reset_email(user, otp_code):
    """
    Send password reset OTP email to user
    """
    try:
        from django.core.mail import EmailMultiAlternatives
        
        subject = 'Fagi Errands - Password Reset Code'
        plain_message = f'Your password reset code is: {otp_code}\n\nThis code expires in 1 hour.\n\nIf you did not request this, please ignore this email.'
        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #333;">Password Reset - Fagi Errands</h2>
            </div>
            
            <p>Hello {user.first_name or 'there'}!</p>
            <p>Your password reset code is:</p>
            
            <div style="background: #f4f4f4; padding: 30px; text-align: center; margin: 30px 0; border-radius: 10px; border: 2px dashed #007bff;">
                <h1 style="font-size: 48px; color: #007bff; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace; font-weight: bold;">
                    {otp_code}
                </h1>
            </div>
            
            <p><strong>Enter this 6-digit code to reset your password.</strong></p>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    <strong>⏰ This code will expire in 1 hour.</strong>
                </p>
            </div>
            
            <p>If you didn't request a password reset, please ignore this email.</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            
            <div style="text-align: center; color: #666; font-size: 14px;">
                <p><strong>Fagi Errands</strong></p>
                <p>Your trusted delivery service</p>
                <p>🚚 Fast • Reliable • Affordable</p>
            </div>
        </body>
        </html>
        '''
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send(fail_silently=False)
        
        logger.info(f"Password reset OTP sent to {user.email}")
        return True, "Password reset email sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
        return False, f"Failed to send password reset email: {str(e)}"
