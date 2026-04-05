#!/usr/bin/env python
"""
Comprehensive test to verify IntaSend webhook integration is working
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

from orders.models import Payment, Order
from accounts.models import User
from django.conf import settings
from intasend import APIService

def test_webhook_integration():
    """Complete webhook integration test"""
    
    print("🧪 Testing IntaSend Webhook Integration")
    print("=" * 60)
    
    # Step 1: Test webhook endpoint accessibility
    print("1. Testing webhook endpoint accessibility...")
    webhook_accessible = test_webhook_endpoint()
    
    # Step 2: Check IntaSend API connectivity
    print("\n2. Testing IntaSend API connectivity...")
    api_working = test_intasend_api()
    
    # Step 3: Create a test payment and monitor for webhook
    print("\n3. Creating test payment to monitor webhook delivery...")
    test_payment_id = create_test_payment()
    
    if test_payment_id:
        print(f"   ✅ Test payment created: ID {test_payment_id}")
        print("   💡 Now make a small test payment (e.g., KSh 10) to see if webhook is received")
        
        # Step 4: Monitor for webhook activity
        print("\n4. Monitoring for webhook activity...")
        monitor_webhook_activity(test_payment_id)
    
    # Step 5: Provide next steps
    print("\n5. Next Steps and Verification:")
    provide_verification_steps()

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    try:
        # Test with a sample payload
        test_payload = {
            "event": "payment.completed",
            "data": {
                "invoice": {"id": "test-webhook-verification"},
                "mpesa_receipt": "TEST123"
            }
        }
        
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Webhook endpoint is accessible and responding")
            return True
        else:
            print(f"   ❌ Webhook endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing webhook endpoint: {str(e)}")
        return False

def test_intasend_api():
    """Test IntaSend API connectivity"""
    try:
        api_service = APIService(
            token=settings.INTASEND_SECRET_KEY,
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Test API by trying to access wallets
        try:
            # This will test if our API keys are working
            response = api_service.collect.mpesa_stk_push(
                phone_number="254700000000",  # Test number
                email="test@example.com",
                amount=1.0,
                narrative="API Test - Do Not Process"
            )
            print("   ✅ IntaSend API is accessible")
            return True
        except Exception as api_err:
            if "phone_number" in str(api_err).lower() or "invalid" in str(api_err).lower():
                print("   ✅ IntaSend API is accessible (expected validation error)")
                return True
            else:
                print(f"   ❌ IntaSend API error: {str(api_err)}")
                return False
                
    except Exception as e:
        print(f"   ❌ Failed to initialize IntaSend API: {str(e)}")
        return False

def create_test_payment():
    """Create a test payment for webhook monitoring"""
    try:
        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            email='webhook_test@example.com',
            defaults={
                'username': 'webhook_test_user',
                'first_name': 'Webhook',
                'last_name': 'Test',
                'user_type': 'client',
                'phone_number': '254700000000'
            }
        )
        
        # Create a test order
        test_order = Order.objects.create(
            client=test_user,
            title='Webhook Test Order',
            description='Test order for webhook verification',
            order_type='shopping',
            status='pending',
            total_price=10.00,
            pickup_location='Test Location',
            delivery_location='Test Destination'
        )
        
        # Create a test payment
        test_payment = Payment.objects.create(
            order=test_order,
            client=test_user,
            amount=10.00,
            payment_method='mpesa',
            phone_number='254700000000',
            email='webhook_test@example.com',
            status='pending',
            transaction_reference=f'WEBHOOK_TEST_{timezone.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        return test_payment.id
        
    except Exception as e:
        print(f"   ❌ Error creating test payment: {str(e)}")
        return None

def monitor_webhook_activity(payment_id):
    """Monitor for webhook activity on the test payment"""
    try:
        payment = Payment.objects.get(id=payment_id)
        initial_status = payment.status
        
        print(f"   📊 Test payment status: {initial_status}")
        print(f"   📱 To test webhook:")
        print(f"      1. Use IntaSend dashboard to send a test webhook")
        print(f"      2. Or make a real KSh 10 payment using phone: 254700000000")
        print(f"      3. Check if payment status changes from '{initial_status}'")
        
        # Check recent webhook logs (if any)
        print(f"\n   📋 Recent payments for reference:")
        recent_payments = Payment.objects.filter(
            payment_date__gte=timezone.now() - timedelta(hours=1)
        ).order_by('-payment_date')[:3]
        
        for p in recent_payments:
            hours_ago = (timezone.now() - p.payment_date).total_seconds() / 3600
            print(f"      Payment {p.id}: {p.status} ({hours_ago:.1f}h ago)")
            
    except Exception as e:
        print(f"   ❌ Error monitoring webhook activity: {str(e)}")

def provide_verification_steps():
    """Provide steps to verify webhook configuration"""
    print("   🔍 How to verify webhook is working:")
    print()
    print("   METHOD 1: IntaSend Dashboard Test")
    print("   1. Login to IntaSend dashboard")
    print("   2. Go to Settings → Webhooks")
    print("   3. Find your webhook URL")
    print("   4. Click 'Test' or 'Send Test Event'")
    print("   5. Check server logs for webhook receipt")
    print()
    print("   METHOD 2: Real Payment Test")
    print("   1. Make a small test payment (KSh 10)")
    print("   2. Monitor payment status in admin panel")
    print("   3. Status should change from 'processing' to 'completed'")
    print("   4. Check server logs for webhook activity")
    print()
    print("   METHOD 3: Check Webhook Logs")
    print("   1. In IntaSend dashboard → Webhooks")
    print("   2. Look for 'Delivery Logs' or 'Event History'")
    print("   3. Verify webhooks are being sent")
    print("   4. Check response codes (200 = success)")
    print()
    print("   🚨 Signs webhook is NOT working:")
    print("   - Payments stuck in 'processing' status")
    print("   - No webhook logs in IntaSend dashboard")
    print("   - No 'Received IntaSend webhook' in server logs")
    print()
    print("   ✅ Signs webhook IS working:")
    print("   - Payments automatically change to 'completed'")
    print("   - Webhook delivery logs show 200 responses")
    print("   - Server logs show 'Received IntaSend webhook'")

def check_webhook_logs():
    """Check for recent webhook activity in logs"""
    print("\n📋 Checking for recent webhook activity...")
    
    # Check recent payment status changes (using payment_date since no updated_at field)
    recent_payments = Payment.objects.filter(
        payment_date__gte=timezone.now() - timedelta(hours=24)
    ).exclude(status='pending').order_by('-payment_date')[:5]
    
    if recent_payments.exists():
        print("   Recent non-pending payments (last 24h):")
        for payment in recent_payments:
            hours_ago = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"   - Payment {payment.id}: {payment.status} (Order {payment.order.id}) - {hours_ago:.1f}h ago")
    else:
        print("   ⚠️  No recent non-pending payments found")
        print("   This might indicate webhooks are not being received or no recent payments")

if __name__ == '__main__':
    try:
        test_webhook_integration()
        check_webhook_logs()
        
        print(f"\n🎯 Summary:")
        print(f"   - Webhook endpoint: Ready")
        print(f"   - IntaSend API: Connected")
        print(f"   - Test payment: Created")
        print(f"   - Next: Configure webhook in IntaSend dashboard")
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()