import os
import random
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

class SMSService:
    """Service for sending SMS via TextPie API"""
    
    API_URL = "https://api.textpie.co.ke/sms/sendsms"
    
    @staticmethod
    def generate_otp():
        """Generate a 4-digit OTP"""
        return str(random.randint(1000, 9999))
    
    @staticmethod
    def send_otp(phone_number, otp):
        """
        Send OTP via SMS to the given phone number
        
        Args:
            phone_number (str): Phone number in format 254... or +254... or 0722...
            otp (str): 4-digit OTP code
            
        Returns:
            dict: Response from TextPie API or error dict
        """
        # Ensure phone number is in correct format (254...)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        message = f"Your FagiErrands verification code is: {otp}. Valid for 5 minutes. Do not share this code."
        
        payload = {
            "api_key": os.getenv('TEXTPIE_API_KEY'),
            "service_id": int(os.getenv('TEXTPIE_SERVICE_ID', 0)),
            "mobile": phone_number,
            "response_type": "json",
            "shortcode": os.getenv('TEXTPIE_SHORTCODE'),
            "message": message
        }
        
        try:
            response = requests.post(SMSService.API_URL, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "status_code": "error",
                "status_desc": str(e),
                "success": False
            }
    
    @staticmethod
    def is_otp_valid(otp_created_at):
        """Check if OTP is still valid (within 5 minutes)"""
        if not otp_created_at:
            return False
        expiry_time = otp_created_at + timedelta(minutes=5)
        return timezone.now() <= expiry_time
