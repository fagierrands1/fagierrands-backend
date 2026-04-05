from django.db import migrations, models
from decimal import Decimal

def recalculate_order_prices(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    OrderType = apps.get_model('orders', 'OrderType')
    
    # We target orders with exactly 250.00 which were likely affected by migration 0034
    # and we exclude banking orders as they were excluded in 0034
    orders_to_fix = Order.objects.filter(price=Decimal('250.00')).exclude(order_type__name__iexact='banking')
    
    fixed_count = 0
    for order in orders_to_fix:
        order_type = order.order_type
        base_price = Decimal('200.00')
        price_per_km = Decimal('20.00')
        min_price = Decimal('200.00')
        
        # Recalculate based on 200 base for first 5km, 20 per extra km
        distance = order.distance
        if distance is None:
            new_price = base_price
        else:
            distance_decimal = Decimal(str(distance))
            if distance_decimal <= 5:
                new_price = base_price
            else:
                additional_distance = distance_decimal - 5
                new_price = base_price + (price_per_km * additional_distance)
        
        new_price = max(new_price, min_price)
        
        # If the recalculated price is different from 250, update it
        if new_price != order.price:
            old_price = order.price
            order.price = new_price
            order.save(update_fields=['price'])
            fixed_count += 1
            print(f"Order {order.id}: Reverted price {old_price} → {new_price} KES")

    print(f"✓ Reverted {fixed_count} orders to correct pricing")

def reverse_recalculate(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0036_revert_ordertype_to_200'),
    ]

    operations = [
        migrations.RunPython(recalculate_order_prices, reverse_recalculate),
    ]
