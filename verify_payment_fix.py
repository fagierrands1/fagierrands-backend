#!/usr/bin/env python
"""
Verify that the payment fix worked correctly
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
from django.db import models

def main():
    print("🔍 Verifying payment fix...")
    print("=" * 50)
    
    # Check for any remaining stuck payments
    cutoff_time = timezone.now() - timedelta(hours=1)
    stuck_payments = Payment.objects.filter(
        status='processing',
        payment_date__lt=cutoff_time
    )
    
    if stuck_payments.exists():
        print(f"⚠️  Still found {stuck_payments.count()} stuck payments!")
        for payment in stuck_payments:
            hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
            print(f"  Payment {payment.id}: {hours_stuck:.1f}h stuck")
    else:
        print("✅ No stuck payments found!")
    
    # Show current payment status summary
    print("\n📊 Current payment status summary:")
    print("-" * 50)
    
    status_summary = Payment.objects.values('status').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount')
    ).order_by('status')
    
    total_payments = 0
    total_amount = 0
    
    for status_data in status_summary:
        status = status_data['status']
        count = status_data['count']
        amount = status_data['total_amount'] or 0
        total_payments += count
        total_amount += amount
        print(f"  {status:12s}: {count:4d} payments | KSh {amount:10,.2f}")
    
    print("-" * 50)
    print(f"  {'TOTAL':12s}: {total_payments:4d} payments | KSh {total_amount:10,.2f}")
    
    # Show recent payments
    print(f"\n📅 Recent payments (last 5):")
    recent_payments = Payment.objects.all().order_by('-payment_date')[:5]
    
    for payment in recent_payments:
        hours_ago = (timezone.now() - payment.payment_date).total_seconds() / 3600
        print(f"  ID: {payment.id:4d} | {payment.status:10s} | "
              f"{payment.payment_method:6s} | KSh {payment.amount:8.2f} | "
              f"{hours_ago:5.1f}h ago")
    
    print(f"\n✨ Verification completed!")

if __name__ == '__main__':
    main()