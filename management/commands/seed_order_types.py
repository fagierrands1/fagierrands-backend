from django.core.management.base import BaseCommand
from orders.models import OrderType

class Command(BaseCommand):
    help = 'Seeds initial order types into the database'

    def handle(self, *args, **options):
        order_types = [
            {
                'name': 'Shopping',
                'description': 'Purchase and delivery of groceries, goods, or other items.'
            },
            {
                'name': 'Delivery',
                'description': 'Pickup and delivery service for packages, documents, or other items.'
            },
            {
                'name': 'Cargo Delivery',
                'description': 'Transport of larger items or cargo requiring special handling.'
            },
            {
                'name': 'Banking',
                'description': 'Assistance with banking tasks such as deposits, withdrawals, or transfers.'
            },
            {
                'name': 'Handyman',
                'description': 'Home repair, maintenance, or other skilled work services.'
            },
        ]

        count = 0
        for order_type_data in order_types:
            order_type, created = OrderType.objects.get_or_create(
                name=order_type_data['name'],
                defaults={'description': order_type_data['description']}
            )
            
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Created order type: {order_type.name}'))
            else:
                self.stdout.write(f'Order type already exists: {order_type.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} order types'))