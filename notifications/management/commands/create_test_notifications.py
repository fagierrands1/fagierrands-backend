from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test notifications for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Create notifications for specific user ID',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                users = [user]
                self.stdout.write(f'Creating notifications for user: {user.username}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            users = User.objects.all()
            self.stdout.write(f'Creating notifications for {users.count()} users')

        test_notifications = [
            {
                'notification_type': 'message',
                'title': 'Welcome to Fagi Errands!',
                'message': 'Your notification system is working perfectly with VAPID support.'
            },
            {
                'notification_type': 'message',
                'title': 'System Update',
                'message': 'Push notifications are now enabled and ready to use.'
            },
            {
                'notification_type': 'message',
                'title': 'Test Notification',
                'message': 'This is a test notification to verify the system is working.'
            }
        ]

        created_count = 0
        for user in users:
            for notification_data in test_notifications:
                notification, created = Notification.objects.get_or_create(
                    recipient=user,
                    title=notification_data['title'],
                    defaults={
                        'notification_type': notification_data['notification_type'],
                        'message': notification_data['message'],
                        'read': False
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'Created: {notification.title} for {user.username}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} test notifications')
        )