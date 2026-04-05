# Generated migration to remove transfer-related fields from BankingOrder
# This migration safely removes fields only if they exist in the database

from django.db import migrations, connection


def remove_fields_if_exist(apps, schema_editor):
    """
    Safely remove fields from BankingOrder table if they exist.
    This handles cases where fields were already removed or never created.
    This works with PostgreSQL databases.
    """
    BankingOrder = apps.get_model('orders', 'BankingOrder')
    table_name = BankingOrder._meta.db_table
    db_vendor = connection.vendor
    
    fields_to_remove = ['recipient_name', 'recipient_account']
    
    with connection.cursor() as cursor:
        for field_name in fields_to_remove:
            try:
                # Check if column exists (PostgreSQL specific)
                if db_vendor == 'postgresql':
                    cursor.execute(f"""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, [table_name, field_name])
                    column_exists = cursor.fetchone() is not None
                else:
                    # For other databases, try the operation and catch the error
                    column_exists = True
                
                if column_exists:
                    try:
                        if db_vendor == 'postgresql':
                            cursor.execute(f'ALTER TABLE "{table_name}" DROP COLUMN "{field_name}";')
                        else:
                            cursor.execute(f'ALTER TABLE {table_name} DROP COLUMN {field_name};')
                        print(f"✓ Dropped column '{field_name}' from {table_name}")
                    except Exception as e:
                        if "does not exist" in str(e) or "no such column" in str(e):
                            print(f"✓ Column '{field_name}' does not exist (skipped)")
                        else:
                            print(f"✗ Error removing column '{field_name}': {e}")
                else:
                    print(f"✓ Column '{field_name}' does not exist (skipped)")
            except Exception as e:
                print(f"⚠ Unexpected error processing '{field_name}': {e}")


def reverse_fields(apps, schema_editor):
    """
    Reverse operation - not implemented as we cannot safely restore fields without schema info.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0023_update_banking_transaction_types'),
    ]

    operations = [
        migrations.RunPython(remove_fields_if_exist, reverse_fields),
    ]