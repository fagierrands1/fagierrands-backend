from django.core.management.base import BaseCommand
from orders.models import HandymanServiceType

class Command(BaseCommand):
    help = 'Add default handyman service types'

    def handle(self, *args, **kwargs):
        services = [
            {
                'name': 'Plumbing',
                'description': 'All plumbing related services including repairs and installations.',
                'icon': 'plumbing-icon',
                'price_estimate': 50.00,
                'is_active': True
            },
            {
                'name': 'Electrician',
                'description': 'Electrical services including wiring, repairs, and installations.',
                'icon': 'electrician-icon',
                'price_estimate': 60.00,
                'is_active': True
            }
        ]

        for service in services:
            obj, created = HandymanServiceType.objects.get_or_create(
                name=service['name'],
                defaults=service
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added service type: {service['name']}"))
            else:
                self.stdout.write(f"Service type already exists: {service['name']}")
