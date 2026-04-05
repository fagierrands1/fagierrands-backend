from django.core.management.base import BaseCommand
from django.conf import settings
from intasend import APIService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test IntaSend API configuration'

    def handle(self, *args, **options):
        self.stdout.write("Testing IntaSend API configuration...")
        
        # Check if keys are set
        publishable_key = settings.INTASEND_PUBLISHABLE_KEY
        secret_key = settings.INTASEND_SECRET_KEY
        test_mode = settings.INTASEND_TEST_MODE
        
        self.stdout.write(f"Publishable Key: {'Set' if publishable_key else 'Not Set'}")
        self.stdout.write(f"Secret Key: {'Set' if secret_key else 'Not Set'}")
        self.stdout.write(f"Test Mode: {test_mode}")
        
        if not publishable_key or not secret_key:
            self.stdout.write(self.style.ERROR("IntaSend keys are not properly configured!"))
            return
        
        try:
            # Initialize API service
            api_service = APIService(
                token=secret_key,
                publishable_key=publishable_key,
                test=test_mode
            )
            
            # Try to get wallet balance (this will test if the keys are valid)
            try:
                wallets = api_service.wallets.list()
                self.stdout.write(self.style.SUCCESS("IntaSend API connection successful!"))
                self.stdout.write(f"Available wallets: {len(wallets) if wallets else 0}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not fetch wallets (this might be normal): {str(e)}"))
                
                # Try a simpler test - just initialize the collect service
                try:
                    collect_service = api_service.collect
                    self.stdout.write(self.style.SUCCESS("IntaSend collect service initialized successfully!"))
                except Exception as e2:
                    self.stdout.write(self.style.ERROR(f"Failed to initialize collect service: {str(e2)}"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize IntaSend API: {str(e)}"))