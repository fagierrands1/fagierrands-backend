from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import EmailVerification, User, OTPVerification
from datetime import timedelta
import logging
import random

logger = logging.getLogger(__name__)


def send_verification_email(user, request=None):
    """
    Send email verification to user
    """
    try:
        # Create or get existing verification token
        verification, created = EmailVerification.objects.get_or_create(
            user=user,
            is_used=False,
            defaults={}
        )
        
        # If not created, check if expired and create new one if needed
        if not created and verification.is_expired():
            verification.delete()
            verification = EmailVerification.objects.create(user=user)
        
        # Build verification URL
        if request:
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
        else:
            domain = 'fagierrands-server.vercel.app'  # Default production domain
            protocol = 'https'
        
        verification_url = f"{protocol}://{domain}/api/accounts/verify-email/{verification.token}/"
        
        # Prepare email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'frontend_url': settings.FRONTEND_URL,
        }
        
        # Render email templates
        html_message = render_to_string('email_verification.html', context)
        plain_message = render_to_string('email_verification.txt', context)
        
        # Send email
        send_mail(
            subject='Verify Your Email - Fagi Errands',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def verify_email_token(token):
    """
    Verify email using token
    Returns tuple (success, message, user)
    """
    try:
        verification = EmailVerification.objects.get(token=token, is_used=False)
        
        if verification.is_expired():
            return False, "Verification link has expired. Please request a new one.", None
        
        # Mark verification as used
        verification.is_used = True
        verification.save()
        
        # Mark user email as verified
        user = verification.user
        user.email_verified = True
        user.save()
        
        logger.info(f"Email verified successfully for user {user.email}")
        return True, "Email verified successfully!", user
        
    except EmailVerification.DoesNotExist:
        return False, "Invalid or expired verification link.", None
    except Exception as e:
        logger.error(f"Error verifying email token {token}: {str(e)}")
        return False, "An error occurred while verifying your email.", None


def send_verification_otp(user, request=None):
    """
    Send OTP verification email to user
    """
    try:
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Delete any existing unused OTP records for this user
        OTPVerification.objects.filter(user=user, is_used=False).delete()
        
        # Create new OTP record
        otp_record = OTPVerification.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=False,
            attempts=0
        )
        
        # Create email content
        subject = 'Email Verification - Fagi Errands'
        
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #333;">Email Verification - Fagi Errands</h2>
            </div>
            
            <p>Hello {user.first_name or 'there'}!</p>
            <p>Your email verification code is:</p>
            
            <div style="background: #f4f4f4; padding: 30px; text-align: center; margin: 30px 0; border-radius: 10px; border: 2px dashed #007bff;">
                <h1 style="font-size: 48px; color: #007bff; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace; font-weight: bold;">
                    {otp_code}
                </h1>
            </div>
            
            <p><strong>Enter this 6-digit code in the app to verify your email address.</strong></p>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    <strong>⏰ This code will expire in 1 hour.</strong>
                </p>
            </div>
            
            <p>If you didn't request this verification, please ignore this email.</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            
            <div style="text-align: center; color: #666; font-size: 14px;">
                <p>© 2024 Fagi Errands. All rights reserved.</p>
            </div>
        </body>
        </html>
        '''
        
        plain_content = f'''
        Email Verification - Fagi Errands
        
        Hello {user.first_name or 'there'}!
        
        Your email verification code is: {otp_code}
        
        Enter this 6-digit code in the app to verify your email address.
        
        This code will expire in 1 hour.
        
        If you didn't request this verification, please ignore this email.
        
        © 2024 Fagi Errands. All rights reserved.
        '''
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"OTP verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP verification email to {user.email}: {str(e)}")
        return False


def verify_otp_code(email, otp_code):
    """
    Verify OTP code for email verification
    Returns tuple (success, message, user)
    """
    try:
        user = User.objects.get(email=email)
        
        if user.email_verified:
            return False, "Email is already verified.", None
        
        # Find the OTP record
        try:
            otp_record = OTPVerification.objects.get(
                user=user,
                otp_code=otp_code,
                is_used=False
            )
        except OTPVerification.DoesNotExist:
            return False, "Invalid or expired verification code.", None
        
        # Check if OTP is expired
        if otp_record.is_expired():
            return False, "Verification code has expired. Please request a new one.", None
        
        # Mark OTP as used
        otp_record.is_used = True
        otp_record.save()
        
        # Mark user email as verified
        user.email_verified = True
        user.save()
        
        logger.info(f"Email verified successfully for user {user.email} using OTP")
        return True, "Email verified successfully!", user
        
    except User.DoesNotExist:
        return False, "No user found with this email address.", None
    except Exception as e:
        logger.error(f"Error verifying OTP for {email}: {str(e)}")
        return False, "An error occurred while verifying your email.", None


def resend_verification_email(email, request=None):
    """
    Resend verification email to user (now sends OTP instead of link)
    """
    try:
        user = User.objects.get(email=email)
        
        if user.email_verified:
            return False, "Email is already verified."
        
        # Send OTP verification email instead of link
        success = send_verification_otp(user, request)
        
        if success:
            return True, "Verification code sent successfully."
        else:
            return False, "Failed to send verification code."
            
    except User.DoesNotExist:
        return False, "No user found with this email address."
    except Exception as e:
        logger.error(f"Error resending verification email to {email}: {str(e)}")
        return False, "An error occurred while sending the verification code."