from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.email_utils import send_verification_email
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Test email verification system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test verification to',
            required=True
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f"Testing email verification for: {email}")
        
        try:
            # Check if user exists
            user = User.objects.get(email=email)
            self.stdout.write(f"Found user: {user.username}")
            
            # Send verification email
            success = send_verification_email(user)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Verification email sent successfully to {email}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to send verification email to {email}")
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"No user found with email: {email}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )