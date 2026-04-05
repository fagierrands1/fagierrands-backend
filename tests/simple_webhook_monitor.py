#!/usr/bin/env python
"""
Simple real-time webhook monitor - fixed for Payment model fields
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

def monitor_payments():
    """Monitor payments for webhook activity"""
    
    print("🔍 Simple Webhook Monitor")
    print("=" * 30)
    print("Monitoring for:")
    print("- New payments")
    print("- Status changes")
    print("- Stuck payments")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Get initial state
    last_payment_count = Payment.objects.count()
    last_check = timezone.now()
    
    print(f"📊 Starting monitor at {last_check.strftime('%H:%M:%S')}")
    print(f"📊 Current payment count: {last_payment_count}")
    print()
    
    try:
        while True:
            current_time = timezone.now()
            
            # Check for new payments
            current_payment_count = Payment.objects.count()
            if current_payment_count > last_payment_count:
                new_count = current_payment_count - last_payment_count
                print(f"🆕 {new_count} NEW PAYMENT(S) CREATED!")
                
                # Show the new payments
                new_payments = Payment.objects.order_by('-id')[:new_count]
                for payment in new_payments:
                    print(f"   Payment {payment.id}: {payment.status} | KSh {payment.amount}")
                
                last_payment_count = current_payment_count
            
            # Check for non-pending payments (indicates webhook activity)
            non_pending_payments = Payment.objects.exclude(status='pending').order_by('-payment_date')[:3]
            
            for payment in non_pending_payments:
                hours_ago = (current_time - payment.payment_date).total_seconds() / 3600
                if hours_ago < 0.1:  # Less than 6 minutes ago
                    print(f"🔄 RECENT STATUS CHANGE: Payment {payment.id} → {payment.status}")
                    print(f"   💡 This indicates webhook activity!")
            
            # Check for stuck payments
            stuck_payments = Payment.objects.filter(
                status='processing',
                payment_date__lt=current_time - timedelta(minutes=5)
            )
            
            for payment in stuck_payments:
                minutes_stuck = (current_time - payment.payment_date).total_seconds() / 60
                if minutes_stuck > 5 and int(minutes_stuck) % 5 == 0:  # Show every 5 minutes
                    print(f"⏳ Payment {payment.id} stuck in processing for {minutes_stuck:.0f} minutes")
            
            # Show status every 30 seconds
            if int(time.time()) % 30 == 0:
                pending_count = Payment.objects.filter(status='pending').count()
                processing_count = Payment.objects.filter(status='processing').count()
                completed_count = Payment.objects.filter(status='completed').count()
                
                print(f"⏰ {current_time.strftime('%H:%M:%S')} | "
                      f"Pending: {pending_count} | Processing: {processing_count} | Completed: {completed_count}")
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Monitor stopped at {timezone.now().strftime('%H:%M:%S')}")
        
        # Final summary
        final_counts = {
            'total': Payment.objects.count(),
            'pending': Payment.objects.filter(status='pending').count(),
            'processing': Payment.objects.filter(status='processing').count(),
            'completed': Payment.objects.filter(status='completed').count(),
            'failed': Payment.objects.filter(status='failed').count(),
            'cancelled': Payment.objects.filter(status='cancelled').count(),
        }
        
        print("\n📋 Final Status Summary:")
        for status, count in final_counts.items():
            if count > 0:
                print(f"   {status}: {count}")

if __name__ == '__main__':
    try:
        monitor_payments()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()