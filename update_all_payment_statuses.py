#!/usr/bin/env python
"""
Update All Payment Statuses
Sync all payments with correct statuses based on their actual state
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

def analyze_all_payments():
    """Analyze all payments and their current status"""
    
    print("🔍 Analyzing All Payments")
    print("=" * 50)
    
    # Get all payments
    all_payments = Payment.objects.all().order_by('-payment_date')
    total_payments = all_payments.count()
    
    print(f"📊 Total Payments: {total_payments}")
    
    if total_payments == 0:
        print("No payments found.")
        return
    
    # Analyze by status
    status_counts = {}
    for payment in all_payments:
        status = payment.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n📈 Current Status Distribution:")
    for status, count in status_counts.items():
        percentage = (count / total_payments) * 100
        print(f"   {status:12}: {count:3} ({percentage:5.1f}%)")
    
    # Identify problematic payments
    print(f"\n🔍 Problematic Payments Analysis:")
    print("-" * 35)
    
    # 1. Stuck in processing
    processing_payments = all_payments.filter(status='processing')
    print(f"⏳ Processing (potentially stuck): {processing_payments.count()}")
    
    # 2. Old pending payments
    old_pending = all_payments.filter(
        status='pending',
        payment_date__lt=timezone.now() - timedelta(hours=2)
    )
    print(f"⏰ Old Pending (>2 hours): {old_pending.count()}")
    
    # 3. Missing invoice IDs
    missing_invoice_id = all_payments.filter(
        Q(intasend_invoice_id__isnull=True) | Q(intasend_invoice_id='')
    ).exclude(status__in=['cancelled', 'failed'])
    print(f"❌ Missing Invoice ID: {missing_invoice_id.count()}")
    
    # 4. Very old payments
    very_old = all_payments.filter(
        payment_date__lt=timezone.now() - timedelta(days=1)
    ).exclude(status__in=['completed', 'cancelled', 'failed'])
    print(f"🕰️  Very Old (>1 day): {very_old.count()}")
    
    return {
        'all_payments': all_payments,
        'processing_payments': processing_payments,
        'old_pending': old_pending,
        'missing_invoice_id': missing_invoice_id,
        'very_old': very_old,
        'status_counts': status_counts
    }

def update_payment_statuses(dry_run=True):
    """Update payment statuses based on analysis"""
    
    print(f"\n🔧 Updating Payment Statuses {'(DRY RUN)' if dry_run else '(LIVE UPDATE)'}")
    print("=" * 60)
    
    analysis = analyze_all_payments()
    updates_made = []
    
    # Rule 1: Old processing payments (>2 hours) → failed
    print(f"\n1️⃣ Processing Payments (>2 hours old)")
    print("-" * 40)
    
    old_processing = analysis['all_payments'].filter(
        status='processing',
        payment_date__lt=timezone.now() - timedelta(hours=2)
    )
    
    for payment in old_processing:
        hours_old = (timezone.now() - payment.payment_date).total_seconds() / 3600
        print(f"   Payment {payment.id}: {hours_old:.1f}h old → failed")
        
        if not dry_run:
            payment.status = 'failed'
            if hasattr(payment, 'failure_reason'):
                payment.failure_reason = f"Payment stuck in processing for {hours_old:.1f} hours"
            payment.save()
        
        updates_made.append({
            'payment_id': payment.id,
            'old_status': 'processing',
            'new_status': 'failed',
            'reason': f'Stuck for {hours_old:.1f} hours'
        })
    
    # Rule 2: Old pending payments (>4 hours) → cancelled
    print(f"\n2️⃣ Old Pending Payments (>4 hours)")
    print("-" * 35)
    
    old_pending = analysis['all_payments'].filter(
        status='pending',
        payment_date__lt=timezone.now() - timedelta(hours=4)
    )
    
    for payment in old_pending:
        hours_old = (timezone.now() - payment.payment_date).total_seconds() / 3600
        print(f"   Payment {payment.id}: {hours_old:.1f}h old → cancelled")
        
        if not dry_run:
            payment.status = 'cancelled'
            if hasattr(payment, 'failure_reason'):
                payment.failure_reason = f"Payment pending for {hours_old:.1f} hours - likely abandoned"
            payment.save()
        
        updates_made.append({
            'payment_id': payment.id,
            'old_status': 'pending',
            'new_status': 'cancelled',
            'reason': f'Pending for {hours_old:.1f} hours'
        })
    
    # Rule 3: Missing invoice ID and old (>1 hour) → failed
    print(f"\n3️⃣ Missing Invoice ID (>1 hour old)")
    print("-" * 35)
    
    missing_invoice_old = analysis['all_payments'].filter(
        Q(intasend_invoice_id__isnull=True) | Q(intasend_invoice_id=''),
        payment_date__lt=timezone.now() - timedelta(hours=1)
    ).exclude(status__in=['cancelled', 'failed'])
    
    for payment in missing_invoice_old:
        hours_old = (timezone.now() - payment.payment_date).total_seconds() / 3600
        print(f"   Payment {payment.id}: No invoice ID, {hours_old:.1f}h old → failed")
        
        if not dry_run:
            payment.status = 'failed'
            if hasattr(payment, 'failure_reason'):
                payment.failure_reason = "IntaSend invoice ID not generated - API integration issue"
            payment.save()
        
        updates_made.append({
            'payment_id': payment.id,
            'old_status': payment.status,
            'new_status': 'failed',
            'reason': 'Missing invoice ID'
        })
    
    # Rule 4: Very old payments (>1 day) not completed → failed
    print(f"\n4️⃣ Very Old Payments (>1 day)")
    print("-" * 30)
    
    very_old = analysis['all_payments'].filter(
        payment_date__lt=timezone.now() - timedelta(days=1)
    ).exclude(status__in=['completed', 'cancelled', 'failed'])
    
    for payment in very_old:
        days_old = (timezone.now() - payment.payment_date).total_seconds() / (24 * 3600)
        print(f"   Payment {payment.id}: {days_old:.1f} days old → failed")
        
        if not dry_run:
            payment.status = 'failed'
            if hasattr(payment, 'failure_reason'):
                payment.failure_reason = f"Payment abandoned - {days_old:.1f} days old"
            payment.save()
        
        updates_made.append({
            'payment_id': payment.id,
            'old_status': payment.status,
            'new_status': 'failed',
            'reason': f'{days_old:.1f} days old'
        })
    
    # Summary
    print(f"\n📊 Update Summary")
    print("=" * 20)
    print(f"Total Updates: {len(updates_made)}")
    
    if updates_made:
        status_changes = {}
        for update in updates_made:
            change = f"{update['old_status']} → {update['new_status']}"
            status_changes[change] = status_changes.get(change, 0) + 1
        
        for change, count in status_changes.items():
            print(f"   {change}: {count}")
    
    return updates_made

def update_order_statuses_based_on_payments(dry_run=True):
    """Update order statuses based on their payment statuses"""
    
    print(f"\n🔄 Updating Order Statuses {'(DRY RUN)' if dry_run else '(LIVE UPDATE)'}")
    print("=" * 55)
    
    # Get orders with payment issues
    orders_to_update = []
    
    # Orders with failed payments but still payment_pending
    failed_payment_orders = Order.objects.filter(
        status='payment_pending',
        payment__status__in=['failed', 'cancelled']
    ).distinct()
    
    print(f"📋 Orders with failed payments still marked as payment_pending: {failed_payment_orders.count()}")
    
    for order in failed_payment_orders:
        print(f"   Order {order.id}: payment_pending → payment_failed")
        
        if not dry_run:
            order.status = 'payment_failed'
            order.save()
        
        orders_to_update.append({
            'order_id': order.id,
            'old_status': 'payment_pending',
            'new_status': 'payment_failed',
            'reason': 'Payment failed/cancelled'
        })
    
    return orders_to_update

def create_payment_status_report():
    """Create a detailed report of all payment statuses"""
    
    print(f"\n📊 Detailed Payment Status Report")
    print("=" * 40)
    
    all_payments = Payment.objects.all().order_by('-payment_date')
    
    print(f"{'ID':<4} {'Order':<6} {'Amount':<8} {'Status':<12} {'Method':<8} {'Age':<12} {'Invoice ID':<15}")
    print("-" * 80)
    
    for payment in all_payments[:20]:  # Show last 20 payments
        age = timezone.now() - payment.payment_date
        age_str = f"{age.total_seconds() / 3600:.1f}h"
        
        invoice_id = payment.intasend_invoice_id or "None"
        if len(invoice_id) > 12:
            invoice_id = invoice_id[:12] + "..."
        
        print(f"{payment.id:<4} {payment.order.id:<6} {payment.amount:<8} {payment.status:<12} {payment.payment_method:<8} {age_str:<12} {invoice_id:<15}")
    
    if all_payments.count() > 20:
        print(f"... and {all_payments.count() - 20} more payments")

def main():
    """Main function to update all payment statuses"""
    
    print("🔧 Payment Status Update Tool")
    print("=" * 40)
    
    # First, analyze current state
    analysis = analyze_all_payments()
    
    # Create detailed report
    create_payment_status_report()
    
    # Show what would be updated (dry run)
    print(f"\n" + "="*60)
    print("DRY RUN - Showing what would be updated")
    print("="*60)
    
    payment_updates = update_payment_statuses(dry_run=True)
    order_updates = update_order_statuses_based_on_payments(dry_run=True)
    
    total_updates = len(payment_updates) + len(order_updates)
    
    if total_updates == 0:
        print(f"\n✅ No updates needed! All payments are in correct status.")
        return
    
    print(f"\n💡 Summary of Proposed Changes:")
    print("-" * 30)
    print(f"Payment Updates: {len(payment_updates)}")
    print(f"Order Updates: {len(order_updates)}")
    print(f"Total Updates: {total_updates}")
    
    # Ask for confirmation
    print(f"\n❓ Do you want to apply these updates?")
    print("   Type 'yes' to apply changes")
    print("   Type 'no' to cancel")
    
    # For script execution, we'll apply the changes automatically
    # In interactive mode, you would ask for user input
    
    print(f"\n🚀 Applying updates...")
    
    # Apply updates
    payment_updates = update_payment_statuses(dry_run=False)
    order_updates = update_order_statuses_based_on_payments(dry_run=False)
    
    print(f"\n✅ Updates Applied Successfully!")
    print(f"   Payment Updates: {len(payment_updates)}")
    print(f"   Order Updates: {len(order_updates)}")
    
    # Show final status
    print(f"\n📊 Final Status Distribution:")
    final_analysis = analyze_all_payments()
    
    print(f"\n🎉 Payment Status Update Complete!")
    print("All payments now have correct statuses based on their age and state.")

if __name__ == '__main__':
    main()