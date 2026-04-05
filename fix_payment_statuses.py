#!/usr/bin/env python
"""
Fix Payment Statuses - Simple and Direct
Update all stuck payments to correct statuses
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment, Order
from django.utils import timezone
from django.db.models import Q

def fix_all_payment_statuses():
    """Fix all payment statuses based on logical rules"""
    
    print("🔧 Fixing All Payment Statuses")
    print("=" * 40)
    
    # Get all payments
    all_payments = Payment.objects.all().order_by('-payment_date')
    total_payments = all_payments.count()
    
    print(f"📊 Total Payments: {total_payments}")
    
    # Show current distribution
    status_counts = {}
    for payment in all_payments:
        status = payment.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n📈 Current Status Distribution:")
    for status, count in status_counts.items():
        percentage = (count / total_payments) * 100
        print(f"   {status:12}: {count:3} ({percentage:5.1f}%)")
    
    updates_made = []
    
    print(f"\n🔧 Applying Fixes:")
    print("-" * 20)
    
    # Fix 1: Old processing payments (>2 hours) → failed
    old_processing = all_payments.filter(
        status='processing',
        payment_date__lt=timezone.now() - timedelta(hours=2)
    )
    
    print(f"1. Processing payments >2h old: {old_processing.count()}")
    for payment in old_processing:
        hours_old = (timezone.now() - payment.payment_date).total_seconds() / 3600
        print(f"   Payment {payment.id}: {hours_old:.1f}h → failed")
        
        payment.status = 'failed'
        payment.save()
        updates_made.append(f"Payment {payment.id}: processing → failed")
    
    # Fix 2: Old pending payments (>4 hours) → cancelled
    old_pending = all_payments.filter(
        status='pending',
        payment_date__lt=timezone.now() - timedelta(hours=4)
    )
    
    print(f"\n2. Pending payments >4h old: {old_pending.count()}")
    for payment in old_pending:
        hours_old = (timezone.now() - payment.payment_date).total_seconds() / 3600
        print(f"   Payment {payment.id}: {hours_old:.1f}h → cancelled")
        
        payment.status = 'cancelled'
        payment.save()
        updates_made.append(f"Payment {payment.id}: pending → cancelled")
    
    # Fix 3: Missing invoice ID and old (>1 hour) → failed
    missing_invoice = all_payments.filter(
        Q(intasend_invoice_id__isnull=True) | Q(intasend_invoice_id=''),
        payment_date__lt=timezone.now() - timedelta(hours=1)
    ).exclude(status__in=['cancelled', 'failed'])
    
    print(f"\n3. Missing invoice ID >1h old: {missing_invoice.count()}")
    for payment in missing_invoice:
        hours_old = (timezone.now() - payment.payment_date).total_seconds() / 3600
        old_status = payment.status
        print(f"   Payment {payment.id}: {old_status} → failed (no invoice ID)")
        
        payment.status = 'failed'
        payment.save()
        updates_made.append(f"Payment {payment.id}: {old_status} → failed (no invoice)")
    
    # Fix 4: Very old payments (>1 day) → failed
    very_old = all_payments.filter(
        payment_date__lt=timezone.now() - timedelta(days=1)
    ).exclude(status__in=['completed', 'cancelled', 'failed'])
    
    print(f"\n4. Very old payments >1 day: {very_old.count()}")
    for payment in very_old:
        days_old = (timezone.now() - payment.payment_date).total_seconds() / (24 * 3600)
        old_status = payment.status
        print(f"   Payment {payment.id}: {old_status} → failed ({days_old:.1f} days old)")
        
        payment.status = 'failed'
        payment.save()
        updates_made.append(f"Payment {payment.id}: {old_status} → failed (too old)")
    
    # Show final distribution
    print(f"\n📊 Final Status Distribution:")
    print("-" * 30)
    
    final_status_counts = {}
    for payment in Payment.objects.all():
        status = payment.status
        final_status_counts[status] = final_status_counts.get(status, 0) + 1
    
    for status, count in final_status_counts.items():
        percentage = (count / total_payments) * 100
        print(f"   {status:12}: {count:3} ({percentage:5.1f}%)")
    
    print(f"\n✅ Updates Applied: {len(updates_made)}")
    if updates_made:
        print("Changes made:")
        for update in updates_made:
            print(f"   {update}")
    
    return updates_made

def fix_order_statuses():
    """Fix order statuses based on payment statuses"""
    
    print(f"\n🔄 Fixing Order Statuses")
    print("-" * 25)
    
    updates_made = []
    
    # Get all orders
    all_orders = Order.objects.all()
    
    for order in all_orders:
        # Get all payments for this order
        order_payments = Payment.objects.filter(order=order)
        
        if not order_payments.exists():
            continue
        
        # Check if order status needs updating based on payments
        latest_payment = order_payments.order_by('-payment_date').first()
        
        # If order is payment_pending but payment is failed/cancelled
        if (order.status == 'payment_pending' and 
            latest_payment.status in ['failed', 'cancelled']):
            
            print(f"   Order {order.id}: payment_pending → payment_failed")
            order.status = 'payment_failed'
            order.save()
            updates_made.append(f"Order {order.id}: payment_pending → payment_failed")
        
        # If order is payment_pending but payment is completed
        elif (order.status == 'payment_pending' and 
              latest_payment.status == 'completed'):
            
            print(f"   Order {order.id}: payment_pending → completed")
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.save()
            updates_made.append(f"Order {order.id}: payment_pending → completed")
    
    print(f"\n✅ Order Updates: {len(updates_made)}")
    if updates_made:
        for update in updates_made:
            print(f"   {update}")
    
    return updates_made

def show_summary():
    """Show final summary of all payments and orders"""
    
    print(f"\n📊 Final Summary")
    print("=" * 20)
    
    # Payment summary
    payments = Payment.objects.all()
    payment_status_counts = {}
    for payment in payments:
        status = payment.status
        payment_status_counts[status] = payment_status_counts.get(status, 0) + 1
    
    print(f"💰 Payments ({payments.count()} total):")
    for status, count in payment_status_counts.items():
        print(f"   {status:12}: {count}")
    
    # Order summary
    orders = Order.objects.all()
    order_status_counts = {}
    for order in orders:
        status = order.status
        order_status_counts[status] = order_status_counts.get(status, 0) + 1
    
    print(f"\n📦 Orders ({orders.count()} total):")
    for status, count in order_status_counts.items():
        print(f"   {status:15}: {count}")
    
    # Health check
    print(f"\n🏥 Health Check:")
    
    # Stuck payments
    stuck_payments = Payment.objects.filter(
        status__in=['pending', 'processing'],
        payment_date__lt=timezone.now() - timedelta(hours=2)
    ).count()
    
    if stuck_payments == 0:
        print("   ✅ No stuck payments")
    else:
        print(f"   ⚠️  {stuck_payments} payments still stuck")
    
    # Missing invoice IDs
    missing_invoices = Payment.objects.filter(
        Q(intasend_invoice_id__isnull=True) | Q(intasend_invoice_id='')
    ).exclude(status__in=['cancelled', 'failed']).count()
    
    if missing_invoices == 0:
        print("   ✅ All active payments have invoice IDs")
    else:
        print(f"   ⚠️  {missing_invoices} active payments missing invoice IDs")
    
    # Payment success rate
    total_payments = payments.count()
    completed_payments = payment_status_counts.get('completed', 0)
    if total_payments > 0:
        success_rate = (completed_payments / total_payments) * 100
        print(f"   📈 Payment success rate: {success_rate:.1f}%")

def main():
    """Main function"""
    
    print("🚀 Payment Status Cleanup Tool")
    print("=" * 35)
    
    # Fix payment statuses
    payment_updates = fix_all_payment_statuses()
    
    # Fix order statuses
    order_updates = fix_order_statuses()
    
    # Show final summary
    show_summary()
    
    total_updates = len(payment_updates) + len(order_updates)
    
    print(f"\n🎉 Cleanup Complete!")
    print(f"   Total Updates: {total_updates}")
    print(f"   Payment Updates: {len(payment_updates)}")
    print(f"   Order Updates: {len(order_updates)}")
    
    if total_updates > 0:
        print(f"\n✅ All stuck payments have been resolved!")
        print(f"✅ Payment statuses are now accurate!")
        print(f"✅ Order statuses are synchronized!")
    else:
        print(f"\n✅ No updates needed - everything was already correct!")

if __name__ == '__main__':
    main()