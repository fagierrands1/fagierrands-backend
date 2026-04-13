"""
Password Reset API v1
Clean implementation with 2-step process
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import get_user_model
from django.utils import timezone
from .serializers import normalize_phone_number
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RequestPasswordResetV1(APIView):
    """
    Step 1: Request password reset - sends 4-digit OTP to phone
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication completely

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number'],
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Phone number (e.g., 0796605409)'
                )
            }
        ),
        responses={
            200: openapi.Response('OTP sent successfully'),
            404: openapi.Response('User not found')
        }
    )
    def post(self, request):
        from .services.sms_service import SMSService
        
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)
        
        try:
            user = User.objects.get(phone_number=normalized_phone)
        except User.DoesNotExist:
            # Don't reveal if user exists or not (security)
            return Response({
                'message': 'If this phone number exists, an OTP has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate 4-digit OTP
        otp = SMSService.generate_otp()
        user.phone_otp = otp
        user.phone_otp_created_at = timezone.now()
        user.save()
        
        # Send OTP via SMS
        try:
            response = SMSService.send_otp(normalized_phone, otp, purpose='password_reset')
            if response.get('status_code') == '1000':
                logger.info(f"Password reset OTP sent to {normalized_phone}")
            else:
                logger.error(f"Failed to send OTP: {response.get('status_desc')}")
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
        
        return Response({
            'message': 'OTP sent to your phone number',
            'phone_number': normalized_phone
        }, status=status.HTTP_200_OK)


class ResetPasswordV1(APIView):
    """
    Step 2: Reset password with OTP and new password
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication completely

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'otp', 'new_password', 'confirm_password'],
            properties={
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Phone number'
                ),
                'otp': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='4-digit OTP code'
                ),
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='New password'
                ),
                'confirm_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Confirm new password'
                )
            }
        ),
        responses={
            200: openapi.Response('Password reset successful'),
            400: openapi.Response('Invalid request'),
            404: openapi.Response('User not found')
        }
    )
    def post(self, request):
        from .services.sms_service import SMSService
        
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate all fields
        if not all([phone_number, otp, new_password, confirm_password]):
            return Response({
                'error': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check passwords match
        if new_password != confirm_password:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        if len(new_password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)
        
        try:
            user = User.objects.get(phone_number=normalized_phone)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify OTP
        if user.phone_otp != otp:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check OTP expiration
        if not SMSService.is_otp_valid(user.phone_otp_created_at):
            return Response({
                'error': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        user.set_password(new_password)
        user.phone_otp = None
        user.phone_otp_created_at = None
        user.save()
        
        logger.info(f"Password reset successful for {normalized_phone}")
        
        return Response({
            'message': 'Password reset successful. Please login with your new password.'
        }, status=status.HTTP_200_OK)
