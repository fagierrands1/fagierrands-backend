from django.core.management.base import BaseCommand
from orders.models import HandymanServiceType, OrderType

class Command(BaseCommand):
    help = 'Sets up the handyman service types'

    def handle(self, *args, **options):
        # Get or create the Handyman OrderType
        handyman_order_type, created = OrderType.objects.get_or_create(
            name='Handyman',
            defaults={
                'description': 'Handyman services including plumbing, electrical work, and landscaping',
                'base_price': 500.00,
                'price_per_km': 0.00,
                'min_price': 500.00,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created OrderType: {handyman_order_type}'))
        else:
            self.stdout.write(f'Using existing OrderType: {handyman_order_type}')
        
        # Define the service types
        service_types = [
            {
                'name': 'plumbing',
                'description': 'Plumbing services including repairs, installations, and maintenance',
                'icon': 'fa-wrench',
            },
            {
                'name': 'electrical',
                'description': 'Electrical work including wiring, installations, and repairs',
                'icon': 'fa-bolt',
            },
            {
                'name': 'landscaping',
                'description': 'Landscaping services including garden maintenance, design, and installation',
                'icon': 'fa-leaf',
            },
        ]
        
        # Create or update each service type
        for service_data in service_types:
            service, created = HandymanServiceType.objects.update_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'icon': service_data['icon'],
                    'facilitation_fee': 500.00,
                    'is_active': True,
                    'order_type': handyman_order_type,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created HandymanServiceType: {service}'))
            else:
                self.stdout.write(f'Updated HandymanServiceType: {service}')
        
        self.stdout.write(self.style.SUCCESS('Handyman service types setup complete!'))