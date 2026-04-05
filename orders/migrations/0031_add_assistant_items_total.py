# Generated manually to add missing assistant_items_total field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0030_ensure_mpesa_columns_exist'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='assistant_items_total',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Final items total from receipt, set by assistant', max_digits=10, null=True),
        ),
    ]
