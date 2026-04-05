#!/usr/bin/env python
"""
Diagnostic script to identify why IntaSend webhooks are not updating payment statuses
"""

import os
import sys
import django
import requests
import json
from datetime import timedelta
from django.utils import timezone

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment
from django.conf import settings
from intasend import APIService

def main():
    print("🔍 Diagnosing IntaSend Webhook Issues...")
    print("=" * 60)
    
    # 1. Check IntaSend Configuration
    print("1. Checking IntaSend Configuration:")
    print(f"   Publishable Key: {settings.INTASEND_PUBLISHABLE_KEY[:20]}...")
    print(f"   Secret Key: {settings.INTASEND_SECRET_KEY[:20]}...")
    print(f"   Test Mode: {settings.INTASEND_TEST_MODE}")
    
    # 2. Check webhook URL accessibility
    print("\n2. Checking Webhook URL Accessibility:")
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    print(f"   Webhook URL: {webhook_url}")
    
    try:
        # Test if webhook endpoint is accessible
        response = requests.get(webhook_url.replace('/webhook/', '/'))
        print(f"   Base URL Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing base URL: {str(e)}")
    
    # 3. Check recent processing payments
    print("\n3. Checking Recent Processing Payments:")
    processing_payments = Payment.objects.filter(status='processing').order_by('-payment_date')[:5]
    
    if not processing_payments.exists():
        print("   ✅ No payments currently in processing status")
    else:
        print(f"   ⚠️  Found {processing_payments.count()} payments in processing status:")
        for payment in processing_payments:
            hours_processing = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"     Payment {payment.id}: {hours_processing:.1f}h, Invoice: {payment.intasend_invoice_id}")
    
    # 4. Test IntaSend API connectivity
    print("\n4. Testing IntaSend API Connectivity:")
    try:
        api_service = APIService(
            token=settings.INTASEND_SECRET_KEY,
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Try to get wallet balance (this tests API connectivity)
        try:
            wallets = api_service.wallets.list()
            print("   ✅ IntaSend API connection successful")
            print(f"   Wallets found: {len(wallets) if isinstance(wallets, list) else 'N/A'}")
        except Exception as api_err:
            print(f"   ❌ IntaSend API error: {str(api_err)}")
            
    except Exception as e:
        print(f"   ❌ Failed to initialize IntaSend API: {str(e)}")
    
    # 5. Check webhook configuration in IntaSend
    print("\n5. Checking IntaSend Webhook Configuration:")
    try:
        api_service = APIService(
            token=settings.INTASEND_SECRET_KEY,
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Note: IntaSend doesn't have a direct API to list webhooks
        # But we can check if webhooks are configured by looking at recent payments
        print("   💡 IntaSend webhook configuration must be done via dashboard")
        print("   Expected webhook URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
        
    except Exception as e:
        print(f"   ❌ Error checking webhook config: {str(e)}")
    
    # 6. Simulate webhook payload to test endpoint
    print("\n6. Testing Webhook Endpoint:")
    test_webhook_payload()
    
    # 7. Provide recommendations
    print("\n7. Recommendations:")
    provide_recommendations()

def test_webhook_payload():
    """Test the webhook endpoint with a sample payload"""
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    # Sample webhook payload for payment completion
    test_payload = {
        "event": "payment.completed",
        "data": {
            "invoice": {
                "id": "test-invoice-id"
            },
            "mpesa_receipt": "TEST123456"
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"   Webhook test response: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Webhook endpoint is accessible and responding")
        else:
            print(f"   ⚠️  Webhook returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Error testing webhook: {str(e)}")

def provide_recommendations():
    """Provide recommendations based on findings"""
    print("   Based on the diagnosis, here are the likely issues and solutions:")
    print()
    print("   🔧 MOST LIKELY ISSUES:")
    print("   1. Webhook URL not configured in IntaSend dashboard")
    print("   2. Webhook URL configured incorrectly")
    print("   3. IntaSend webhook events not enabled")
    print("   4. Network/firewall blocking webhook calls")
    print()
    print("   ✅ SOLUTIONS:")
    print("   1. Login to IntaSend dashboard (https://sandbox.intasend.com or https://payment.intasend.com)")
    print("   2. Go to Settings > Webhooks")
    print("   3. Add webhook URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print("   4. Enable these events:")
    print("      - payment.completed")
    print("      - payment.failed")
    print("      - payment.cancelled")
    print("   5. Test webhook delivery from IntaSend dashboard")
    print()
    print("   🔍 IMMEDIATE ACTIONS:")
    print("   1. Check IntaSend dashboard webhook configuration")
    print("   2. Test webhook delivery manually")
    print("   3. Monitor webhook logs in IntaSend dashboard")
    print("   4. Run the automatic payment fix script for current stuck payments")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnosis cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during diagnosis: {str(e)}")
        import traceback
        traceback.print_exc()