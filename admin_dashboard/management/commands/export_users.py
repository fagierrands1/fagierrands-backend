from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admin_dashboard.utils.excel_export import ExcelExporter

User = get_user_model()


class Command(BaseCommand):
    help = 'Export all users to Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='exports/users.xlsx',
            help='Output file path for the Excel file'
        )
        parser.add_argument(
            '--user-type',
            type=str,
            choices=['user', 'assistant', 'handler', 'admin', 'vendor'],
            help='Filter by user type'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        user_type = options.get('user_type')
        
        queryset = User.objects.all()
        if user_type:
            queryset = queryset.filter(user_type=user_type)
            self.stdout.write(f"Exporting {user_type} users...")
        else:
            self.stdout.write("Exporting all users...")
        
        exporter = ExcelExporter()
        
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                  'user_type', 'is_verified', 'email_verified', 'is_online', 'created_at', 'updated_at']
        headers = ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone', 
                   'User Type', 'Verified', 'Email Verified', 'Online', 'Created', 'Updated']
        
        exporter.add_queryset(queryset, fields, headers)
        
        saved_path = exporter.save(output_path)
        self.stdout.write(self.style.SUCCESS(f'Successfully exported {queryset.count()} users to {saved_path}'))
