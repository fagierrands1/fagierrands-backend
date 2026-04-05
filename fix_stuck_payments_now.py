#!/usr/bin/env python
"""
Immediate fix for stuck payments in the admin panel.
This script will identify and fix payments that have been stuck in 'processing' status.
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
    print("🔍 Checking for stuck payments...")
    print("=" * 60)
    
    # Find payments stuck in processing for more than 1 hour (very conservative)
    cutoff_time = timezone.now() - timedelta(hours=1)
    
    stuck_payments = Payment.objects.filter(
        status='processing',
        payment_date__lt=cutoff_time
    ).order_by('payment_date')
    
    if not stuck_payments.exists():
        print("✅ No stuck payments found!")
        return
    
    print(f"⚠️  Found {stuck_payments.count()} payments stuck in 'processing' status:")
    print("-" * 60)
    
    total_stuck_amount = 0
    for payment in stuck_payments:
        hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
        total_stuck_amount += payment.amount
        
        print(f"Payment ID: {payment.id:4d} | Order: {payment.order.id:4d} | "
              f"Amount: KSh {payment.amount:8.2f} | Method: {payment.payment_method:6s} | "
              f"Stuck: {hours_stuck:5.1f}h | Date: {payment.payment_date.strftime('%Y-%m-%d %H:%M')}")
    
    print("-" * 60)
    print(f"Total stuck amount: KSh {total_stuck_amount:,.2f}")
    
    # Show options
    print("\n🔧 What would you like to do with these stuck payments?")
    print("1. Mark as 'failed' (recommended - allows customers to retry)")
    print("2. Mark as 'cancelled' (payment was cancelled)")
    print("3. Mark as 'pending' (reset to try again)")
    print("4. Show more details first")
    print("5. Exit without changes")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            new_status = 'failed'
            break
        elif choice == '2':
            new_status = 'cancelled'
            break
        elif choice == '3':
            new_status = 'pending'
            break
        elif choice == '4':
            show_payment_details(stuck_payments)
            continue
        elif choice == '5':
            print("Exiting without making changes.")
            return
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
    
    # Confirm the action
    print(f"\n⚠️  This will change {stuck_payments.count()} payments to '{new_status}' status.")
    confirm = input("Are you sure? Type 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("Operation cancelled.")
        return
    
    # Update the payments
    print(f"\n🔄 Updating payments to '{new_status}' status...")
    
    updated_count = 0
    for payment in stuck_payments:
        try:
            old_status = payment.status
            payment.status = new_status
            payment.save()
            updated_count += 1
            print(f"✅ Updated Payment {payment.id} (Order {payment.order.id}) from '{old_status}' to '{new_status}'")
        except Exception as e:
            print(f"❌ Failed to update Payment {payment.id}: {str(e)}")
    
    print(f"\n🎉 Successfully updated {updated_count} out of {stuck_payments.count()} payments!")
    
    # Show final status summary
    print("\n📊 Current payment status summary:")
    status_summary = Payment.objects.values('status').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount')
    ).order_by('status')
    
    for status_data in status_summary:
        status = status_data['status']
        count = status_data['count']
        amount = status_data['total_amount'] or 0
        print(f"  {status:12s}: {count:4d} payments | KSh {amount:10,.2f}")

def show_payment_details(payments):
    print("\n📋 Detailed payment information:")
    print("=" * 80)
    
    for payment in payments:
        hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
        
        print(f"\nPayment ID: {payment.id}")
        print(f"  Order ID: {payment.order.id}")
        print(f"  Client: {payment.client.username if payment.client else 'N/A'}")
        print(f"  Amount: KSh {payment.amount}")
        print(f"  Payment Method: {payment.payment_method}")
        print(f"  Transaction Reference: {payment.transaction_reference}")
        print(f"  IntaSend Invoice ID: {payment.intasend_invoice_id or 'N/A'}")
        print(f"  Payment Date: {payment.payment_date}")
        print(f"  Hours Stuck: {hours_stuck:.1f}")
        
        # Show order details
        order = payment.order
        print(f"  Order Status: {order.status}")
        print(f"  Order Title: {order.title}")
        print("-" * 40)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()