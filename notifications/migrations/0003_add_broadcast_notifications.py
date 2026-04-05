# Generated manually for broadcast notifications

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0002_userpushsubscription'),
    ]

    operations = [
        # Add new notification types
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('order_created', 'Order Created'),
                    ('order_assigned', 'Order Assigned'),
                    ('order_started', 'Order Started'),
                    ('order_completed', 'Order Completed'),
                    ('order_cancelled', 'Order Cancelled'),
                    ('verification_approved', 'Verification Approved'),
                    ('verification_rejected', 'Verification Rejected'),
                    ('message', 'Message'),
                    ('app_update', 'App Update'),
                    ('promotion', 'Promotion'),
                    ('announcement', 'Announcement'),
                ],
                max_length=50
            ),
        ),
        # Create BroadcastNotification model
        migrations.CreateModel(
            name='BroadcastNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(
                    choices=[
                        ('app_update', 'App Update'),
                        ('promotion', 'Promotion'),
                        ('announcement', 'Announcement'),
                    ],
                    default='announcement',
                    max_length=50
                )),
                ('target_audience', models.CharField(
                    choices=[
                        ('all', 'All Users'),
                        ('clients', 'Clients Only'),
                        ('assistants', 'Assistants Only'),
                        ('handlers', 'Handlers Only'),
                        ('admins', 'Admins Only'),
                    ],
                    default='all',
                    max_length=20
                )),
                ('status', models.CharField(
                    choices=[
                        ('draft', 'Draft'),
                        ('scheduled', 'Scheduled'),
                        ('sending', 'Sending'),
                        ('sent', 'Sent'),
                        ('failed', 'Failed'),
                    ],
                    default='draft',
                    max_length=20
                )),
                ('action_url', models.URLField(blank=True, help_text='URL to open when notification is tapped', null=True)),
                ('image_url', models.URLField(blank=True, help_text='Image to display in notification', null=True)),
                ('scheduled_for', models.DateTimeField(blank=True, help_text='When to send the notification', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('total_recipients', models.IntegerField(default=0)),
                ('successful_sends', models.IntegerField(default=0)),
                ('failed_sends', models.IntegerField(default=0)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_broadcasts',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]