"""
Live M-Pesa STK Push Test
This will send an actual STK Push prompt to a test phone number
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
import django
django.setup()

from orders.mpesa_service import MpesaDarajaService
import time

print("="*70)
print("  M-PESA LIVE STK PUSH TEST")
print("="*70)

print("\n⚠️  WARNING: This will send an actual STK Push prompt!")
print("Make sure you have:")
print("  1. Valid M-Pesa sandbox credentials")
print("  2. A test phone number registered in sandbox")
print("  3. The Safaricom test app installed (for sandbox)")
print("\nSandbox Test Phone Numbers (from Safaricom):")
print("  - 254708374149")
print("  - 254712345678 (generic test number)")
print("="*70)

# Get user input
proceed = input("\nDo you want to proceed? (yes/no): ")

if proceed.lower() != 'yes':
    print("Test cancelled.")
    sys.exit(0)

phone = input("\nEnter test phone number (e.g., 254708374149): ").strip()
amount_input = input("Enter test amount in KSh (e.g., 1 or 10): ").strip()

try:
    amount = int(amount_input)
    if amount < 1:
        print("❌ Amount must be at least 1 KSh")
        sys.exit(1)
except ValueError:
    print("❌ Invalid amount. Please enter a number.")
    sys.exit(1)

print("\n" + "="*70)
print("  INITIATING STK PUSH")
print("="*70)

# Initialize service
service = MpesaDarajaService()

print(f"\n📱 Phone: {phone}")
print(f"💰 Amount: KSh {amount}")
print(f"🔧 Environment: {service.environment}")
print(f"🏢 Shortcode: {service.shortcode}")

# Send STK Push
print("\n⏳ Sending STK Push request...")

try:
    result = service.stk_push(
        phone_number=254758292353,
        amount=amount,
        account_reference="TEST001",
        transaction_desc="Test Payment - Fagi Errands"
    )
    
    print("\n" + "="*70)
    print("  STK PUSH RESULT")
    print("="*70)
    
    if result.get('success'):
        print("\n✅ STK Push sent successfully!")
        print(f"\n📋 Transaction Details:")
        print(f"   Checkout Request ID: {result.get('CheckoutRequestID')}")
        print(f"   Merchant Request ID: {result.get('MerchantRequestID')}")
        print(f"   Response Code: {result.get('ResponseCode')}")
        print(f"   Response Description: {result.get('ResponseDescription')}")
        print(f"   Customer Message: {result.get('CustomerMessage')}")
        
        print("\n📱 Check your phone for the M-Pesa prompt!")
        print("   You have 60 seconds to complete the payment.")
        
        # Wait and check status
        checkout_request_id = result.get('CheckoutRequestID')
        merchant_request_id = result.get('MerchantRequestID')
        
        if checkout_request_id and merchant_request_id:
            print("\n⏳ Waiting 10 seconds before checking status...")
            time.sleep(10)
            
            print("\n🔍 Checking transaction status...")
            status_result = service.query_stk_status(checkout_request_id)
            
            print("\n📊 Status Query Result:")
            print(f"   Result Code: {status_result.get('ResultCode')}")
            print(f"   Result Description: {status_result.get('ResultDesc')}")
            
            if status_result.get('ResultCode') == '0':
                print("\n✅ Payment completed successfully!")
            elif status_result.get('ResultCode') == '1032':
                print("\n⏳ Payment request cancelled by user")
            elif status_result.get('ResultCode') == '1037':
                print("\n⏳ Payment timeout - user didn't enter PIN")
            elif status_result.get('ResultCode') == '1':
                print("\n⏳ Payment still pending - user hasn't completed")
            else:
                print(f"\n⚠️  Payment status: {status_result.get('ResultDesc')}")
            
            # Show callback metadata if available
            if 'CallbackMetadata' in status_result:
                metadata = status_result['CallbackMetadata'].get('Item', [])
                if metadata:
                    print("\n💳 Payment Metadata:")
                    for item in metadata:
                        name = item.get('Name')
                        value = item.get('Value')
                        print(f"   {name}: {value}")
        
        print("\n" + "="*70)
        print("  TEST COMPLETED")
        print("="*70)
        print("\nWhat happens next:")
        print("1. If payment is completed, M-Pesa will send a callback")
        print("2. The callback URL is: {}/api/orders/payments/mpesa/stk-callback/".format(
            os.getenv('BASE_URL', 'https://errandserver.fagitone.com')
        ))
        print("3. Check your Django logs for callback data")
        print("4. Payment status will be updated in the database")
        print("="*70)
        
    else:
        print("\n❌ STK Push failed!")
        print(f"\n📋 Error Details:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        
        if 'response' in result:
            response = result['response']
            print(f"   Response Code: {response.get('errorCode')}")
            print(f"   Error Message: {response.get('errorMessage')}")
            print(f"\n   Full Response: {response}")
        
        print("\n💡 Common Issues:")
        print("   - Invalid phone number format (must be 254XXXXXXXXX)")
        print("   - Phone not registered in sandbox")
        print("   - Invalid credentials")
        print("   - Amount too low (minimum KSh 1)")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print(f"   Error type: {type(e).__name__}")
    
    import traceback
    print(f"\n📋 Full Traceback:")
    print(traceback.format_exc())
    
    print("\n💡 Troubleshooting:")
    print("   1. Check your M-Pesa credentials in .env")
    print("   2. Verify phone number format (254XXXXXXXXX)")
    print("   3. Ensure you're using sandbox test numbers")
    print("   4. Check internet connection")
    print("   5. Verify Safaricom API is accessible")

print("\n")