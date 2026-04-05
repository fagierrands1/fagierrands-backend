from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import (
    Order,
    ShoppingItem,
    OrderImage,
    OrderAttachment,
    OrderReview,
    CargoDeliveryDetails,
    Payment,
    OrderPrepayment,
    EmergencyAlert,
    HandymanOrder,
    ServiceQuote,
    QuoteImage,
    HandymanOrderImage,
    BankingOrder,
)


class Command(BaseCommand):
    help = "Delete ALL order data (orders + related transactional records). Keeps master data like order types and banks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Show what would be deleted without making changes",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        skip_confirm = options.get("yes", False)

        counts = {
            "payments": Payment.objects.count(),
            "order_prepayments": OrderPrepayment.objects.count(),
            "emergency_alerts": EmergencyAlert.objects.count(),
            "service_quotes": ServiceQuote.objects.count(),
            "quote_images": QuoteImage.objects.count(),
            "handyman_order_images": HandymanOrderImage.objects.count(),
            "handyman_orders": HandymanOrder.objects.count(),
            "banking_orders": BankingOrder.objects.count(),
            "shopping_items": ShoppingItem.objects.count(),
            "order_images": OrderImage.objects.count(),
            "order_attachments": OrderAttachment.objects.count(),
            "order_reviews": OrderReview.objects.count(),
            "cargo_details": CargoDeliveryDetails.objects.count(),
            "orders": Order.objects.count(),
        }

        self.stdout.write("Planned deletions (transactional data only):")
        for k, v in counts.items():
            self.stdout.write(f" - {k}: {v}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: no data will be deleted."))
            return

        if not skip_confirm:
            confirm = input("Type 'DELETE' to confirm deletion of all order data: ").strip()
            if confirm != "DELETE":
                self.stdout.write(self.style.ERROR("Aborted."))
                return

        with transaction.atomic():
            # Delete children first (safety), though CASCADE would handle most
            QuoteImage.objects.all().delete()
            HandymanOrderImage.objects.all().delete()
            ServiceQuote.objects.all().delete()
            Payment.objects.all().delete()
            OrderPrepayment.objects.all().delete()
            EmergencyAlert.objects.all().delete()
            ShoppingItem.objects.all().delete()
            OrderImage.objects.all().delete()
            OrderAttachment.objects.all().delete()
            OrderReview.objects.all().delete()
            CargoDeliveryDetails.objects.all().delete()
            HandymanOrder.objects.all().delete()
            BankingOrder.objects.all().delete()
            # Finally, core orders
            Order.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("All order data cleared."))