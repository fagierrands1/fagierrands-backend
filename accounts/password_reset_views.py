from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import get_user_model
from .models import EmailOTP
import random
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_sms(phone_number, otp):
    logger.info(f"Sending OTP {otp} to {phone_number}")
    # Implement your SMS sending logic here
    pass


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number'],
            properties={'phone_number': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        responses={200: 'OTP sent', 404: 'User not found'}
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            otp_code = generate_otp()
            
            EmailOTP.objects.filter(user=user, otp_type='password_reset').delete()
            EmailOTP.objects.create(user=user, otp=otp_code, otp_type='password_reset')
            
            send_otp_sms(phone_number, otp_code)
            
            return Response({'message': 'OTP sent to your phone'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class VerifyPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'otp'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: 'OTP verified', 400: 'Invalid OTP'}
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        
        if not phone_number or not otp:
            return Response({'error': 'Phone number and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            otp_obj = EmailOTP.objects.filter(
                user=user, 
                otp=otp, 
                otp_type='password_reset',
                is_verified=False
            ).first()
            
            if not otp_obj:
                return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not otp_obj.is_valid():
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            otp_obj.is_verified = True
            otp_obj.save()
            
            return Response({
                'message': 'OTP verified successfully',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'otp', 'new_password'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: 'Password reset successful', 400: 'Invalid request'}
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        if not all([phone_number, otp, new_password]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            otp_obj = EmailOTP.objects.filter(
                user=user,
                otp=otp,
                otp_type='password_reset',
                is_verified=True
            ).first()
            
            if not otp_obj:
                return Response({'error': 'Invalid or unverified OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            otp_obj.delete()
            
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
