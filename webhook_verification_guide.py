#!/usr/bin/env python
"""
Step-by-step guide to verify webhook configuration in IntaSend dashboard
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment

def main():
    print("🔍 IntaSend Webhook Verification Guide")
    print("=" * 50)
    
    print("\n📋 STEP-BY-STEP VERIFICATION PROCESS:")
    print()
    
    # Step 1: Dashboard Check
    print("1️⃣  CHECK INTASEND DASHBOARD CONFIGURATION")
    print("   a) Login to: https://payment.intasend.com")
    print("   b) Navigate to: Settings → Webhooks")
    print("   c) Verify webhook URL is listed:")
    print("      ✅ https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print("   d) Verify events are enabled:")
    print("      ✅ payment.completed")
    print("      ✅ payment.failed") 
    print("      ✅ payment.cancelled")
    print()
    
    # Step 2: Test Webhook Delivery
    print("2️⃣  TEST WEBHOOK DELIVERY FROM DASHBOARD")
    print("   a) In IntaSend dashboard → Webhooks")
    print("   b) Find your webhook URL")
    print("   c) Look for 'Test' or 'Send Test Event' button")
    print("   d) Send a test webhook")
    print("   e) Expected result: Should see 200 OK response")
    print()
    
    # Step 3: Check Delivery Logs
    print("3️⃣  CHECK WEBHOOK DELIVERY LOGS")
    print("   a) In IntaSend dashboard → Webhooks")
    print("   b) Look for 'Delivery Logs' or 'Event History'")
    print("   c) Check recent webhook attempts:")
    print("      ✅ Status: 200 (Success)")
    print("      ❌ Status: 404/500 (Failed)")
    print("   d) If failed, check the error message")
    print()
    
    # Step 4: Real Payment Test
    print("4️⃣  REAL PAYMENT TEST")
    print("   a) Create a small test order (KSh 10-50)")
    print("   b) Initiate M-Pesa payment")
    print("   c) Complete the payment on your phone")
    print("   d) Monitor payment status in admin panel")
    print("   e) Expected: Status changes from 'processing' → 'completed'")
    print()
    
    # Step 5: Server Log Check
    print("5️⃣  CHECK SERVER LOGS")
    print("   a) Look for these log messages:")
    print("      ✅ 'Received IntaSend webhook: event=payment.completed'")
    print("      ✅ 'Payment X status updated from processing to completed'")
    print("   b) If no logs found, webhook is not reaching server")
    print()
    
    # Current status check
    print("6️⃣  CURRENT SYSTEM STATUS CHECK")
    check_current_status()
    
    # Troubleshooting
    print("\n🔧 TROUBLESHOOTING COMMON ISSUES:")
    print()
    print("❌ ISSUE: Webhook returns 404 Not Found")
    print("   ✅ SOLUTION: Check webhook URL format")
    print("   ✅ CORRECT: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print("   ❌ WRONG: https://fagierrands-server.vercel.app/orders/payments/webhook/")
    print()
    
    print("❌ ISSUE: Webhook returns 500 Internal Server Error")
    print("   ✅ SOLUTION: Check server logs for Python errors")
    print("   ✅ SOLUTION: Verify payment exists with correct invoice_id")
    print()
    
    print("❌ ISSUE: No webhook delivery attempts in logs")
    print("   ✅ SOLUTION: Webhook URL not configured in dashboard")
    print("   ✅ SOLUTION: Events not enabled in dashboard")
    print()
    
    print("❌ ISSUE: Webhook delivered but payment status not updating")
    print("   ✅ SOLUTION: Check invoice_id matching")
    print("   ✅ SOLUTION: Check server logs for processing errors")
    print()
    
    # Quick verification commands
    print("\n⚡ QUICK VERIFICATION COMMANDS:")
    print()
    print("   Test webhook endpoint:")
    print("   → python test_webhook_endpoint.py")
    print()
    print("   Check current payment status:")
    print("   → python verify_payment_fix.py")
    print()
    print("   Monitor webhook integration:")
    print("   → python test_webhook_integration.py")
    print()
    
    # Success indicators
    print("\n✅ SUCCESS INDICATORS:")
    print("   1. Webhook URL listed in IntaSend dashboard")
    print("   2. Test webhook returns 200 OK")
    print("   3. Delivery logs show successful attempts")
    print("   4. Real payments automatically update status")
    print("   5. Server logs show webhook receipt messages")
    print("   6. No payments stuck in 'processing' status")

def check_current_status():
    """Check current payment status"""
    print("   📊 Current Payment Status:")
    
    # Check for stuck payments
    stuck_payments = Payment.objects.filter(
        status='processing',
        payment_date__lt=timezone.now() - timedelta(hours=1)
    )
    
    if stuck_payments.exists():
        print(f"   ⚠️  {stuck_payments.count()} payments stuck in processing")
        print("   → This indicates webhooks are NOT working")
    else:
        print("   ✅ No payments stuck in processing")
        print("   → This is good, but test with new payment to confirm")
    
    # Check recent payments
    recent_payments = Payment.objects.filter(
        payment_date__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-payment_date')[:5]
    
    if recent_payments.exists():
        print(f"   📋 Recent payments (last 24h):")
        for payment in recent_payments:
            hours_ago = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"      Payment {payment.id}: {payment.status} ({hours_ago:.1f}h ago)")
    else:
        print("   📋 No recent payments found")

if __name__ == '__main__':
    main()