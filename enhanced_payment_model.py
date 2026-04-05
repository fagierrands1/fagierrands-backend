#!/usr/bin/env python
"""
Enhanced Payment Model for Better IntaSend Integration
Run this to generate the migration for enhanced payment fields
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.core.management import execute_from_command_line

def create_enhanced_payment_migration():
    """Create migration for enhanced payment model"""
    
    print("🔧 Creating Enhanced Payment Model Migration")
    print("=" * 50)
    
    # First, let's create the migration file content
    migration_content = '''# Generated migration for enhanced IntaSend integration

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),  # Adjust this to your latest migration
    ]

    operations = [
        # Add IntaSend specific fields
        migrations.AddField(
            model_name='payment',
            name='intasend_api_ref',
            field=models.CharField(blank=True, max_length=255, null=True, help_text='IntaSend API reference'),
        ),
        migrations.AddField(
            model_name='payment',
            name='intasend_provider',
            field=models.CharField(blank=True, max_length=50, null=True, help_text='Payment provider (M-PESA, CARD-PAYMENT)'),
        ),
        migrations.AddField(
            model_name='payment',
            name='intasend_charges',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, help_text='IntaSend processing charges'),
        ),
        migrations.AddField(
            model_name='payment',
            name='intasend_net_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, help_text='Net amount after charges'),
        ),
        
        # Add timestamp fields
        migrations.AddField(
            model_name='payment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Last updated timestamp'),
        ),
        migrations.AddField(
            model_name='payment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Payment completion timestamp'),
        ),
        
        # Add failure tracking fields
        migrations.AddField(
            model_name='payment',
            name='failure_reason',
            field=models.TextField(blank=True, null=True, help_text='Detailed failure reason from IntaSend'),
        ),
        migrations.AddField(
            model_name='payment',
            name='failure_code',
            field=models.CharField(blank=True, max_length=50, null=True, help_text='IntaSend failure code'),
        ),
        migrations.AddField(
            model_name='payment',
            name='retry_count',
            field=models.PositiveIntegerField(default=0, help_text='Number of retry attempts'),
        ),
        
        # Add webhook tracking fields
        migrations.AddField(
            model_name='payment',
            name='webhook_received_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When webhook was received'),
        ),
        migrations.AddField(
            model_name='payment',
            name='webhook_challenge',
            field=models.CharField(blank=True, max_length=255, null=True, help_text='Webhook challenge for validation'),
        ),
        
        # Add refund status to choices (requires model update)
        # This will be handled in the model definition
        
        # Add database indexes for performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_payment_status ON orders_payment(status);",
            reverse_sql="DROP INDEX IF EXISTS idx_payment_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_payment_intasend_invoice ON orders_payment(intasend_invoice_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_payment_intasend_invoice;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_payment_transaction_ref ON orders_payment(transaction_reference);",
            reverse_sql="DROP INDEX IF EXISTS idx_payment_transaction_ref;"
        ),
    ]
'''
    
    print("📝 Migration content prepared")
    print("\n🔧 To apply these enhancements:")
    print("1. Update your Payment model in orders/models.py")
    print("2. Run: python manage.py makemigrations orders --name enhanced_intasend_integration")
    print("3. Run: python manage.py migrate")
    
    print("\n📊 Enhanced fields to add to Payment model:")
    enhanced_fields = [
        "intasend_api_ref = models.CharField(max_length=255, blank=True, null=True)",
        "intasend_provider = models.CharField(max_length=50, blank=True, null=True)",
        "intasend_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)",
        "intasend_net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)",
        "updated_at = models.DateTimeField(auto_now=True)",
        "completed_at = models.DateTimeField(null=True, blank=True)",
        "failure_reason = models.TextField(blank=True, null=True)",
        "failure_code = models.CharField(max_length=50, blank=True, null=True)",
        "retry_count = models.PositiveIntegerField(default=0)",
        "webhook_received_at = models.DateTimeField(null=True, blank=True)",
        "webhook_challenge = models.CharField(max_length=255, blank=True, null=True)",
    ]
    
    for field in enhanced_fields:
        print(f"    {field}")
    
    print("\n✅ Also update PAYMENT_STATUS_CHOICES to include:")
    print("    ('refunded', 'Refunded'),")
    
    print("\n🎯 Benefits of enhanced model:")
    print("  ✅ Complete IntaSend webhook data capture")
    print("  ✅ Better failure tracking and debugging")
    print("  ✅ Automatic retry logic support")
    print("  ✅ Webhook security validation")
    print("  ✅ Performance optimized with indexes")
    print("  ✅ Comprehensive audit trail")

if __name__ == '__main__':
    create_enhanced_payment_migration()