#!/usr/bin/env python
"""
Simple webhook test script - fixed for Payment model fields
"""

import os
import sys
import django
import requests
from datetime import timedelta
from django.utils import timezone

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment

def test_webhook_simple():
    """Simple webhook test"""
    
    print("🧪 Simple Webhook Test")
    print("=" * 30)
    
    # 1. Test webhook endpoint
    print("1. Testing webhook endpoint...")
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    test_payload = {
        "event": "payment.completed",
        "data": {
            "invoice": {"id": "test-webhook-123"},
            "mpesa_receipt": "TEST123"
        }
    }
    
    try:
        response = requests.post(webhook_url, json=test_payload, timeout=10)
        if response.status_code == 200:
            print("   ✅ Webhook endpoint working")
        else:
            print(f"   ❌ Webhook returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Webhook test failed: {str(e)}")
    
    # 2. Check current payment status
    print("\n2. Current payment status:")
    
    total_payments = Payment.objects.count()
    print(f"   Total payments: {total_payments}")
    
    # Count by status
    statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
    for status in statuses:
        count = Payment.objects.filter(status=status).count()
        if count > 0:
            print(f"   {status}: {count}")
    
    # 3. Check for stuck payments
    print("\n3. Checking for stuck payments...")
    stuck_payments = Payment.objects.filter(
        status='processing',
        payment_date__lt=timezone.now() - timedelta(hours=1)
    )
    
    if stuck_payments.exists():
        print(f"   ⚠️  {stuck_payments.count()} payments stuck in processing")
        for payment in stuck_payments:
            hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"      Payment {payment.id}: {hours_stuck:.1f}h stuck")
    else:
        print("   ✅ No stuck payments found")
    
    # 4. Recent payment activity
    print("\n4. Recent payment activity (last 24h):")
    recent_payments = Payment.objects.filter(
        payment_date__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-payment_date')[:5]
    
    if recent_payments.exists():
        for payment in recent_payments:
            hours_ago = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"   Payment {payment.id}: {payment.status} ({hours_ago:.1f}h ago)")
    else:
        print("   No recent payments")
    
    # 5. Next steps
    print("\n5. Next steps to test webhook:")
    print("   a) Configure webhook in IntaSend dashboard:")
    print("      URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    print("   b) Enable events: payment.completed, payment.failed, payment.cancelled")
    print("   c) Send test webhook from dashboard")
    print("   d) Make a real test payment (KSh 10)")
    print("   e) Check if payment status updates automatically")

if __name__ == '__main__':
    try:
        test_webhook_simple()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()