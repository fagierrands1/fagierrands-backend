# Generated to ensure critical M-Pesa fields exist in databases that may have missed migration 0025
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0029_payment_mpesa_transaction_id"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE IF EXISTS orders_payment
                    ADD COLUMN IF NOT EXISTS mpesa_checkout_request_id varchar(255),
                    ADD COLUMN IF NOT EXISTS mpesa_merchant_request_id varchar(255),
                    ADD COLUMN IF NOT EXISTS mpesa_receipt_number varchar(255),
                    ADD COLUMN IF NOT EXISTS mpesa_transaction_date varchar(50),
                    ADD COLUMN IF NOT EXISTS mpesa_phone_number varchar(20),
                    ADD COLUMN IF NOT EXISTS mpesa_transaction_id varchar(255);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE IF EXISTS orders_orderprepayment
                    ADD COLUMN IF NOT EXISTS mpesa_checkout_request_id varchar(255),
                    ADD COLUMN IF NOT EXISTS mpesa_merchant_request_id varchar(255),
                    ADD COLUMN IF NOT EXISTS mpesa_receipt_number varchar(255);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]