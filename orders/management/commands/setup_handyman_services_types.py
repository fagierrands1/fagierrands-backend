from django.core.management.base import BaseCommand
from orders.models import HandymanServiceTypes, OrderType

class Command(BaseCommand):
    help = 'Sets up the handyman service types (plural model)'

    def handle(self, *args, **options):
        # Create service types
        service_types = [
            {
                'name': 'Plumbing',
                'description': 'Professional plumbing services including pipe repairs, installations, and drain cleaning.',
                'icon': 'fa-wrench',
                'price_estimate': 1500.00,
                'is_active': True
            },
            {
                'name': 'Electrical',
                'description': 'Electrical services including wiring, installations, and repairs.',
                'icon': 'fa-bolt',
                'price_estimate': 2000.00,
                'is_active': True
            },
            {
                'name': 'Carpentry',
                'description': 'Carpentry services including furniture assembly, repairs, and custom woodwork.',
                'icon': 'fa-hammer',
                'price_estimate': 1800.00,
                'is_active': True
            },
            {
                'name': 'Painting',
                'description': 'Professional painting services for interior and exterior surfaces.',
                'icon': 'fa-paint-roller',
                'price_estimate': 2500.00,
                'is_active': True
            },
            {
                'name': 'Cleaning',
                'description': 'Thorough cleaning services for homes and offices.',
                'icon': 'fa-broom',
                'price_estimate': 1200.00,
                'is_active': True
            },
        ]
        
        # Create or update each service type
        for service_data in service_types:
            service, created = HandymanServiceTypes.objects.update_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'icon': service_data['icon'],
                    'price_estimate': service_data['price_estimate'],
                    'is_active': service_data['is_active'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created HandymanServiceTypes: {service}'))
            else:
                self.stdout.write(f'Updated HandymanServiceTypes: {service}')
        
        self.stdout.write(self.style.SUCCESS('Handyman service types (plural model) setup complete!'))