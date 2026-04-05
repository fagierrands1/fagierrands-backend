"""
NCBA Till API Payment Views
Replaces legacy M-Pesa integration
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction as db_transaction
from .models import Order, Payment, OrderPrepayment, ShoppingItem
from .serializers import PaymentSerializer, InitiatePaymentSerializer
from .ncba_service import NCBAService
import json
import uuid
import logging

logger = logging.getLogger(__name__)

ncba_service = NCBAService()

def process_ncba_stk_push(payment):
    """
    Helper function to process NCBA STK Push payment
    Can be called from different views
    """
    try:
        logger.info(f"Processing NCBA STK Push for payment ID: {payment.id}")
        
        # Format phone number
        phone_number = payment.phone_number
        if not phone_number:
            return {'success': False, 'error': 'Phone number is required'}
            
        # Remove any non-numeric characters (like + or spaces)
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('7') and len(phone_number) == 9:
            phone_number = '254' + phone_number
        elif phone_number.startswith('1') and len(phone_number) == 9:
            # Handle new 01xx prefixes
            phone_number = '254' + phone_number
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        # Determine amount to charge (use final_amount if available, otherwise amount)
        amount_to_charge = payment.final_amount if payment.final_amount and payment.final_amount > 0 else payment.amount
        
        # Round to nearest integer (NCBA STK Push often rejects decimals)
        final_amount_to_charge = int(round(float(amount_to_charge)))
        
        logger.info(f"Original Amount: {amount_to_charge}, Rounded Amount: {final_amount_to_charge}")
        
        # Initiate STK Push via NCBA
        response = ncba_service.initiate_stk_push(
            phone_number=phone_number,
            amount=final_amount_to_charge,
            account_no=f"Order-{payment.order.id}"
        )
        
        logger.info(f"NCBA STK Push response: {json.dumps(response, indent=2)}")
        
        # Check response
        if response.get('success'):
            # Success - STK Push sent
            transaction_id = response.get('TransactionID')
            reference_id = response.get('ReferenceID')
            
            # Update payment with NCBA references
            payment.mpesa_checkout_request_id = transaction_id # Reusing field for TransactionID
            payment.status = 'processing'
            payment.save()
            
            logger.info(f"Payment {payment.id} updated with NCBA references")
            
            return {
                'success': True,
                'message': 'NCBA payment initiated successfully. Please check your phone for the payment prompt.',
                'data': {
                    'transaction_id': transaction_id,
                    'reference_id': reference_id,
                    'customer_message': response.get('StatusDescription', 'Please check your phone'),
                    'paybill': ncba_service.paybill_no,
                    'account': ncba_service.till_no if ncba_service.use_till_as_account else f"Order-{payment.order.id}"
                }
            }
        else:
            # Failed to initiate STK Push
            status_code = response.get('StatusCode', 'Unknown')
            status_desc = response.get('StatusDescription', 'Failed to initiate NCBA payment')
            error_message = f"STK Push Failed: {status_desc} (Code: {status_code})"
            
            logger.error(f"NCBA STK Push failed for payment {payment.id}: {error_message}")
            
            payment.status = 'failed'
            payment.save()
            
            return {
                'success': False,
                'error': error_message,
                'status_code': status_code,
                'manual_payment_details': {
                    'paybill': ncba_service.paybill_no,
                    'account': ncba_service.till_no if ncba_service.use_till_as_account else f"Order-{payment.order.id}",
                    'amount': float(amount_to_charge)
                }
            }
    
    except Exception as e:
        logger.error(f"Error processing NCBA payment for payment ID {payment.id}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Update payment status to failed
        payment.status = 'failed'
        payment.save()
        
        return {
            'success': False,
            'error': str(e)
        }

class InitiatePaymentView(generics.CreateAPIView):
    """
    API endpoint to initiate a payment for an order using NCBA Till
    """
    serializer_class = InitiatePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        logger.info(f"NCBA Payment initiation request data: {request.data}")
        
        try:
            # Validate the serializer
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Serializer validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the order exists and belongs to the current user
            order_id = serializer.validated_data.get('order').id
            try:
                order = Order.objects.get(id=order_id)
                logger.info(f"Found order: {order.id}, status: {order.status}")
                
                # Check if the order belongs to the current user
                if order.client != request.user and not request.user.is_staff:
                    return Response({'error': 'You do not have permission to initiate payment for this order'}, 
                                   status=status.HTTP_403_FORBIDDEN)
            except Order.DoesNotExist:
                return Response({'error': f'Order with ID {order_id} not found'}, 
                               status=status.HTTP_404_NOT_FOUND)
            
            # Check if payment already exists for this order
            existing_payment = Payment.objects.filter(order=order, status__in=['pending', 'processing']).first()
            if existing_payment:
                logger.info(f"Existing payment found: ID={existing_payment.id}, Method={existing_payment.payment_method}, Status={existing_payment.status}")
                # If payment is in processing status, reset it to pending to allow retry
                if existing_payment.status == 'processing':
                    logger.info(f"Resetting payment {existing_payment.id} from processing to pending for retry")
                    existing_payment.status = 'pending'
                    existing_payment.save()
                
                # Return the existing payment info
                response_data = {
                    'payment_id': existing_payment.id,
                    'transaction_reference': existing_payment.transaction_reference,
                    'amount': float(existing_payment.amount),
                    'discount_amount': float(existing_payment.discount_amount) if hasattr(existing_payment, 'discount_amount') else 0.0,
                    'final_amount': float(existing_payment.final_amount) if hasattr(existing_payment, 'final_amount') and existing_payment.final_amount else float(existing_payment.amount),
                    'points_used': existing_payment.points_used if hasattr(existing_payment, 'points_used') else 0,
                    'payment_method': existing_payment.payment_method,
                    'redirect_url': f"/payment/{existing_payment.id}"
                }

                # Auto-trigger STK push for NCBA/M-Pesa payments on retry
                logger.info(f"Checking if STK push should be triggered for existing payment: Method={existing_payment.payment_method}, Phone={existing_payment.phone_number}")
                if existing_payment.payment_method in ['ncba', 'mpesa'] and existing_payment.phone_number:
                    logger.info(f"Auto-triggering STK push for existing payment ID {existing_payment.id}")
                    stk_push_result = process_ncba_stk_push(existing_payment)
                    
                    if stk_push_result.get('success'):
                        response_data['stk_pushed'] = True
                        response_data['message'] = stk_push_result.get('message')
                        if 'data' in stk_push_result:
                            response_data['stk_data'] = stk_push_result['data']
                    else:
                        response_data['stk_pushed'] = False
                        response_data['stk_error'] = stk_push_result.get('error')
                        if 'manual_payment_details' in stk_push_result:
                            response_data['manual_payment_details'] = stk_push_result['manual_payment_details']
                else:
                    logger.info("STK push condition NOT met for existing payment")

                return Response(response_data, status=status.HTTP_200_OK)
            
            logger.info("No existing payment found, creating new one")
            # Create new payment
            payment = serializer.save(client=request.user)
            logger.info(f"Created new NCBA payment: ID={payment.id}, Status={payment.status}, Method={payment.payment_method}, Phone={payment.phone_number}")
            
            # Prepare response data with payment details
            response_data = {
                'payment_id': payment.id,
                'transaction_reference': payment.transaction_reference,
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'redirect_url': f"/payment/{payment.id}"
            }
            
            # Auto-trigger STK push for NCBA/M-Pesa payments
            logger.info(f"Checking if STK push should be triggered for new payment: Method={payment.payment_method}, Phone={payment.phone_number}")
            if payment.payment_method in ['ncba', 'mpesa'] and payment.phone_number:
                logger.info(f"Auto-triggering STK push for payment ID {payment.id}")
                stk_push_result = process_ncba_stk_push(payment)
                
                if stk_push_result.get('success'):
                    response_data['stk_pushed'] = True
                    response_data['message'] = stk_push_result.get('message')
                    if 'data' in stk_push_result:
                        response_data['stk_data'] = stk_push_result['data']
                else:
                    response_data['stk_pushed'] = False
                    response_data['stk_error'] = stk_push_result.get('error')
                    if 'manual_payment_details' in stk_push_result:
                        response_data['manual_payment_details'] = stk_push_result['manual_payment_details']
            else:
                logger.info("STK push condition NOT met for new payment")
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            logger.error(f"Error in NCBA payment initiation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentStatusView(generics.RetrieveAPIView):
    """
    API endpoint to check the status of a payment
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Override to get the payment object with better error handling
        """
        payment_id = self.kwargs.get('pk')
        
        try:
            # First check if the payment exists at all
            payment = Payment.objects.get(id=payment_id)
            
            # Then check if it belongs to the current user
            if payment.order.client != self.request.user:
                self.permission_denied(
                    self.request,
                    message="You do not have permission to view this payment."
                )
            
            return payment
        except Payment.DoesNotExist:
            # Custom 404 response with more details
            from django.http import Http404
            raise Http404(f"Payment with ID {payment_id} does not exist.")


class NCBAPaymentView(APIView):
    """
    API endpoint to process a payment through NCBA Till API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            logger.info(f"Processing NCBA payment request for payment ID: {payment_id}")
            
            # Get the payment object
            payment = get_object_or_404(Payment, id=payment_id)
            logger.info(f"Found payment: ID={payment.id}, Status={payment.status}, Method={payment.payment_method}")
            
            # Check if the payment belongs to the current user
            if payment.order.client != request.user:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to process this payment.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if payment is already completed
            if payment.status == 'completed':
                return Response({
                    'status': 'error',
                    'message': 'Payment is already completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate phone number
            if not payment.phone_number:
                return Response({
                    'status': 'error',
                    'message': 'Phone number is required for NCBA payment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process NCBA payment
            return self.process_ncba_payment(payment)
            
        except Exception as e:
            logger.error(f"Error in NCBAPaymentView.post for payment ID {payment_id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_ncba_payment(self, payment):
        """
        Process NCBA STK Push payment
        """
        result = process_ncba_stk_push(payment)
        
        if result.get('success'):
            return Response({
                'status': 'success',
                'message': result.get('message'),
                'data': result.get('data')
            })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get('error') == 'Internal Server Error':
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                
            response_data = {
                'status': 'error',
                'message': result.get('error')
            }
            if 'manual_payment_details' in result:
                response_data['manual_payment_details'] = result['manual_payment_details']
                
            return Response(response_data, status=status_code)


class NCBAWebhookHandler:
    """
    NCBA Till API webhook handler
    """

    @staticmethod
    def handle_callback(payload):
        """
        Handle NCBA callback
        """
        logger.info("=" * 80)
        logger.info("Processing NCBA callback")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            # NCBA callback format might differ from M-Pesa
            # For now, let's assume it has TransactionID and Status
            transaction_id = payload.get('TransactionID')
            status_val = payload.get('Status') # 'SUCCESS' or 'FAILED'
            
            if not transaction_id:
                logger.error("No TransactionID in NCBA callback")
                return {'status': 'error', 'message': 'No TransactionID'}

            # Try to find payment by transaction ID (stored in mpesa_checkout_request_id)
            payment = None
            prepayment = None

            try:
                payment = Payment.objects.get(mpesa_checkout_request_id=transaction_id)
                logger.info(f"Found regular payment: ID={payment.id}, Order ID={payment.order.id}")
            except Payment.DoesNotExist:
                try:
                    prepayment = OrderPrepayment.objects.get(mpesa_checkout_request_id=transaction_id)
                    logger.info(f"Found prepayment: ID={prepayment.id}")
                except OrderPrepayment.DoesNotExist:
                    logger.error(f"No payment or prepayment found for TransactionID: {transaction_id}")
                    return {'status': 'error', 'message': 'Payment not found'}

            # Process based on status
            if status_val == 'SUCCESS':
                logger.info("NCBA Payment successful")
                with db_transaction.atomic():
                    if payment:
                        payment.status = 'completed'
                        payment.transaction_id = payload.get('MpesaReceiptNumber', transaction_id)
                        payment.save()
                        
                        # Update order
                        order = payment.order
                        if order.status == 'payment_pending':
                            order.status = 'completed'
                            order.completed_at = timezone.now()
                            order.save()
                    elif prepayment:
                        prepayment.status = 'completed'
                        prepayment.transaction_id = payload.get('MpesaReceiptNumber', transaction_id)
                        prepayment.save()
                        
                        logger.info(f"Prepayment {prepayment.id} marked as completed")
                        
                        # Handle prepayment logic (create order etc.)
                        if prepayment.order:
                            # Order already exists (new flow), just ensure it's in a good state
                            order = prepayment.order
                            logger.info(f"Linked order {order.id} found for prepayment")
                            # If it was payment_pending, move to pending
                            if order.status == 'payment_pending':
                                order.status = 'pending'
                                order.save()
                        else:
                            # Legacy flow: create order from prepayment details
                            try:
                                from .models import Order, ShoppingItem
                                order = Order.objects.create(
                                    client=prepayment.client,
                                    order_type=prepayment.order_type,
                                    title=prepayment.title or 'Shopping Order',
                                    description=prepayment.description or '',
                                    pickup_address=prepayment.pickup_address,
                                    pickup_latitude=prepayment.pickup_latitude,
                                    pickup_longitude=prepayment.pickup_longitude,
                                    delivery_address=prepayment.delivery_address,
                                    delivery_latitude=prepayment.delivery_latitude,
                                    delivery_longitude=prepayment.delivery_longitude,
                                    status='pending'
                                )
                                
                                # Create shopping items if provided
                                if isinstance(prepayment.items, list) and prepayment.items:
                                    for item_data in prepayment.items:
                                        try:
                                            ShoppingItem.objects.create(
                                                order=order,
                                                name=str(item_data.get('name', 'Item')),
                                                quantity=int(item_data.get('quantity', 1)),
                                                price=float(item_data.get('price', 0)),
                                                description=str(item_data.get('description', ''))
                                            )
                                        except Exception as e:
                                            logger.error(f"Failed to create shopping item in callback: {e}")
                                
                                # Link the order back to prepayment
                                prepayment.order = order
                                prepayment.save(update_fields=['order'])
                                logger.info(f"Order {order.id} created from prepayment {prepayment.transaction_reference}")
                            except Exception as e:
                                logger.error(f"Failed to create order from prepayment in callback: {e}")
            else:
                logger.warning(f"NCBA Payment failed: {status_val}")
                if payment:
                    payment.status = 'failed'
                    payment.save()
                elif prepayment:
                    prepayment.status = 'failed'
                    prepayment.save()

            return {'status': 'success'}

        except Exception as e:
            logger.error(f"Error processing NCBA callback: {str(e)}")
            return {'status': 'error', 'message': str(e)}


class NCBACallbackView(APIView):
    """
    API endpoint to handle NCBA callbacks
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = NCBAWebhookHandler.handle_callback(request.data)
        return Response(response)


class OrderPaymentStatusView(APIView):
    """
    API endpoint to check payment status for a specific order
    Optimized for NCBA and frontend polling
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            cache_key = f"payment_status_order_{order_id}_user_{request.user.id}"
            
            cached_data = cache.get(cache_key)
            if cached_data and not request.GET.get('force_refresh'):
                return Response(cached_data)
            
            order = get_object_or_404(Order, id=order_id)
            
            if order.client != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
            # Check regular payments first
            payment = Payment.objects.filter(order=order).order_by('-payment_date').first()
            if payment:
                # Polling logic for NCBA
                if payment.status == 'processing' and payment.mpesa_checkout_request_id:
                    try:
                        query_resp = ncba_service.stk_query(payment.mpesa_checkout_request_id)
                        if query_resp.get('status') == 'SUCCESS':
                            payment.status = 'completed'
                            payment.save()
                            if order.status == 'payment_pending':
                                order.status = 'completed'
                                order.completed_at = timezone.now()
                                order.save()
                        elif query_resp.get('status') == 'FAILED':
                            payment.status = 'failed'
                            payment.save()
                    except Exception as e:
                        logger.error(f"NCBA Query failed: {e}")

                response_data = {
                    'order_id': order.id,
                    'order_status': order.status,
                    'payment': {
                        'id': payment.id,
                        'status': payment.status,
                        'amount': str(payment.amount),
                        'payment_method': payment.payment_method,
                    },
                    'has_payment': True,
                    'payment_type': 'regular'
                }
                cache.set(cache_key, response_data, 10)
                return Response(response_data)
            
            # Check prepayments
            prepayment = OrderPrepayment.objects.filter(order=order).order_by('-created_at').first()
            if prepayment:
                response_data = {
                    'order_id': order.id,
                    'order_status': order.status,
                    'payment': {
                        'id': prepayment.id,
                        'status': prepayment.status,
                        'amount': str(prepayment.deposit_amount),
                    },
                    'has_payment': True,
                    'payment_type': 'prepayment'
                }
                return Response(response_data)
                
            return Response({
                'order_id': order.id,
                'order_status': order.status,
                'has_payment': False
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCancellationView(APIView):
    """
    API endpoint to cancel a pending/processing payment
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            # Get the payment and verify ownership
            payment = get_object_or_404(Payment, id=payment_id)
            
            # Check if the payment belongs to the current user's order
            if payment.order.client != request.user:
                return Response({
                    'error': 'You do not have permission to cancel this payment.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Only allow cancellation of processing/pending payments
            if payment.status not in ['processing', 'pending', 'initiated']:
                return Response({
                    'error': f'Cannot cancel payment with status: {payment.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update payment status to cancelled
            payment.status = 'cancelled'
            payment.save()
            
            # Clear cache for this order's payment status
            cache_key = f"payment_status_order_{payment.order.id}_user_{request.user.id}"
            cache.delete(cache_key)
            
            logger.info(f"Payment {payment_id} cancelled by user {request.user.id}")
            
            return Response({
                'message': 'Payment cancelled successfully',
                'payment_id': payment_id,
                'new_status': 'cancelled',
                'cancelled_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error cancelling payment {payment_id}: {str(e)}")
            return Response({
                'error': 'Failed to cancel payment',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NCBAQRGenerationView(APIView):
    """
    API endpoint to generate NCBA Dynamic QR Code
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            amount = request.data.get('amount')
            order_id = request.data.get('order_id')
            narration = f"Order-{order_id}" if order_id else "Fagi Errands"
            
            qr_data = ncba_service.generate_qr(amount=amount, narration=narration)
            return Response(qr_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
