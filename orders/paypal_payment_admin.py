from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from .models import Payment
from .ncba_service import NCBAService


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:payment_id>/send-stk/",
                self.admin_site.admin_view(self.process_stk_push_view),
                name="orders_payment_send_stk",
            ),
        ]
        return custom_urls + urls

    def process_stk_push_view(self, request, payment_id, *args, **kwargs):
        payment = self.get_object(request, payment_id)
        if not payment:
            self.message_user(request, "Payment not found.", level=messages.ERROR)
            return redirect("admin:orders_payment_changelist")

        try:
            self._trigger_stk_push(payment, request)
        except Exception as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
        return redirect("admin:orders_payment_change", payment_id)

    def _trigger_stk_push(self, payment, request):
        if payment.payment_method != "mpesa":
            raise ValueError("Payment method must be M-Pesa to initiate STK push.")
        if not payment.phone_number:
            raise ValueError("Payment does not have a phone number associated with it.")

        # Format phone number for NCBA (254...)
        phone = payment.phone_number
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone

        ncba_service = NCBAService()
        result = ncba_service.initiate_stk_push(
            phone_number=phone,
            amount=float(payment.final_amount or payment.amount),
            account_no=f"Order-{payment.order_id}",
        )

        if result.get("success"):
            payment.mpesa_checkout_request_id = result.get("TransactionID")
            payment.mpesa_phone_number = phone
            payment.status = "processing"
            payment.save(
                update_fields=[
                    "mpesa_checkout_request_id",
                    "mpesa_phone_number",
                    "status",
                ]
            )
            self.message_user(
                request,
                f"NCBA STK Push sent. TransactionID: {payment.mpesa_checkout_request_id}",
                level=messages.SUCCESS,
            )
        else:
            error_message = result.get(
                "error", "Failed to initiate NCBA payment"
            )
            payment.status = "failed"
            payment.save(update_fields=["status"])
            self.message_user(
                request,
                f"NCBA STK Push failed: {error_message}",
                level=messages.ERROR,
            )