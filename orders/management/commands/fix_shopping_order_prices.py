from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix shopping orders with missing or incorrect prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find shopping orders with no price or price = 0
        shopping_orders = Order.objects.filter(
            order_type__name__icontains='shopping'
        ).filter(
            price__isnull=True
        ) | Order.objects.filter(
            order_type__name__icontains='shopping',
            price=0
        )

        self.stdout.write(f"Found {shopping_orders.count()} shopping orders with missing/zero prices")

        fixed_count = 0
        for order in shopping_orders:
            old_price = order.price
            
            # Calculate new price
            new_price = order.calculate_price()
            
            if dry_run:
                self.stdout.write(
                    f"Order {order.id}: {old_price} → {new_price} "
                    f"(items: {order.shopping_items.count()}, distance: {order.distance}km)"
                )
            else:
                order.price = new_price
                order.price_finalized = True
                order.save(update_fields=['price', 'price_finalized'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Order {order.id}: {old_price} → {new_price}"
                    )
                )
            
            fixed_count += 1

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully fixed {fixed_count} orders"
                )
            )
        else:
            self.stdout.write(f"\n[DRY RUN] Would fix {fixed_count} orders")
