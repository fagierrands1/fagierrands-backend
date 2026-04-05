import os
from django.core.management.base import BaseCommand
from notifications.utils import get_vapid_key

class Command(BaseCommand):
    help = 'Generate VAPID keys for Web Push notifications'

    def handle(self, *args, **options):
        try:
            # Generate keys
            vapid_keys = get_vapid_key()
            
            if not vapid_keys['public_key'] or not vapid_keys['private_key']:
                self.stdout.write(self.style.ERROR('Failed to generate VAPID keys. Make sure py_vapid is installed.'))
                return
                
            # Print keys
            self.stdout.write(self.style.SUCCESS('VAPID keys generated successfully!'))
            self.stdout.write(self.style.SUCCESS(f"VAPID_PUBLIC_KEY={vapid_keys['public_key']}"))
            self.stdout.write(self.style.SUCCESS(f"VAPID_PRIVATE_KEY={vapid_keys['private_key']}"))
            
            # Suggest adding to .env file
            self.stdout.write(self.style.WARNING('Add these keys to your .env file:'))
            self.stdout.write(f"VAPID_PUBLIC_KEY={vapid_keys['public_key']}")
            self.stdout.write(f"VAPID_PRIVATE_KEY={vapid_keys['private_key']}")
            self.stdout.write(f"WEBPUSH_EMAIL=admin@fagierrands.com")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating VAPID keys: {e}'))