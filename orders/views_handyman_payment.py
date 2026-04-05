import uuid
import logging
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import HandymanOrder, Payment
from .ncba_service import NCBAService

from .views_payment_ncba import process_ncba_stk_push

logger = logging.getLogger(__name__)

class HandymanServiceFinalPaymentView(APIView):
    """
    API view for processing the final payment for handyman services
    This only charges the approved service price, not the facilitation fee
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, handyman_order_id):
        """Process the final payment for a handyman service"""
        try:
            # Get the handyman order
            handyman_order = HandymanOrder.objects.get(
                id=handyman_order_id,
                client=request.user,
                status='quote_approved',
                final_payment_complete=False
            )
        except HandymanOrder.DoesNotExist:
            return Response(
                {'error': 'Handyman order not found or not eligible for final payment'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if there's an approved service price
        if not handyman_order.approved_service_price or handyman_order.approved_service_price <= 0:
            return Response(
                {'error': 'No approved service price found for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a payment record for the final payment (only the approved service price)
        payment = Payment.objects.create(
            order=handyman_order.order,
            client=request.user,
            amount=handyman_order.approved_service_price,  # Only charge the approved service price
            final_amount=handyman_order.approved_service_price, # Ensure final_amount is set
            payment_method=request.data.get('payment_method', 'ncba'), # Default to ncba
            status='pending',
            transaction_reference=f"HANDYMAN-FINAL-{handyman_order.id}-{uuid.uuid4().hex[:8]}",
            phone_number=request.data.get('phone_number'),
            email=request.data.get('email')
        )
        
        # Process the payment based on the payment method
        if payment.payment_method in ['mpesa', 'ncba']:
            result = process_ncba_stk_push(payment)
        else:
            return Response({
                'success': False,
                'message': 'Card payments are currently not supported for handyman services. Please use M-Pesa or NCBA.',
                'error': 'Unsupported payment method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': 'Final payment initiated successfully',
                'payment_id': payment.id,
                'checkout_request_id': result.get('data', {}).get('transaction_id'),
                'merchant_request_id': result.get('data', {}).get('reference_id'),
                'note': 'You are only being charged for the approved service price. Check your phone for payment prompt.'
            })
        else:
            return Response({
                'success': False,
                'message': result.get('error', 'Payment processing failed'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
