# Generated migration for M-Pesa Daraja API integration
# This migration removes IntaSend fields and adds M-Pesa Daraja fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0024_remove_banking_transfer_fields'),
    ]

    operations = [
        # Remove IntaSend fields from Payment model
        migrations.RemoveField(
            model_name='payment',
            name='intasend_checkout_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='intasend_invoice_id',
        ),
        
        # Add M-Pesa Daraja fields to Payment model
        migrations.AddField(
            model_name='payment',
            name='mpesa_checkout_request_id',
            field=models.CharField(blank=True, max_length=255, null=True, help_text='M-Pesa CheckoutRequestID from STK Push'),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_merchant_request_id',
            field=models.CharField(blank=True, max_length=255, null=True, help_text='M-Pesa MerchantRequestID from STK Push'),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_receipt_number',
            field=models.CharField(blank=True, max_length=255, null=True, help_text='M-Pesa receipt number'),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_transaction_date',
            field=models.CharField(blank=True, max_length=50, null=True, help_text='M-Pesa transaction date'),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_phone_number',
            field=models.CharField(blank=True, max_length=20, null=True, help_text='Phone number used for M-Pesa payment'),
        ),
        
        # Remove IntaSend fields from OrderPrepayment model
        migrations.RemoveField(
            model_name='orderprepayment',
            name='intasend_checkout_id',
        ),
        migrations.RemoveField(
            model_name='orderprepayment',
            name='intasend_invoice_id',
        ),
        
        # Add M-Pesa Daraja fields to OrderPrepayment model
        migrations.AddField(
            model_name='orderprepayment',
            name='mpesa_checkout_request_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='orderprepayment',
            name='mpesa_merchant_request_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='orderprepayment',
            name='mpesa_receipt_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]