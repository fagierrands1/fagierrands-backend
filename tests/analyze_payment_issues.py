#!/usr/bin/env python
"""
Analyze payment issues and provide solutions
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment, Order

def analyze_payment_issues():
    """Analyze payment patterns and identify issues"""
    
    print("🔍 Payment Issue Analysis")
    print("=" * 50)
    
    # Get all payments
    payments = Payment.objects.all().order_by('-payment_date')
    total_payments = payments.count()
    
    if total_payments == 0:
        print("No payments found in database.")
        return
    
    # Status breakdown
    status_counts = {}
    for payment in payments:
        status = payment.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"📊 Payment Status Breakdown (Total: {total_payments})")
    print("-" * 40)
    for status, count in status_counts.items():
        percentage = (count / total_payments) * 100
        print(f"  {status:12}: {count:3} payments ({percentage:5.1f}%)")
    
    # Time analysis
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)
    
    recent_payments = payments.filter(payment_date__gte=last_24h)
    weekly_payments = payments.filter(payment_date__gte=last_week)
    
    print(f"\n📅 Time Analysis")
    print("-" * 20)
    print(f"  Last 24 hours: {recent_payments.count()} payments")
    print(f"  Last 7 days  : {weekly_payments.count()} payments")
    
    # Stuck payments analysis
    stuck_threshold = now - timedelta(hours=2)
    stuck_payments = payments.filter(
        status='processing',
        payment_date__lt=stuck_threshold
    )
    
    print(f"\n⚠️  Stuck Payments Analysis")
    print("-" * 30)
    print(f"  Stuck payments (>2h): {stuck_payments.count()}")
    
    if stuck_payments.exists():
        print(f"  Stuck payment details:")
        for payment in stuck_payments[:5]:  # Show first 5
            hours_stuck = (now - payment.payment_date).total_seconds() / 3600
            print(f"    ID {payment.id}: {hours_stuck:.1f}h stuck | Amount: KSh {payment.amount} | Method: {payment.payment_method}")
    
    # Success rate analysis
    completed_payments = payments.filter(status='completed').count()
    failed_payments = payments.filter(status='failed').count()
    cancelled_payments = payments.filter(status='cancelled').count()
    processing_payments = payments.filter(status='processing').count()
    pending_payments = payments.filter(status='pending').count()
    
    resolved_payments = completed_payments + failed_payments + cancelled_payments
    unresolved_payments = processing_payments + pending_payments
    
    if total_payments > 0:
        success_rate = (completed_payments / total_payments) * 100
        resolution_rate = (resolved_payments / total_payments) * 100
    else:
        success_rate = 0
        resolution_rate = 0
    
    print(f"\n📈 Success Metrics")
    print("-" * 20)
    print(f"  Success rate    : {success_rate:.1f}% ({completed_payments}/{total_payments})")
    print(f"  Resolution rate : {resolution_rate:.1f}% ({resolved_payments}/{total_payments})")
    print(f"  Unresolved      : {unresolved_payments} payments")
    
    # Payment method analysis
    method_counts = {}
    for payment in payments:
        method = payment.payment_method or 'unknown'
        method_counts[method] = method_counts.get(method, 0) + 1
    
    print(f"\n💳 Payment Method Breakdown")
    print("-" * 30)
    for method, count in method_counts.items():
        percentage = (count / total_payments) * 100
        print(f"  {method:10}: {count:3} payments ({percentage:5.1f}%)")
    
    # Recent activity
    print(f"\n🕒 Recent Payment Activity")
    print("-" * 30)
    recent_payments_list = payments[:10]  # Last 10 payments
    
    if recent_payments_list:
        for payment in recent_payments_list:
            time_ago = now - payment.payment_date
            hours_ago = time_ago.total_seconds() / 3600
            
            if hours_ago < 1:
                time_str = f"{int(time_ago.total_seconds() / 60)}m ago"
            elif hours_ago < 24:
                time_str = f"{hours_ago:.1f}h ago"
            else:
                days_ago = time_ago.days
                time_str = f"{days_ago}d ago"
            
            print(f"  ID {payment.id:2}: {payment.status:10} | KSh {payment.amount:6} | {payment.payment_method:6} | {time_str}")
    else:
        print("  No recent payments")
    
    # Issue diagnosis
    print(f"\n🔧 Issue Diagnosis & Solutions")
    print("=" * 40)
    
    if stuck_payments.count() > 0:
        print(f"❌ ISSUE: {stuck_payments.count()} payments stuck in processing")
        print(f"   CAUSE: No webhook configured in IntaSend dashboard")
        print(f"   SOLUTION: Configure webhook URL in IntaSend dashboard")
        print(f"   URL: https://fagierrands-server.vercel.app/api/orders/payments/webhook/")
    
    if success_rate < 50:
        print(f"❌ ISSUE: Low success rate ({success_rate:.1f}%)")
        print(f"   CAUSE: Payments not completing successfully")
        print(f"   SOLUTION: Check IntaSend integration and webhook setup")
    
    if resolution_rate < 80:
        print(f"⚠️  ISSUE: Low resolution rate ({resolution_rate:.1f}%)")
        print(f"   CAUSE: Too many unresolved payments")
        print(f"   SOLUTION: Implement automatic stuck payment handling")
    
    if unresolved_payments > 5:
        print(f"⚠️  ISSUE: {unresolved_payments} unresolved payments")
        print(f"   SOLUTION: Run stuck payment cleanup script")
    
    # Recommendations
    print(f"\n💡 Recommendations")
    print("-" * 20)
    print(f"1. 🔗 Configure IntaSend webhook (CRITICAL)")
    print(f"2. 🧪 Test webhook with Postman")
    print(f"3. 💰 Make test payment to verify end-to-end flow")
    print(f"4. 🔄 Set up automatic stuck payment cleanup")
    print(f"5. 📊 Monitor payment success rates")
    
    return {
        'total_payments': total_payments,
        'stuck_payments': stuck_payments.count(),
        'success_rate': success_rate,
        'resolution_rate': resolution_rate,
        'status_counts': status_counts
    }

if __name__ == '__main__':
    try:
        analyze_payment_issues()
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()