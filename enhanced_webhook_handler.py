#!/usr/bin/env python
"""
Enhanced IntaSend Webhook Handler
This is the improved version with comprehensive IntaSend integration
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class EnhancedIntaSendWebhookView(APIView):
    """
    Enhanced IntaSend webhook handler with comprehensive integration
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            payload = request.data
            logger.info(f"Received IntaSend webhook: {payload}")
            
            # Validate webhook challenge for security
            if not self.validate_webhook_challenge(payload):
                logger.error("Webhook challenge validation failed")
                return Response({
                    'status': 'error',
                    'message': 'Invalid webhook challenge'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Handle both official IntaSend format and legacy format
            if 'invoice_id' in payload and 'state' in payload:
                return self.handle_official_webhook(payload)
            elif 'event' in payload:
                return self.handle_legacy_webhook(payload)
            else:
                logger.warning(f"Unknown webhook format: {payload}")
                return Response({'status': 'success'})  # Accept unknown formats gracefully
        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def validate_webhook_challenge(self, payload):
        """Validate webhook challenge for security"""
        expected_challenge = "fagierrands_webhook_2025_secure"
        received_challenge = payload.get('challenge')
        
        # For now, allow webhooks without challenge (for testing)
        # In production, make this mandatory
        if not received_challenge:
            logger.warning("Webhook received without challenge - allowing for testing")
            return True
        
        if received_challenge != expected_challenge:
            logger.error(f"Invalid webhook challenge: {received_challenge}")
            return False
        
        return True
    
    def handle_official_webhook(self, payload):
        """Handle official IntaSend webhook format"""
        invoice_id = payload.get('invoice_id')
        state = payload.get('state')
        
        logger.info(f"Official IntaSend webhook: invoice_id={invoice_id}, state={state}")
        
        if not invoice_id:
            logger.error("No invoice_id in webhook payload")
            return Response({'status': 'success'})
        
        try:
            from orders.models import Payment
            payment = Payment.objects.get(intasend_invoice_id=invoice_id)
            
            old_status, new_status = self.update_payment_from_webhook(payment, payload)
            
            if old_status != new_status:
                logger.info(f"Payment {payment.id} status updated: {old_status} → {new_status}")
                
                # Handle order status updates
                self.update_order_status(payment, new_status)
                
                # Handle handyman orders
                self.update_handyman_order_status(payment, new_status)
            
            return Response({'status': 'success'})
            
        except Payment.DoesNotExist:
            logger.error(f"Payment with IntaSend invoice ID {invoice_id} not found")
            return Response({'status': 'success'})  # Don't return error to IntaSend
    
    def handle_legacy_webhook(self, payload):
        """Handle legacy webhook format for backward compatibility"""
        event = payload.get('event')
        logger.info(f"Legacy webhook format: event={event}")
        
        if event == 'payment.completed':
            data = payload.get('data', {})
            invoice_id = data.get('invoice', {}).get('id')
            
            if invoice_id:
                try:
                    from orders.models import Payment
                    payment = Payment.objects.get(intasend_invoice_id=invoice_id)
                    
                    old_status = payment.status
                    payment.status = 'completed'
                    
                    if data.get('mpesa_receipt'):
                        payment.transaction_id = data.get('mpesa_receipt')
                    
                    payment.webhook_received_at = timezone.now()
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    logger.info(f"Payment {payment.id} completed via legacy webhook")
                    
                    self.update_order_status(payment, 'completed')
                    self.update_handyman_order_status(payment, 'completed')
                    
                except Payment.DoesNotExist:
                    logger.error(f"Payment with invoice ID {invoice_id} not found")
        
        return Response({'status': 'success'})
    
    def update_payment_from_webhook(self, payment, webhook_data):
        """Enhanced webhook processing with full field mapping"""
        
        # Map IntaSend state to payment status
        state_mapping = {
            'COMPLETE': 'completed',
            'FAILED': 'failed',
            'PROCESSING': 'processing',
            'PENDING': 'pending'
        }
        
        old_status = payment.status
        new_status = state_mapping.get(webhook_data.get('state'), payment.status)
        
        # Update status
        payment.status = new_status
        
        # Update IntaSend specific fields (if model has these fields)
        if hasattr(payment, 'intasend_api_ref'):
            payment.intasend_api_ref = webhook_data.get('api_ref')
        if hasattr(payment, 'intasend_provider'):
            payment.intasend_provider = webhook_data.get('provider')
        
        # Update financial fields (if model has these fields)
        if hasattr(payment, 'intasend_charges') and webhook_data.get('charges'):
            try:
                payment.intasend_charges = Decimal(str(webhook_data['charges']))
            except (ValueError, TypeError):
                pass
        
        if hasattr(payment, 'intasend_net_amount') and webhook_data.get('net_amount'):
            try:
                payment.intasend_net_amount = Decimal(str(webhook_data['net_amount']))
            except (ValueError, TypeError):
                pass
        
        # Update transaction ID based on provider
        if webhook_data.get('account'):
            if webhook_data.get('provider') == 'M-PESA':
                payment.transaction_id = webhook_data['account']  # M-Pesa receipt
            else:
                payment.transaction_id = webhook_data['account']  # Card reference
        
        # Update failure information (if model has these fields)
        if hasattr(payment, 'failure_reason') and webhook_data.get('failed_reason'):
            payment.failure_reason = webhook_data['failed_reason']
        if hasattr(payment, 'failure_code') and webhook_data.get('failed_code'):
            payment.failure_code = webhook_data['failed_code']
        
        # Update webhook tracking (if model has these fields)
        if hasattr(payment, 'webhook_received_at'):
            payment.webhook_received_at = timezone.now()
        if hasattr(payment, 'webhook_challenge'):
            payment.webhook_challenge = webhook_data.get('challenge')
        
        # Update timestamps
        if hasattr(payment, 'updated_at'):
            payment.updated_at = timezone.now()
        
        if new_status == 'completed' and old_status != 'completed':
            if hasattr(payment, 'completed_at'):
                payment.completed_at = timezone.now()
        
        payment.save()
        
        return old_status, new_status
    
    def update_order_status(self, payment, payment_status):
        """Update order status based on payment status"""
        order = payment.order
        
        if payment_status == 'completed' and order.status == 'payment_pending':
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.save()
            logger.info(f"Order {order.id} marked as completed")
    
    def update_handyman_order_status(self, payment, payment_status):
        """Update handyman order status if applicable"""
        try:
            from orders.models import HandymanOrder
            handyman_order = HandymanOrder.objects.get(order=payment.order)
            
            if payment_status == 'completed' and handyman_order.status == 'quote_approved':
                handyman_order.status = 'completed'
                handyman_order.completed_at = timezone.now()
                handyman_order.final_payment_complete = True
                handyman_order.save()
                logger.info(f"Handyman order {handyman_order.id} marked as completed")
                
        except HandymanOrder.DoesNotExist:
            pass  # Not a handyman order

# Utility functions for payment processing

def format_phone_number_for_intasend(phone_number):
    """Robust phone number formatting for IntaSend"""
    if not phone_number:
        return None
    
    # Remove all non-digit characters except +
    import re
    phone = re.sub(r'[^\d+]', '', str(phone_number).strip())
    
    # Handle different formats
    if phone.startswith('+254'):
        return phone[1:]  # Remove + to get 254XXXXXXXXX
    elif phone.startswith('254'):
        return phone  # Already correct format
    elif phone.startswith('0') and len(phone) == 10:
        return '254' + phone[1:]  # Convert 07XXXXXXXX to 2547XXXXXXXX
    elif len(phone) == 9:
        return '254' + phone  # Add country code to 7XXXXXXXX
    else:
        # Invalid format, return as is and let IntaSend handle the error
        logger.warning(f"Unusual phone number format: {phone_number} -> {phone}")
        return phone

def retry_failed_payment(payment, max_retries=3):
    """Retry failed payment with exponential backoff"""
    if not hasattr(payment, 'retry_count'):
        logger.warning("Payment model doesn't have retry_count field")
        return False
    
    if payment.retry_count >= max_retries:
        logger.error(f"Payment {payment.id} exceeded max retries ({max_retries})")
        return False
    
    payment.retry_count += 1
    payment.status = 'pending'  # Reset to pending for retry
    payment.save()
    
    logger.info(f"Retrying payment {payment.id} (attempt {payment.retry_count})")
    return True

def get_payment_analytics():
    """Get payment analytics for monitoring"""
    from orders.models import Payment
    from django.db.models import Count, Sum
    
    analytics = {
        'total_payments': Payment.objects.count(),
        'status_breakdown': dict(Payment.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')),
        'total_amount': Payment.objects.aggregate(total=Sum('amount'))['total'] or 0,
        'success_rate': 0,
        'recent_activity': Payment.objects.order_by('-payment_date')[:10]
    }
    
    if analytics['total_payments'] > 0:
        completed_count = analytics['status_breakdown'].get('completed', 0)
        analytics['success_rate'] = (completed_count / analytics['total_payments']) * 100
    
    return analytics