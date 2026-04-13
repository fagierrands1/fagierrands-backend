from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0040_remove_bankingorder_recipient_account_and_more'),
    ]

    operations = [
        # Drop the orphaned table if it exists
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS orders_reportissue_evidence_photos CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP SEQUENCE IF EXISTS orders_reportissue_evidence_photos_id_seq CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
