from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.db import transaction
from django.shortcuts import redirect
from django.urls import path
from django.template.response import TemplateResponse
from django import forms
import json


class StandaloneSTKPushForm(forms.Form):
    phone_number = forms.CharField(
        label="Phone number",
        help_text="Enter the customer's Safaricom number (07XXXXXXXX).",
    )
    amount = forms.DecimalField(
        label="Amount",
        min_value=1,
        max_digits=10,
        decimal_places=2,
        help_text="Total amount to charge the customer.",
    )
    account_reference = forms.CharField(
        label="Account reference",
        required=False,
        help_text="Optional. Defaults to 'Manual-STK'.",
    )
    transaction_description = forms.CharField(
        label="Transaction description",
        required=False,
        help_text="Optional short description shown to the customer.",
    )
    callback_url = forms.URLField(
        label="Callback URL",
        required=False,
        help_text="Optional. Override the default callback URL for this request only.",
    )


# Import models from both files
from .models import (
    Banks, BankingOrder, OrderType, Order, ShoppingItem, OrderImage, 
    OrderReview, CargoDeliveryDetails, HandymanServiceType, 
    HandymanOrder, HandymanOrderImage, HandymanServiceTypes, Payment, OrderPrepayment
)

# Try to import models from models_updated.py
try:
    from .models_updated import (
        OrderTracking, ClientFeedback, RiderFeedback, CargoPhoto, 
        CargoValue, ReportIssue, OrderVideo, Referral, 
        TrackingWaypoint, TrackingEvent, TrackingLocationHistory
    )
    models_updated_imported = True
except ImportError:
    models_updated_imported = False

