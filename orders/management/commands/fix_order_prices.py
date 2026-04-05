from django.core.management.base import BaseCommand
from orders.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix pricing for existing orders to ensure consistency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('DRY RUN MODE - No changes will be made')
        
        self.stdout.write('Checking order prices for consistency...')
        
        orders = Order.objects.filter(price__isnull=False).select_related('order_type')
        updated_count = 0
        would_update_count = 0
        
        for order in orders:
            old_price = order.price
            calculated_price = order.calculate_price()
            
            # Check if prices differ significantly (more than 1 KES difference)
            if abs(old_price - calculated_price) > Decimal('1.00'):
                self.stdout.write(
                    f'Order {order.id}: {order.title[:30]}... '
                    f'Old: {old_price}, New: {calculated_price}'
                )
                
                if not dry_run:
                    order.price = calculated_price
                    order.save(update_fields=['price'])
                    updated_count += 1
                else:
                    would_update_count += 1
        
        if dry_run:
            self.stdout.write(f'Would update {would_update_count} orders')
        else:
            self.stdout.write(f'Updated {updated_count} orders')
        
        self.stdout.write('Price consistency check completed')