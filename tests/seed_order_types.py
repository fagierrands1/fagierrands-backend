"""
Script to seed OrderTypes into the database.
Run this directly from Django shell:

python manage.py shell < seed_order_types.py

Or execute it as a standalone script:

python seed_order_types.py
"""

import os
import django

# Set up Django environment if running as standalone script
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
    django.setup()

# Import models
from orders.models import OrderType

# Define order types
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

# Create order types
count = 0
for order_type_data in order_types:
    order_type, created = OrderType.objects.get_or_create(
        name=order_type_data['name'],
        defaults={'description': order_type_data['description']}
    )
    
    if created:
        count += 1
        print(f'Created order type: {order_type.name}')
    else:
        print(f'Order type already exists: {order_type.name}')

print(f'Successfully created {count} order types')