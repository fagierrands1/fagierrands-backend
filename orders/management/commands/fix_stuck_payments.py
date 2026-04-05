from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Payment
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix payments that have been stuck in processing status for too long'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout-hours',
            type=int,
            default=2,
            help='Number of hours after which a processing payment is considered stuck (default: 2)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes'
        )
        parser.add_argument(
            '--auto-confirm',
            action='store_true',
            help='Automatically confirm changes without prompting'
        )
        parser.add_argument(
            '--set-status',
            choices=['pending', 'failed', 'cancelled'],
            default='failed',
            help='Status to set for stuck payments (default: failed)'
        )

    def handle(self, *args, **options):
        timeout_hours = options['timeout_hours']
        dry_run = options['dry_run']
        auto_confirm = options['auto_confirm']
        new_status = options['set_status']
        
        # Calculate the cutoff time
        cutoff_time = timezone.now() - timedelta(hours=timeout_hours)
        
        self.stdout.write(f"Looking for payments stuck in 'processing' status for more than {timeout_hours} hours...")
        self.stdout.write(f"Cutoff time: {cutoff_time}")
        
        # Find stuck payments
        stuck_payments = Payment.objects.filter(
            status='processing',
            payment_date__lt=cutoff_time
        ).order_by('payment_date')
        
        if not stuck_payments.exists():
            self.stdout.write(self.style.SUCCESS("✅ No stuck payments found!"))
            return
        
        self.stdout.write(f"\n🔍 Found {stuck_payments.count()} stuck payments:")
        self.stdout.write("-" * 80)
        
        total_amount = 0
        for payment in stuck_payments:
            hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
            total_amount += payment.amount
            
            self.stdout.write(
                f"ID: {payment.id:4d} | "
                f"Order: {payment.order.id:4d} | "
                f"Amount: KSh {payment.amount:8.2f} | "
                f"Method: {payment.payment_method:6s} | "
                f"Stuck for: {hours_stuck:5.1f}h | "
                f"Date: {payment.payment_date.strftime('%Y-%m-%d %H:%M')}"
            )
        
        self.stdout.write("-" * 80)
        self.stdout.write(f"Total stuck amount: KSh {total_amount:,.2f}")
        
        if dry_run:
            self.stdout.write(f"\n🔍 DRY RUN: Would change {stuck_payments.count()} payments to '{new_status}' status")
            return
        
        # Confirm the action
        if not auto_confirm:
            self.stdout.write(f"\n⚠️  This will change {stuck_payments.count()} payments from 'processing' to '{new_status}' status.")
            
            if new_status == 'failed':
                self.stdout.write("   This means these payments will be marked as failed and customers may need to retry.")
            elif new_status == 'cancelled':
                self.stdout.write("   This means these payments will be marked as cancelled.")
            elif new_status == 'pending':
                self.stdout.write("   This means these payments will be reset to pending status for retry.")
            
            confirm = input("\nDo you want to proceed? (yes/no): ")
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write("Operation cancelled.")
                return
        
        # Update the payments
        self.stdout.write(f"\n🔄 Updating {stuck_payments.count()} payments to '{new_status}' status...")
        
        updated_count = 0
        for payment in stuck_payments:
            try:
                old_status = payment.status
                payment.status = new_status
                payment.save()
                updated_count += 1
                
                # Log the change
                logger.info(
                    f"Payment {payment.id} (Order {payment.order.id}) status changed from "
                    f"'{old_status}' to '{new_status}' - was stuck for "
                    f"{(timezone.now() - payment.payment_date).total_seconds() / 3600:.1f} hours"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to update payment {payment.id}: {str(e)}")
                )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully updated {updated_count} payments to '{new_status}' status")
            )
            
            # Show summary by payment method
            method_summary = {}
            for payment in stuck_payments:
                method = payment.payment_method
                if method not in method_summary:
                    method_summary[method] = {'count': 0, 'amount': 0}
                method_summary[method]['count'] += 1
                method_summary[method]['amount'] += payment.amount
            
            self.stdout.write("\n📊 Summary by payment method:")
            for method, data in method_summary.items():
                self.stdout.write(f"  {method}: {data['count']} payments, KSh {data['amount']:,.2f}")
        
        # Show current payment status overview
        self.stdout.write("\n📈 Current payment status overview:")
        status_counts = Payment.objects.values('status').annotate(
            count=models.Count('id')
        ).order_by('status')
        
        for status_data in status_counts:
            status = status_data['status']
            count = status_data['count']
            self.stdout.write(f"  {status}: {count}")
        
        self.stdout.write(f"\n✨ Operation completed successfully!")


# Import models at the end to avoid circular imports
from django.db import models