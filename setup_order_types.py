"""
Setup correct order types for FagiErrands
ID 1: Normal Delivery (KSh 200 base)
ID 2: Cargo Delivery (KSh 300 base)
ID 3: Cheque Banking (KSh 200 base)
"""
from orders.models import OrderType

# Update or create order types
order_types = [
    {
        'id': 1,
        'name': 'Normal Delivery',
        'description': 'Pickup and delivery of packages, documents, or parcels',
        'base_price': 200.00,
        'price_per_km': 20.00,
        'min_price': 200.00
    },
    {
        'id': 2,
        'name': 'Cargo Delivery',
        'description': 'Transport of larger items or heavy cargo',
        'base_price': 300.00,
        'price_per_km': 20.00,
        'min_price': 300.00
    },
    {
        'id': 3,
        'name': 'Cheque Banking',
        'description': 'Banking errands including cheque deposits and withdrawals',
        'base_price': 200.00,
        'price_per_km': 20.00,
        'min_price': 200.00
    }
]

for ot_data in order_types:
    ot, created = OrderType.objects.update_or_create(
        id=ot_data['id'],
        defaults={
            'name': ot_data['name'],
            'description': ot_data['description'],
            'base_price': ot_data['base_price'],
            'price_per_km': ot_data['price_per_km'],
            'min_price': ot_data['min_price']
        }
    )
    action = "Created" if created else "Updated"
    print(f"{action} ID {ot.id}: {ot.name} - Base: KSh {ot.base_price}")

print("\n✅ Order types configured successfully!")
print("\nCurrent order types:")
for ot in OrderType.objects.all().order_by('id'):
    print(f"  {ot.id}. {ot.name} - Base: KSh {ot.base_price}")
