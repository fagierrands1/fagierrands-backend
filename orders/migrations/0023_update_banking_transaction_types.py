# Generated migration for updating BankingOrder transaction types to cheque_deposit only

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0022_trigram_extension_and_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankingorder',
            name='transaction_type',
            field=models.CharField(
                max_length=20,
                choices=[('cheque_deposit', 'Cheque Deposit')]
            ),
        ),
    ]