# Register models with improved admin interfaces
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'get_transaction_reference',
        'get_order_id',
        'get_client',
        'get_amount',
        'get_payment_method',
        'get_status_with_warning',
        'get_hours_since_payment',
        'get_payment_date',
    )
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('transaction_reference', 'transaction_id', 'phone_number', 'email')
    date_hierarchy = 'payment_date'
    actions = [
        'mark_as_failed',
        'mark_as_cancelled',
        'mark_as_pending',
        'mark_as_completed',
        'send_mpesa_stk_push',
        'query_mpesa_stk_status',
    ]
    change_form_template = 'admin/orders/payment/change_form.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'manual-stk/',
                self.admin_site.admin_view(self.standalone_stk_push_view),
                name='orders_payment_manual_stk',
            ),
            path(
                '<int:payment_id>/send-stk/',
                self.admin_site.admin_view(self.process_stk_push_view),
                name='orders_payment_send_stk',
            ),
            path(
                '<int:payment_id>/stk-status/',
                self.admin_site.admin_view(self.process_stk_query_view),
                name='orders_payment_stk_status',
            ),
        ]
        return custom_urls + urls

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('order', 'client')

    def get_order_id(self, obj):
        try:
            return obj.order.id if obj.order else None
        except Exception:
            return None
    get_order_id.short_description = 'Order ID'
    
    def get_client(self, obj):
        try:
            return obj.client
        except Exception:
            return None
    get_client.short_description = 'Client'
    
    def get_amount(self, obj):
        try:
            return obj.amount
        except Exception:
            return None
    get_amount.short_description = 'Amount'
    
    def get_payment_method(self, obj):
        try:
            return obj.payment_method
        except Exception:
            return None
    get_payment_method.short_description = 'Payment Method'
    
    def get_status(self, obj):
        try:
            return obj.status
        except Exception:
            return None
    get_status.short_description = 'Status'
    
    def get_payment_date(self, obj):
        try:
            return obj.payment_date
        except Exception:
            return None
    get_payment_date.short_description = 'Payment Date'
    
    def get_transaction_reference(self, obj):
        try:
            return obj.transaction_reference
        except Exception:
            return None
    get_transaction_reference.short_description = 'Transaction Reference'
    
    def get_status_with_warning(self, obj):
        """Display status with warning for stuck payments"""
        try:
            status = obj.status
            if status == 'processing':
                hours_since = (timezone.now() - obj.payment_date).total_seconds() / 3600
                if hours_since > 2:  # More than 2 hours
                    return f"🔴 {status} ({hours_since:.1f}h)"
                elif hours_since > 1:  # More than 1 hour
                    return f"🟡 {status} ({hours_since:.1f}h)"
            return status
        except Exception:
            return obj.status if hasattr(obj, 'status') else None
    get_status_with_warning.short_description = 'Status'
    get_status_with_warning.admin_order_field = 'status'
    
    def get_hours_since_payment(self, obj):
        """Show how many hours since payment was created"""
        try:
            hours = (timezone.now() - obj.payment_date).total_seconds() / 3600
            if hours < 1:
                minutes = hours * 60
                return f"{minutes:.0f}m"
            elif hours < 24:
                return f"{hours:.1f}h"
            else:
                days = hours / 24
                return f"{days:.1f}d"
        except Exception:
            return None
    get_hours_since_payment.short_description = 'Age'
    get_hours_since_payment.admin_order_field = 'payment_date'
    
    # Admin actions for bulk status changes
    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed"""
        count = queryset.update(status='failed')
        self.message_user(request, f'{count} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected payments as cancelled"""
        count = queryset.update(status='cancelled')
        self.message_user(request, f'{count} payments marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected payments as cancelled"
    
    def mark_as_pending(self, request, queryset):
        """Mark selected payments as pending"""
        count = queryset.update(status='pending')
        self.message_user(request, f'{count} payments marked as pending.')
    mark_as_pending.short_description = "Mark selected payments as pending"
    
    def mark_as_completed(self, request, queryset):
        """Mark selected payments as completed"""
        count = queryset.update(status='completed')
        self.message_user(request, f'{count} payments marked as completed.')
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def order_id(self, obj):
        return obj.order.id if obj.order else None
    
    def send_mpesa_stk_push(self, request, queryset):
        """Admin action to initiate M-Pesa STK Push for selected payments."""
        success = 0
        errors = []
        for payment in queryset:
            try:
                result = self._trigger_stk_push(payment, request)
                if result:
                    success += 1
            except Exception as exc:
                errors.append(f"Payment {payment.id}: {exc}")
        if success:
            self.message_user(request, f"Successfully initiated STK Push for {success} payment(s).", level=messages.SUCCESS)
        if errors:
            self.message_user(request, "\n".join(errors), level=messages.ERROR)
    send_mpesa_stk_push.short_description = "Send M-Pesa STK Push"
    
    def query_mpesa_stk_status(self, request, queryset):
        """Admin action to query status of initiated STK Push requests via NCBA."""
        from .ncba_service import NCBAService
        ncba_service = NCBAService()
    
        for payment in queryset:
            if not payment.mpesa_checkout_request_id:
                self.message_user(
                    request,
                    f"Payment {payment.id} has no NCBA TransactionID yet; initiate STK first.",
                    level=messages.WARNING,
                )
                continue
            try:
                result = ncba_service.stk_query(payment.mpesa_checkout_request_id)
                self.message_user(
                    request,
                    f"Payment {payment.id} NCBA response: {json.dumps(result)}",
                    level=messages.INFO,
                )
                
                # Update payment status if found
                ncba_status = result.get('status')
                if ncba_status == 'SUCCESS':
                    payment.status = 'completed'
                    payment.save()
                elif ncba_status == 'FAILED':
                    payment.status = 'failed'
                    payment.save()
                    
            except Exception as exc:
                self.message_user(
                    request,
                    f"Failed to query NCBA payment {payment.id}: {exc}",
                    level=messages.ERROR,
                )
    query_mpesa_stk_status.short_description = "Query NCBA STK status"
    query_mpesa_stk_status.allowed_permissions = ('change',)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.setdefault(
            "standalone_stk_url",
            self.get_admin_url("orders_payment_manual_stk"),
        )
        return super().changelist_view(request, extra_context=extra_context)

    @staticmethod
    def get_admin_url(name):
        from django.urls import reverse

        return reverse(f"admin:{name}")

    def process_stk_push_view(self, request, payment_id, *args, **kwargs):
        payment = self.get_object(request, payment_id)
        if not payment:
            self.message_user(request, "Payment not found.", level=messages.ERROR)
            return redirect('admin:orders_payment_changelist')
        try:
            self._trigger_stk_push(payment, request, form_data=request.POST or None)
        except ValueError as validation_error:
            self.message_user(request, str(validation_error), level=messages.ERROR)
        except Exception as exc:
            self.message_user(request, f"Failed to initiate STK Push: {exc}", level=messages.ERROR)
        return redirect('admin:orders_payment_change', payment_id)
    
    def process_stk_query_view(self, request, payment_id, *args, **kwargs):
        payment = self.get_object(request, payment_id)
        if not payment:
            self.message_user(request, "Payment not found.", level=messages.ERROR)
            return redirect('admin:orders_payment_changelist')
        if not payment.mpesa_checkout_request_id:
            self.message_user(
                request,
                "Payment does not have an NCBA TransactionID yet.",
                level=messages.WARNING,
            )
            return redirect('admin:orders_payment_change', payment_id)
        from .ncba_service import NCBAService
        ncba_service = NCBAService()
    
        try:
            result = ncba_service.stk_query(payment.mpesa_checkout_request_id)
            self.message_user(
                request,
                f"NCBA response: {json.dumps(result)}",
                level=messages.INFO,
            )
        except Exception as exc:
            self.message_user(
                request,
                f"Failed to query NCBA status: {exc}",
                level=messages.ERROR,
            )
        return redirect('admin:orders_payment_change', payment_id)

    def standalone_stk_push_view(self, request):
        from .ncba_service import NCBAService
        ncba_service = NCBAService()

        if request.method == "POST":
            form = StandaloneSTKPushForm(request.POST)
            if form.is_valid():
                phone_number = form.cleaned_data["phone_number"]
                amount = form.cleaned_data["amount"]
                account_reference = (
                    form.cleaned_data["account_reference"] or "Manual-STK"
                )
                
                # NCBA expects 254...
                if phone_number.startswith('0'):
                    formatted_phone = '254' + phone_number[1:]
                elif not phone_number.startswith('254'):
                    formatted_phone = '254' + phone_number
                else:
                    formatted_phone = phone_number

                try:
                    result = ncba_service.initiate_stk_push(
                        phone_number=formatted_phone,
                        amount=float(amount),
                        account_no=account_reference
                    )
                    if result.get("StatusCode") == "0":
                        self.message_user(
                            request,
                            "NCBA STK push sent successfully. TransactionID: "
                            f"{result.get('TransactionID')}",
                            level=messages.SUCCESS,
                        )
                        return redirect("admin:orders_payment_manual_stk")
                    self.message_user(
                        request,
                        result.get(
                            "StatusDescription",
                            "Failed to initiate NCBA payment.",
                        ),
                        level=messages.ERROR,
                    )
                except Exception as exc:  # pragma: no cover - network failure path
                    self.message_user(
                        request,
                        f"Failed to initiate NCBA STK push: {exc}",
                        level=messages.ERROR,
                    )
        else:
            form = StandaloneSTKPushForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "title": "Send manual M-Pesa STK push",
        }
        return TemplateResponse(
            request,
            "admin/orders/payment/manual_stk_push.html",
            context,
        )

    def _trigger_stk_push(self, payment, request, form_data=None):
        """Helper that performs validation and triggers the STK push via NCBA."""
        from .ncba_service import NCBAService
        ncba_service = NCBAService()

        if payment.payment_method != 'mpesa':
            raise ValueError("Payment method must be M-Pesa to initiate STK push.")
        if not payment.phone_number:
            raise ValueError("Payment does not have a phone number associated with it.")

        if form_data and 'phone_number' in form_data and form_data['phone_number']:
            phone = form_data['phone_number']
        else:
            phone = payment.phone_number

        # NCBA expects 254...
        if phone.startswith('0'):
            formatted_phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            formatted_phone = '254' + phone
        else:
            formatted_phone = phone

        if form_data and form_data.get('amount'):
            amount_to_charge = form_data['amount']
        else:
            amount_to_charge = payment.final_amount or payment.amount

        result = ncba_service.initiate_stk_push(
            phone_number=formatted_phone,
            amount=float(amount_to_charge),
            account_no=f"Order-{payment.order_id}"
        )

        if result.get('StatusCode') == '0':
            payment.mpesa_checkout_request_id = result.get('TransactionID')
            payment.mpesa_phone_number = formatted_phone
            payment.status = 'processing'
            payment.save(update_fields=[
                'mpesa_checkout_request_id',
                'mpesa_phone_number',
                'status',
            ])
            self.message_user(
                request,
                f"NCBA STK Push sent. TransactionID: {payment.mpesa_checkout_request_id}",
                level=messages.SUCCESS,
            )
            return True

        error_message = result.get('StatusDescription', 'Failed to initiate NCBA payment')
        self.message_user(
            request,
            f"NCBA STK Push failed: {error_message}",
            level=messages.ERROR,
        )
        payment.status = 'failed'
        payment.save(update_fields=['status'])
        return False

