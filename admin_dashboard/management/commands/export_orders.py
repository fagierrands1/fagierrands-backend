from django.core.management.base import BaseCommand
from orders.models import Order
from admin_dashboard.utils.excel_export import ExcelExporter


class Command(BaseCommand):
    help = 'Export all orders to Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='exports/orders.xlsx',
            help='Output file path for the Excel file'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['pending', 'assigned', 'accepted', 'in_progress', 'completed', 'cancelled'],
            help='Filter by order status'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        status = options.get('status')
        
        queryset = Order.objects.all().select_related('user', 'assigned_to', 'order_type')
        if status:
            queryset = queryset.filter(status=status)
            self.stdout.write(f"Exporting {status} orders...")
        else:
            self.stdout.write("Exporting all orders...")
        
        exporter = ExcelExporter()
        
        fields = ['id', 'user__username', 'order_type__name', 'assigned_to__username', 'status',
                  'pickup_location', 'dropoff_location', 'total_price', 'payment_status',
                  'created_at', 'updated_at']
        headers = ['ID', 'Customer', 'Service Type', 'Assigned To', 'Status',
                   'Pickup', 'Dropoff', 'Total Price', 'Payment Status', 'Created', 'Updated']
        
        exporter.add_queryset(queryset, fields, headers)
        
        saved_path = exporter.save(output_path)
        self.stdout.write(self.style.SUCCESS(f'Successfully exported {queryset.count()} orders to {saved_path}'))
