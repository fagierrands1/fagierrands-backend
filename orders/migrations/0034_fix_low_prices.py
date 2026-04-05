"""
Data migration to fix all orders with prices below minimum (250 KES)
"""
from django.db import migrations, models
from decimal import Decimal

def fix_low_prices(apps, schema_editor):
    """Fix orders with prices below 250 KES minimum"""
    Order = apps.get_model('orders', 'Order')
    OrderType = apps.get_model('orders', 'OrderType')
    
    min_price = Decimal('250.00')
    
    fixed_count = 0
    for order in Order.objects.filter(price__lt=min_price).select_related('order_type'):
        if order.order_type.name.lower() in ['banking']:
            continue
        
        old_price = order.price
        new_price = min_price
        order.price = new_price
        order.save(update_fields=['price'])
        
        fixed_count += 1
        print(f"Order {order.id}: Fixed price {old_price} → {new_price} KES")
    
    print(f"✓ Fixed {fixed_count} orders with low prices")

def reverse_fix(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0033_add_estimated_value_field'),
    ]

    operations = [
        migrations.RunPython(fix_low_prices, reverse_fix),
    ]