@admin.register(OrderPrepayment)
class OrderPrepaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_reference', 'get_order_id', 'client', 'order_type', 'status',
        'deposit_amount', 'total_amount', 'payment_method', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at', 'order_type')
    search_fields = (
        'transaction_reference', 'intasend_invoice_id', 'intasend_checkout_id',
        'phone_number', 'email'
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'items_preview')
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_cancelled', 'create_orders_from_prepayments']

    fieldsets = (
        (None, {
            'fields': (
                'client', 'order_type', 'status',
                ('total_amount', 'deposit_amount'),
                ('payment_method', 'transaction_reference'),
                ('intasend_invoice_id', 'intasend_checkout_id'),
                ('phone_number', 'email'),
                'created_at',
                'items_preview',
            )
        }),
    )

    def items_preview(self, obj):
        try:
            data = obj.items
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-width:100%; white-space:pre-wrap; word-wrap:break-word;">{}</pre>', formatted)
        except Exception as e:
            return f"Error rendering items: {e}"
    items_preview.short_description = 'Items / Handyman Payload'

    def get_order_id(self, obj):
        try:
            return obj.order.id if obj.order else None
        except Exception:
            return None
    get_order_id.short_description = 'Order ID'

    # Admin actions
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} prepayment(s) marked as completed.")
    mark_as_completed.short_description = 'Mark selected prepayments as completed'

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} prepayment(s) marked as failed.")
    mark_as_failed.short_description = 'Mark selected prepayments as failed'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} prepayment(s) marked as cancelled.")
    mark_as_cancelled.short_description = 'Mark selected prepayments as cancelled'

    def create_orders_from_prepayments(self, request, queryset):
        """Create Orders for completed prepayments lacking an order (idempotent)."""
        created = 0
        skipped = 0
        errors = 0
        for prepay in queryset:
            try:
                if prepay.order_id or prepay.status != 'completed':
                    skipped += 1
                    continue
                with transaction.atomic():
                    order = Order.objects.create(
                        client=prepay.client,
                        order_type=prepay.order_type,
                        title=prepay.title or 'Shopping/Service Order',
                        description=prepay.description or '',
                        pickup_address=prepay.pickup_address or '',
                        pickup_latitude=prepay.pickup_latitude,
                        pickup_longitude=prepay.pickup_longitude,
                        delivery_address=prepay.delivery_address or '',
                        delivery_latitude=prepay.delivery_latitude,
                        delivery_longitude=prepay.delivery_longitude,
                        status='pending',
                    )

                    items_payload = prepay.items
                    if isinstance(items_payload, list):
                        for it in items_payload:
                            try:
                                ShoppingItem.objects.create(
                                    order=order,
                                    name=str((it or {}).get('name', 'Item')),
                                    quantity=int((it or {}).get('quantity', 1) or 1),
                                    price=float((it or {}).get('price', 0) or 0),
                                    description=str((it or {}).get('description', ''))[:500],
                                )
                            except Exception:
                                pass

                    # Optional handyman support if payload is dict with handyman
                    try:
                        from .models import HandymanOrder, HandymanServiceType
                        if isinstance(items_payload, dict) and items_payload.get('handyman'):
                            handyman_payload = items_payload.get('handyman') or {}
                            service_type = None
                            stid = handyman_payload.get('service_type_id')
                            if stid:
                                try:
                                    service_type = HandymanServiceType.objects.get(id=stid)
                                except HandymanServiceType.DoesNotExist:
                                    service_type = None
                            HandymanOrder.objects.create(
                                order=order,
                                client=prepay.client,
                                service_type=service_type,
                                description=prepay.description or '',
                                address=prepay.delivery_address or '',
                                latitude=prepay.delivery_latitude,
                                longitude=prepay.delivery_longitude,
                                scheduled_date=handyman_payload.get('scheduled_date') or timezone.now().date(),
                                scheduled_time_slot=handyman_payload.get('scheduled_time_slot') or 'morning',
                                alternative_contact=handyman_payload.get('alternative_contact') or '',
                                facilitation_fee=prepay.deposit_amount,
                                facilitation_fee_paid=True,
                                status='pending',
                            )
                    except Exception:
                        pass

                    try:
                        order.price = order.calculate_price()
                        order.save(update_fields=['price'])
                    except Exception:
                        pass

                    prepay.order = order
                    prepay.save(update_fields=['order'])
                    created += 1
            except Exception:
                errors += 1
        self.message_user(request, f"Created {created} order(s), skipped {skipped}, errors {errors}.")
    create_orders_from_prepayments.short_description = 'Create Orders from selected prepayments (completed only)'

