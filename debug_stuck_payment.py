#!/usr/bin/env python
"""
Debug Stuck Payment Issue
Analyzes why payment ID 21 is stuck in processing
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment
from django.utils import timezone
import requests
import json

def debug_stuck_payment():
    """Debug the stuck payment issue"""
    
    print("🔍 Debugging Stuck Payment Issue")
    print("=" * 50)
    
    # Get the specific payment
    try:
        payment = Payment.objects.get(id=21)
        print(f"📊 Payment Details:")
        print(f"   ID: {payment.id}")
        print(f"   Order: {payment.order.id}")
        print(f"   Amount: KSh {payment.amount}")
        print(f"   Status: {payment.status}")
        print(f"   Method: {payment.payment_method}")
        print(f"   Phone: {payment.phone_number}")
        print(f"   Transaction Ref: {payment.transaction_reference}")
        print(f"   IntaSend Checkout ID: {payment.intasend_checkout_id}")
        print(f"   IntaSend Invoice ID: {payment.intasend_invoice_id}")
        print(f"   Payment Date: {payment.payment_date}")
        
        # Check how long it's been stuck
        time_stuck = timezone.now() - payment.payment_date
        hours_stuck = time_stuck.total_seconds() / 3600
        print(f"   Time Stuck: {hours_stuck:.1f} hours")
        
    except Payment.DoesNotExist:
        print("❌ Payment ID 21 not found")
        return
    
    print(f"\n🔍 Issue Analysis:")
    print("-" * 20)
    
    # Issue 1: Missing Invoice ID
    if not payment.intasend_invoice_id:
        print("❌ CRITICAL: IntaSend Invoice ID is missing")
        print("   This means the STK Push didn't return proper invoice ID")
        print("   Webhook can't match this payment")
        print("   Solution: Check IntaSend API response format")
    else:
        print("✅ IntaSend Invoice ID present")
    
    # Issue 2: Checkout ID present but no Invoice ID
    if payment.intasend_checkout_id and not payment.intasend_invoice_id:
        print("⚠️  Checkout ID present but Invoice ID missing")
        print("   This suggests STK Push was initiated but response parsing failed")
        print("   Check the IntaSend API response handling")
    
    # Issue 3: Time stuck
    if hours_stuck > 2:
        print(f"⚠️  Payment stuck for {hours_stuck:.1f} hours (>2h threshold)")
        print("   This payment should be marked as failed or cancelled")
    
    print(f"\n🔧 Recommended Actions:")
    print("-" * 25)
    
    print("1. 🔗 Configure IntaSend Webhook:")
    print("   URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print("   Challenge: fagierrands_webhook_2025_secure")
    print("   Events: All Payment Collection Events")
    
    print("\n2. 🧪 Test Webhook Manually:")
    print("   Run the webhook test to verify it's working")
    
    print("\n3. 🔄 Fix Current Stuck Payment:")
    print("   Manually update this payment based on IntaSend dashboard status")
    
    print("\n4. 📊 Check IntaSend Dashboard:")
    print("   Login to IntaSend and check the actual status of this payment")
    
    # Test webhook endpoint
    print(f"\n🧪 Testing Webhook Endpoint:")
    print("-" * 30)
    
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    try:
        # Test with a sample webhook payload
        test_payload = {
            "invoice_id": "TEST_WEBHOOK_DEBUG",
            "state": "COMPLETE",
            "provider": "M-PESA",
            "charges": "16.80",
            "net_amount": "543.20",
            "currency": "KES",
            "value": "560.00",
            "account": "QGH7X8Y9Z0",
            "api_ref": "ISL_debug_test",
            "host": "https://payment.intasend.com",
            "failed_reason": None,
            "failed_code": None,
            "created_at": "2025-01-08T15:09:59Z",
            "updated_at": "2025-01-08T15:10:30Z",
            "challenge": "fagierrands_webhook_2025_secure"
        }
        
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Webhook endpoint is accessible and responding")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Webhook endpoint returned: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Webhook endpoint test failed: {str(e)}")
    
    # Suggest manual fix for current payment
    print(f"\n🔧 Manual Fix for Payment ID 21:")
    print("-" * 35)
    
    print("Since IntaSend dashboard shows 'failed', update the payment:")
    print(f"1. Set status to 'failed'")
    print(f"2. Add failure reason")
    print(f"3. Allow user to retry")
    
    return payment

def fix_stuck_payment(payment_id, new_status='failed', reason='Payment failed in IntaSend dashboard'):
    """Fix a stuck payment by updating its status"""
    
    try:
        payment = Payment.objects.get(id=payment_id)
        old_status = payment.status
        
        payment.status = new_status
        
        # Add failure reason if model supports it
        if hasattr(payment, 'failure_reason'):
            payment.failure_reason = reason
        
        payment.save()
        
        print(f"✅ Payment {payment_id} updated: {old_status} → {new_status}")
        return True
        
    except Payment.DoesNotExist:
        print(f"❌ Payment {payment_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error updating payment: {str(e)}")
        return False

if __name__ == '__main__':
    payment = debug_stuck_payment()
    
    print(f"\n💡 Next Steps:")
    print("-" * 15)
    print("1. Configure webhook in IntaSend dashboard")
    print("2. Test with new payment (KSh 5-10)")
    print("3. Fix current stuck payment:")
    print(f"   python -c \"from debug_stuck_payment import fix_stuck_payment; fix_stuck_payment(21)\"")
    print("4. Monitor future payments for similar issues")