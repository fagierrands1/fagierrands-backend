from django.db import migrations, models
from decimal import Decimal

def revert_ordertype_prices(apps, schema_editor):
    OrderType = apps.get_model('orders', 'OrderType')
    OrderType.objects.all().update(
        base_price=Decimal('200.00'),
        min_price=Decimal('200.00'),
        price_per_km=Decimal('20.00')
    )

def reverse_revert(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0034_fix_low_prices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordertype',
            name='base_price',
            field=models.DecimalField(decimal_places=2, default=200.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='ordertype',
            name='min_price',
            field=models.DecimalField(decimal_places=2, default=200.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='ordertype',
            name='price_per_km',
            field=models.DecimalField(decimal_places=2, default=20.0, max_digits=10),
        ),
        migrations.RunPython(revert_ordertype_prices, reverse_revert),
    ]