@admin.register(OrderType)
class OrderTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'client', 'assistant', 'order_type', 'status', 'price', 'created_at')
    list_filter = ('status', 'order_type', 'created_at')
    search_fields = ('title', 'description', 'client__username', 'assistant__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'quantity', 'price')
    list_filter = ('order__status',)
    search_fields = ('name', 'description', 'order__title')

@admin.register(OrderImage)
class OrderImageAdmin(admin.ModelAdmin):
    list_display = ('order', 'description', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('order__title', 'description')
    date_hierarchy = 'uploaded_at'

@admin.register(OrderReview)
class OrderReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('order__title', 'comment')
    date_hierarchy = 'created_at'

@admin.register(CargoDeliveryDetails)
class CargoDeliveryDetailsAdmin(admin.ModelAdmin):
    list_display = ('order', 'cargo_weight', 'cargo_size', 'need_helpers')
    list_filter = ('need_helpers', 'cargo_size')
    search_fields = ('order__title', 'special_instructions')

@admin.register(HandymanServiceType)
class HandymanServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'facilitation_fee', 'is_active', 'order_type')
    list_filter = ('is_active', 'name')
    search_fields = ('name', 'description')
    autocomplete_fields = ('order_type',)

@admin.register(HandymanServiceTypes)
class HandymanServiceTypesAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_estimate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(HandymanOrder)
class HandymanOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'assistant', 'service_type', 'status', 'facilitation_fee', 
                   'service_quote', 'approved_service_price', 'total_price', 'scheduled_date')
    list_filter = ('status', 'service_type', 'scheduled_date', 'facilitation_fee_paid', 'final_payment_complete')
    search_fields = ('client__username', 'assistant__username', 'description', 'address')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'assistant', 'handler', 'service_type', 'description', 'status')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'scheduled_time_slot', 'alternative_contact')
        }),
        ('Payment Information', {
            'fields': (
                ('facilitation_fee', 'facilitation_fee_paid'),
                ('service_quote', 'quote_notes'), 
                ('approved_service_price', 'final_payment_complete'),
                'total_price',
            ),
            'description': '<div style="padding: 10px; background-color: #f8f9fa; border-left: 4px solid #0d6efd; margin-bottom: 10px;">'
                          '<strong>Payment Process:</strong><br>'
                          '1. Client pays the facilitation fee (KSh 500) upfront<br>'
                          '2. Service provider submits a quote after assessment<br>'
                          '3. Admin approves the quote and sets the final service price<br>'
                          '4. Client pays <strong>only the approved service price</strong> at the end<br>'
                          '5. Total price is calculated for record-keeping only</div>'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'assigned_at', 'started_at', 
                      'quote_provided_at', 'quote_approved_at', 'completed_at', 'cancelled_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save_model to calculate total price and update timestamps"""
        # If approved_service_price is set, calculate total price
        if obj.approved_service_price:
            # Calculate total value (for record-keeping)
            obj.total_price = obj.facilitation_fee + obj.approved_service_price
            
            # Update status to quote_approved if it was in quote_provided status
            if obj.status == 'quote_provided':
                obj.status = 'quote_approved'
                obj.quote_approved_at = timezone.now()
                
                # Add admin message
                from django.contrib import messages
                messages.info(request, 
                    f"Quote approved. The client will be charged KSh {obj.approved_service_price} "
                    f"for the service. They have already paid the KSh {obj.facilitation_fee} facilitation fee.")
        
        # If service_quote is set and status is in_progress, update status to quote_provided
        if obj.service_quote and obj.status == 'in_progress' and not obj.quote_provided_at:
            obj.status = 'quote_provided'
            obj.quote_provided_at = timezone.now()
            
        super().save_model(request, obj, form, change)

@admin.register(HandymanOrderImage)
class HandymanOrderImageAdmin(admin.ModelAdmin):
    list_display = ('order', 'description', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('order__id', 'description')
    date_hierarchy = 'uploaded_at'

@admin.register(Banks)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(BankingOrder)
class BankingOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank', 'transaction_type', 'amount', 'status', 'scheduled_date', 'created_at')
    list_filter = ('status', 'transaction_type', 'bank')
    search_fields = ('user__username', 'user__email', 'transaction_details')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

# Register models from models_updated.py if they were successfully imported
if models_updated_imported:
    @admin.register(OrderTracking)
    class OrderTrackingAdmin(admin.ModelAdmin):
        list_display = ('order', 'current_latitude', 'current_longitude', 'last_updated', 'estimated_arrival_time')
        search_fields = ('order__id', 'order__title')
        date_hierarchy = 'last_updated'
    
    @admin.register(ClientFeedback)
    class ClientFeedbackAdmin(admin.ModelAdmin):
        list_display = ('order', 'delivered_promptly', 'professionalism', 'service_quality', 'created_at')
        list_filter = ('delivered_promptly', 'professionalism', 'service_quality')
        search_fields = ('order__id', 'comments')
        date_hierarchy = 'created_at'
    
    @admin.register(RiderFeedback)
    class RiderFeedbackAdmin(admin.ModelAdmin):
        list_display = ('order', 'clear_communication', 'payment_timeliness', 'interaction_quality', 'created_at')
        list_filter = ('clear_communication', 'payment_timeliness', 'interaction_quality')
        search_fields = ('order__id', 'comments')
        date_hierarchy = 'created_at'
    
    @admin.register(CargoPhoto)
    class CargoPhotoAdmin(admin.ModelAdmin):
        list_display = ('order', 'description', 'uploaded_at')
        search_fields = ('order__id', 'description')
        date_hierarchy = 'uploaded_at'
    
    @admin.register(CargoValue)
    class CargoValueAdmin(admin.ModelAdmin):
        list_display = ('order', 'value', 'visible_to_handler_only')
        list_filter = ('visible_to_handler_only',)
        search_fields = ('order__id',)
    
    @admin.register(ReportIssue)
    class ReportIssueAdmin(admin.ModelAdmin):
        list_display = ('order', 'incident_timestamp', 'reported_at')
        search_fields = ('order__id', 'description')
        date_hierarchy = 'reported_at'
    
    @admin.register(OrderVideo)
    class OrderVideoAdmin(admin.ModelAdmin):
        list_display = ('order', 'description', 'uploaded_at')
        search_fields = ('order__id', 'description')
        date_hierarchy = 'uploaded_at'
    
    @admin.register(Referral)
    class ReferralAdmin(admin.ModelAdmin):
        list_display = ('referrer', 'referred_user', 'discount_amount', 'redeemed', 'created_at')
        list_filter = ('redeemed', 'created_at')
        search_fields = ('referrer__username', 'referred_user__username')
        date_hierarchy = 'created_at'
    
    @admin.register(TrackingWaypoint)
    class TrackingWaypointAdmin(admin.ModelAdmin):
        list_display = ('tracking', 'waypoint_type', 'name', 'order_index', 'arrival_time')
        list_filter = ('waypoint_type',)
        search_fields = ('tracking__order__id', 'name', 'description')
        date_hierarchy = 'arrival_time'
    
    @admin.register(TrackingEvent)
    class TrackingEventAdmin(admin.ModelAdmin):
        list_display = ('tracking', 'event_type', 'timestamp')
        list_filter = ('event_type', 'timestamp')
        search_fields = ('tracking__order__id', 'description')
        date_hierarchy = 'timestamp'
    
    @admin.register(TrackingLocationHistory)
    class TrackingLocationHistoryAdmin(admin.ModelAdmin):
        list_display = ('tracking', 'latitude', 'longitude', 'timestamp')
        search_fields = ('tracking__order__id',)
        date_hierarchy = 'timestamp'

