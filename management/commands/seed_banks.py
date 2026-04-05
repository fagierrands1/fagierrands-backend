from django.core.management.base import BaseCommand
from orders.models import Banks

class Command(BaseCommand):
    help = 'Seed the database with sample banks'

    def handle(self, *args, **kwargs):
        banks_data = [
            {'name': 'Bank of America', 'description': 'Leading US bank', 'is_active': True},
            {'name': 'Chase Bank', 'description': 'Major US bank', 'is_active': True},
            {'name': 'Wells Fargo', 'description': 'US multinational bank', 'is_active': True},
            {'name': 'Citibank', 'description': 'Global bank', 'is_active': True},
            {'name': 'HSBC', 'description': 'International bank', 'is_active': True},
        ]

        for bank_data in banks_data:
            bank, created = Banks.objects.get_or_create(name=bank_data['name'], defaults=bank_data)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created bank: {bank.name}"))
            else:
                self.stdout.write(f"Bank already exists: {bank.name}")
