#!/usr/bin/env python3
"""
Test script to verify TextPie SMS with new sender ID
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.services.sms_service import SMSService

def test_sms_sender():
    """Test SMS sending with new sender ID"""
    
    print("=" * 60)
    print("TextPie SMS Configuration Test")
    print("=" * 60)
    
    # Display current configuration
    print(f"\n📋 Current Configuration:")
    print(f"   API Key: {os.getenv('TEXTPIE_API_KEY')[:20]}...")
    print(f"   Service ID: {os.getenv('TEXTPIE_SERVICE_ID')}")
    print(f"   Sender ID (Shortcode): {os.getenv('TEXTPIE_SHORTCODE')}")
    
    # Get phone number from user
    phone = input("\n📱 Enter your phone number (e.g., 0722123456 or 254722123456): ").strip()
    
    if not phone:
        print("❌ No phone number provided. Exiting.")
        return
    
    # Generate test OTP
    otp = SMSService.generate_otp()
    print(f"\n🔐 Generated OTP: {otp}")
    
    # Send SMS
    print(f"\n📤 Sending SMS to {phone}...")
    response = SMSService.send_otp(phone, otp, purpose='verification')
    
    print(f"\n📥 Response from TextPie:")
    print(f"   {response}")
    
    # Check response
    if response.get('success') or response.get('status_code') == '100':
        print("\n✅ SMS sent successfully!")
        print(f"   Sender ID: FagiErrands")
        print(f"   Check your phone for the OTP: {otp}")
    else:
        print("\n❌ Failed to send SMS")
        print(f"   Error: {response.get('status_desc', 'Unknown error')}")
        print("\n🔍 Troubleshooting tips:")
        print("   1. Verify sender ID 'FagiErrands' is approved in TextPie dashboard")
        print("   2. Check if your TextPie account has sufficient credits")
        print("   3. Ensure the sender ID is active (not pending approval)")
        print("   4. Verify API key and Service ID are correct")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_sms_sender()
