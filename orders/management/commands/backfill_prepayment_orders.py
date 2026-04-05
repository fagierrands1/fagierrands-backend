from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from orders.models import (
    OrderPrepayment,
    Order,
    ShoppingItem,
)

# Optional imports guarded inside functions to avoid hard dependency if app parts are missing
try:
    from orders.models import HandymanOrder, HandymanServiceType
    HAS_HANDYMAN = True
except Exception:
    HAS_HANDYMAN = False


class Command(BaseCommand):
    help = (
        "Create missing Orders from completed OrderPrepayment records. "
        "By default runs in DRY-RUN mode. Use --commit to persist changes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reference",
            dest="reference",
            help="Filter by specific prepayment transaction_reference",
        )
        parser.add_argument(
            "--invoice-id",
            dest="invoice_id",
            help="Filter by specific IntaSend invoice ID",
        )
        parser.add_argument(
            "--since-days",
            dest="since_days",
            type=int,
            default=None,
            help="Only process prepayments created within the last N days",
        )
        parser.add_argument(
            "--limit",
            dest="limit",
            type=int,
            default=None,
            help="Limit the number of prepayments to process",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            dest="commit",
            help="Actually create orders (otherwise dry-run)",
        )

    def handle(self, *args, **options):
        reference = options.get("reference")
        invoice_id = options.get("invoice_id")
        since_days = options.get("since_days")
        limit = options.get("limit")
        commit = options.get("commit")

        qs = OrderPrepayment.objects.filter(status="completed", order__isnull=True)
        if reference:
            qs = qs.filter(transaction_reference=reference)
        if invoice_id:
            qs = qs.filter(intasend_invoice_id=invoice_id)
        if since_days:
            cutoff = timezone.now() - timezone.timedelta(days=since_days)
            qs = qs.filter(created_at__gte=cutoff)
        if limit:
            qs = qs.order_by("created_at")[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No completed prepayments without orders found."))
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Found {total} completed prepayment(s) missing Orders. Mode: {'COMMIT' if commit else 'DRY-RUN'}."
            )
        )

        created_count = 0
        for prepay in qs:
            try:
                with transaction.atomic():
                    order = Order(
                        client=prepay.client,
                        order_type=prepay.order_type,
                        title=prepay.title or "Shopping/Service Order",
                        description=prepay.description or "",
                        # Map addresses/coordinates
                        pickup_address=prepay.pickup_address or "",
                        pickup_latitude=prepay.pickup_latitude,
                        pickup_longitude=prepay.pickup_longitude,
                        delivery_address=prepay.delivery_address or "",
                        delivery_latitude=prepay.delivery_latitude,
                        delivery_longitude=prepay.delivery_longitude,
                        status="pending",
                    )

                    # Price will be calculated after saving items
                    if commit:
                        order.save()

                    # Create items if prepay.items is a list of shopping items
                    items_payload = prepay.items
                    if isinstance(items_payload, list):
                        for it in items_payload:
                            name = str((it or {}).get("name", "Item"))
                            qty = int((it or {}).get("quantity", 1) or 1)
                            price = float((it or {}).get("price", 0) or 0)
                            if commit:
                                ShoppingItem.objects.create(
                                    order=order,
                                    name=name,
                                    quantity=qty,
                                    price=price,
                                    description=str((it or {}).get("description", ""))[:500],
                                )

                    # If payload contains handyman metadata, optionally create a HandymanOrder
                    if HAS_HANDYMAN and isinstance(items_payload, dict) and items_payload.get("handyman"):
                        handyman_payload = items_payload.get("handyman") or {}
                        service_type_id = handyman_payload.get("service_type_id")
                        if service_type_id:
                            try:
                                service_type = HandymanServiceType.objects.get(id=service_type_id)
                            except HandymanServiceType.DoesNotExist:
                                service_type = None
                        else:
                            service_type = None

                        if commit:
                            HandymanOrder.objects.create(
                                order=order,
                                client=prepay.client,
                                service_type=service_type,
                                description=prepay.description or "",
                                address=prepay.delivery_address or "",
                                latitude=prepay.delivery_latitude,
                                longitude=prepay.delivery_longitude,
                                scheduled_date=handyman_payload.get("scheduled_date") or timezone.now().date(),
                                scheduled_time_slot=handyman_payload.get("scheduled_time_slot") or "morning",
                                alternative_contact=handyman_payload.get("alternative_contact") or "",
                                facilitation_fee=prepay.deposit_amount,
                                facilitation_fee_paid=True,
                                status="pending",
                            )

                    # Calculate and set price
                    if commit:
                        try:
                            order.price = order.calculate_price()
                            order.save(update_fields=["price"])
                        except Exception:
                            pass

                        # Link back on prepayment
                        prepay.order = order
                        prepay.save(update_fields=["order"])

                created_count += 1

                # Log summary for each item
                self.stdout.write(
                    f"{'[DRY-RUN] ' if not commit else ''}Prepared order for prepayment {prepay.transaction_reference} "
                    f"-> order_title='{order.title}' client='{prepay.client}' items_type={'list' if isinstance(prepay.items, list) else type(prepay.items).__name__}"
                )

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed processing prepayment {prepay.transaction_reference}: {e}"
                    )
                )

        if commit:
            self.stdout.write(self.style.SUCCESS(f"Created {created_count} order(s) from completed prepayments."))
        else:
            self.stdout.write(self.style.WARNING(f"DRY-RUN complete. Would create {created_count} order(s). Re-run with --commit to persist."))