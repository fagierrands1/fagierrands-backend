from django.core.management.base import BaseCommand
from accounts.models import Profile
from admin_dashboard.utils.excel_export import ExcelExporter


class Command(BaseCommand):
    help = 'Export all user profiles to Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='exports/profiles.xlsx',
            help='Output file path for the Excel file'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        
        queryset = Profile.objects.all().select_related('user')
        self.stdout.write(f"Exporting {queryset.count()} profiles...")
        
        exporter = ExcelExporter()
        
        fields = ['user__id', 'user__username', 'user__email', 'address', 'wallet_points', 'wallet_balance']
        headers = ['User ID', 'Username', 'Email', 'Address', 'Wallet Points', 'Wallet Balance']
        
        exporter.add_queryset(queryset, fields, headers)
        
        saved_path = exporter.save(output_path)
        self.stdout.write(self.style.SUCCESS(f'Successfully exported {queryset.count()} profiles to {saved_path}'))
