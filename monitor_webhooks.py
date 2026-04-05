#!/usr/bin/env python
"""
Real-time webhook monitoring script
Run this while testing webhook configuration to see if webhooks are being received
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

def monitor_webhooks():
    """Monitor for webhook activity in real-time"""
    
    print("🔍 Real-time Webhook Monitor")
    print("=" * 40)
    print("This script will monitor for:")
    print("- New payments created")
    print("- Payment status changes")
    print("- Webhook activity indicators")
    print()
    print("💡 Keep this running while you:")
    print("1. Configure webhook in IntaSend dashboard")
    print("2. Send test webhook from dashboard")
    print("3. Make a real test payment")
    print()
    print("Press Ctrl+C to stop monitoring")
    print("=" * 40)
    
    # Get initial state
    last_payment_id = Payment.objects.order_by('-id').first().id if Payment.objects.exists() else 0
    last_check_time = timezone.now()
    
    print(f"📊 Starting monitor at {last_check_time.strftime('%H:%M:%S')}")
    print(f"📊 Last payment ID: {last_payment_id}")
    print()
    
    try:
        while True:
            current_time = timezone.now()
            
            # Check for new payments
            new_payments = Payment.objects.filter(id__gt=last_payment_id).order_by('id')
            
            for payment in new_payments:
                print(f"🆕 NEW PAYMENT: ID {payment.id} | Status: {payment.status} | Amount: KSh {payment.amount}")
                last_payment_id = payment.id
            
            # Check for status changes in recent payments
            # Note: Payment model doesn't have updated_at, so we'll check for recent non-pending payments
            recent_status_changes = Payment.objects.filter(
                payment_date__gte=last_check_time - timedelta(minutes=1)
            ).exclude(
                status='pending'  # Focus on payments that have changed from pending
            ).order_by('-payment_date')
            
            for payment in recent_status_changes:
                print(f"🔄 STATUS CHANGE: Payment {payment.id} → {payment.status} | Order: {payment.order.id}")
                print(f"   💡 This indicates webhook was received and processed!")
            
            # Check for processing payments that might be stuck
            processing_payments = Payment.objects.filter(
                status='processing',
                payment_date__lt=timezone.now() - timedelta(minutes=5)
            )
            
            if processing_payments.exists():
                for payment in processing_payments:
                    minutes_stuck = (timezone.now() - payment.payment_date).total_seconds() / 60
                    if minutes_stuck > 5:  # Only show if stuck for more than 5 minutes
                        print(f"⏳ STUCK PAYMENT: ID {payment.id} | Processing for {minutes_stuck:.1f} minutes")
            
            last_check_time = current_time
            
            # Show current time every 30 seconds
            if int(time.time()) % 30 == 0:
                print(f"⏰ Monitoring... {current_time.strftime('%H:%M:%S')}")
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Monitoring stopped at {timezone.now().strftime('%H:%M:%S')}")
        
        # Show final summary
        print("\n📋 Final Summary:")
        total_payments = Payment.objects.count()
        processing_count = Payment.objects.filter(status='processing').count()
        completed_count = Payment.objects.filter(status='completed').count()
        
        print(f"   Total payments: {total_payments}")
        print(f"   Processing: {processing_count}")
        print(f"   Completed: {completed_count}")
        
        if processing_count > 0:
            print(f"\n⚠️  {processing_count} payments still in processing status")
            print("   This might indicate webhooks are not working yet")
        else:
            print(f"\n✅ No payments stuck in processing status")

def show_recent_activity():
    """Show recent payment activity"""
    print("\n📋 Recent Payment Activity (last 2 hours):")
    print("-" * 50)
    
    recent_payments = Payment.objects.filter(
        payment_date__gte=timezone.now() - timedelta(hours=2)
    ).order_by('-payment_date')[:10]
    
    if recent_payments.exists():
        for payment in recent_payments:
            hours_ago = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"   Payment {payment.id:3d} | {payment.status:10s} | "
                  f"KSh {payment.amount:8.2f} | {hours_ago:4.1f}h ago")
    else:
        print("   No recent payment activity")

if __name__ == '__main__':
    try:
        show_recent_activity()
        monitor_webhooks()
    except Exception as e:
        print(f"\n❌ Error during monitoring: {str(e)}")
        import traceback
        traceback.print_exc()