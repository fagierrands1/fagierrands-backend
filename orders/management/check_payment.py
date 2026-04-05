import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Payment
from django.db import models

class Command(BaseCommand):
    help = 'Check payment statuses and identify issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-stuck',
            action='store_true',
            help='Show detailed information about stuck payments'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Consider payments stuck after this many hours (default: 2)'
        )

    def handle(self, *args, **options):
        show_stuck = options['show_stuck']
        stuck_hours = options['hours']
        
        self.stdout.write("🔍 Checking payment statuses...")
        
        # Get all payments
        payments = Payment.objects.all().order_by('-payment_date')
        
        self.stdout.write(f"📊 Total payments: {payments.count()}")
        
        # Group by status with amounts
        status_summary = Payment.objects.values('status').annotate(
            count=models.Count('id'),
            total_amount=models.Sum('amount')
        ).order_by('status')
        
        self.stdout.write("\n💰 Payment status breakdown:")
        self.stdout.write("-" * 50)
        total_amount = 0
        for status_data in status_summary:
            status = status_data['status']
            count = status_data['count']
            amount = status_data['total_amount'] or 0
            total_amount += amount
            self.stdout.write(f"  {status:12s}: {count:4d} payments | KSh {amount:10,.2f}")
        
        self.stdout.write("-" * 50)
        self.stdout.write(f"  {'TOTAL':12s}: {payments.count():4d} payments | KSh {total_amount:10,.2f}")
        
        # Show recent payments
        self.stdout.write(f"\n📅 Recent payments (last 10):")
        for payment in payments[:10]:
            hours_ago = (timezone.now() - payment.payment_date).total_seconds() / 3600
            self.stdout.write(
                f"  ID: {payment.id:4d} | {payment.status:10s} | "
                f"{payment.payment_method:6s} | KSh {payment.amount:8.2f} | "
                f"{hours_ago:5.1f}h ago"
            )
        
        # Check for stuck processing payments
        cutoff_time = timezone.now() - timedelta(hours=stuck_hours)
        stuck_payments = Payment.objects.filter(
            status='processing',
            payment_date__lt=cutoff_time
        ).order_by('payment_date')
        
        if stuck_payments.exists():
            self.stdout.write(f"\n⚠️  Found {stuck_payments.count()} payments stuck in 'processing' status for more than {stuck_hours} hours:")
            
            if show_stuck:
                self.stdout.write("-" * 80)
                stuck_total = 0
                for payment in stuck_payments:
                    hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
                    stuck_total += payment.amount
                    self.stdout.write(
                        f"  ID: {payment.id:4d} | Order: {payment.order.id:4d} | "
                        f"KSh {payment.amount:8.2f} | {payment.payment_method:6s} | "
                        f"Stuck: {hours_stuck:5.1f}h | {payment.payment_date.strftime('%Y-%m-%d %H:%M')}"
                    )
                self.stdout.write("-" * 80)
                self.stdout.write(f"  Total stuck amount: KSh {stuck_total:,.2f}")
            else:
                self.stdout.write("  Use --show-stuck to see detailed information")
            
            self.stdout.write(f"\n💡 To fix stuck payments, run:")
            self.stdout.write(f"   python manage.py fix_stuck_payments --timeout-hours {stuck_hours}")
            self.stdout.write(f"   python manage.py fix_stuck_payments --dry-run  # to preview changes")
                
        else:
            self.stdout.write(f"\n✅ No payments stuck in 'processing' status for more than {stuck_hours} hours")
        
        # Check for very old pending payments
        old_pending_cutoff = timezone.now() - timedelta(days=7)
        old_pending = Payment.objects.filter(
            status='pending',
            payment_date__lt=old_pending_cutoff
        ).count()
        
        if old_pending > 0:
            self.stdout.write(f"\n📋 Found {old_pending} pending payments older than 7 days")
        
        # Payment method breakdown for processing payments
        processing_by_method = Payment.objects.filter(status='processing').values('payment_method').annotate(
            count=models.Count('id'),
            total_amount=models.Sum('amount')
        )
        
        if processing_by_method:
            self.stdout.write(f"\n🔄 Processing payments by method:")
            for method_data in processing_by_method:
                method = method_data['payment_method']
                count = method_data['count']
                amount = method_data['total_amount'] or 0
                self.stdout.write(f"  {method:6s}: {count:3d} payments | KSh {amount:8,.2f}")
        
        self.stdout.write(f"\n✨ Payment status check completed!")