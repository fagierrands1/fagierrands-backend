#!/usr/bin/env python
"""
Monitor webhook activity while testing with Postman
Run this script while sending Postman requests to see real-time webhook processing
"""

import os
import sys
import django
import time
from datetime import timedelta
from django.utils import timezone

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment

def monitor_postman_tests():
    """Monitor for webhook activity during Postman testing"""
    
    print("🔍 Postman Webhook Test Monitor")
    print("=" * 40)
    print("This monitor will show:")
    print("- Webhook requests received")
    print("- Payment status changes")
    print("- Server processing activity")
    print()
    print("💡 Instructions:")
    print("1. Keep this running")
    print("2. Send Postman requests to webhook endpoint")
    print("3. Watch for activity in this monitor")
    print()
    print("🎯 Webhook URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print()
    print("Press Ctrl+C to stop monitoring")
    print("=" * 40)
    
    # Get initial state
    initial_payment_count = Payment.objects.count()
    last_check = timezone.now()
    request_count = 0
    
    print(f"📊 Starting monitor at {last_check.strftime('%H:%M:%S')}")
    print(f"📊 Current payments in database: {initial_payment_count}")
    print()
    print("🚀 Ready for Postman tests! Send your webhook requests now...")
    print()
    
    try:
        while True:
            current_time = timezone.now()
            
            # Check for any new payments (shouldn't happen with test data)
            current_payment_count = Payment.objects.count()
            if current_payment_count != initial_payment_count:
                print(f"📈 Payment count changed: {initial_payment_count} → {current_payment_count}")
                initial_payment_count = current_payment_count
            
            # Show activity indicator every 10 seconds
            if int(time.time()) % 10 == 0:
                print(f"⏰ {current_time.strftime('%H:%M:%S')} | Monitoring... (Send Postman requests now)")
            
            # Check for recent payment activity (in case test data affects real payments)
            recent_activity = Payment.objects.filter(
                payment_date__gte=current_time - timedelta(minutes=1)
            ).exclude(status='pending')
            
            if recent_activity.exists():
                for payment in recent_activity:
                    print(f"🔄 PAYMENT ACTIVITY: Payment {payment.id} → {payment.status}")
                    print(f"   💡 This could indicate webhook processing!")
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Monitor stopped at {timezone.now().strftime('%H:%M:%S')}")
        
        print("\n📋 Postman Test Results Summary:")
        print("- If you saw webhook activity above: ✅ Webhook is working")
        print("- If no activity shown: Check Postman response codes")
        print("- Expected Postman response: 200 OK with {\"status\": \"success\"}")
        
        print(f"\n💡 Next Steps:")
        print("1. Verify all Postman tests returned 200 OK")
        print("2. Check server logs for webhook processing messages")
        print("3. Configure webhook URL in IntaSend dashboard")
        print("4. Test with real payment")

def show_webhook_test_instructions():
    """Show detailed Postman test instructions"""
    print("\n📋 Postman Test Instructions:")
    print("-" * 30)
    print("1. Open Postman")
    print("2. Create new POST request")
    print("3. URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print("4. Headers:")
    print("   - Content-Type: application/json")
    print("   - User-Agent: IntaSend-Webhook-Test")
    print("5. Body (raw JSON):")
    print("""
{
  "event": "payment.completed",
  "data": {
    "invoice": {
      "id": "test-postman-123"
    },
    "mpesa_receipt": "POSTMAN_TEST_123",
    "amount": 100.00,
    "currency": "KES"
  }
}
    """)
    print("6. Click Send")
    print("7. Expected Response: 200 OK with {\"status\": \"success\"}")

if __name__ == '__main__':
    try:
        show_webhook_test_instructions()
        monitor_postman_tests()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()