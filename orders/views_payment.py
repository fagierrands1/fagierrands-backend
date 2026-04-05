from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from .models import Order, Payment
from .serializers import PaymentSerializer, InitiatePaymentSerializer
import requests
import json
import uuid
import logging

logger = logging.getLogger(__name__)

# IntaSend API configuration
from intasend import APIService

INTASEND_PUBLISHABLE_KEY = settings.INTASEND_PUBLISHABLE_KEY
INTASEND_SECRET_KEY = settings.INTASEND_SECRET_KEY
INTASEND_TEST_MODE = settings.INTASEND_TEST_MODE

class InitiatePaymentView(generics.CreateAPIView):
    """
    API endpoint to initiate a payment for a completed order.
    """
    serializer_class = InitiatePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        logger.info(f"Payment initiation request data: {request.data}")
        
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
                return Response(response_data, status=status.HTTP_200_OK)
            
            # Create new payment
            payment = serializer.save(client=request.user)
            logger.info(f"Created new payment: ID={payment.id}, Status={payment.status}")
            
            # Prepare response data with payment details
            response_data = {
                'payment_id': payment.id,
                'transaction_reference': payment.transaction_reference,
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'redirect_url': f"/payment/{payment.id}"
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            logger.error(f"Error in payment initiation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentStatusView(generics.RetrieveAPIView):
    """
    API endpoint to check the status of a payment.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Override to get the payment object with better error handling.
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

class IntaSendPaymentView(APIView):
    """
    API endpoint to process a payment through IntaSend.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            logger.info(f"Processing payment request for payment ID: {payment_id}")
            
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
            
            # Allow retry for failed payments or pending payments
            # Don't set status to processing here - let the individual payment methods handle it
            
            # Prepare payment data based on payment method
            if payment.payment_method == 'mpesa':
                return self.process_mpesa_payment(payment)
            elif payment.payment_method == 'card':
                return self.process_card_payment(payment)
            else:
                payment.status = 'failed'
                payment.save()
                return Response({
                    'status': 'error',
                    'message': 'Invalid payment method'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in IntaSendPaymentView.post for payment ID {payment_id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_mpesa_payment(self, payment):
        # Rest of the method remains the same...
        try:
            logger.info(f"Processing M-Pesa payment for payment ID: {payment.id}")
            logger.info(f"IntaSend config - Test mode: {INTASEND_TEST_MODE}")
            
            # Validate IntaSend configuration
            if not INTASEND_SECRET_KEY or not INTASEND_PUBLISHABLE_KEY:
                logger.error("IntaSend keys are not properly configured")
                payment.status = 'failed'
                payment.save()
                return Response({
                    'status': 'error',
                    'message': 'Payment service configuration error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Initialize IntaSend API service
            api_service = APIService(
                token=INTASEND_SECRET_KEY,
                publishable_key=INTASEND_PUBLISHABLE_KEY,
                test=INTASEND_TEST_MODE
            )
            
            # Format phone number (remove leading 0 if present and ensure it starts with 254)
            phone_number = payment.phone_number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            logger.info(f"Formatted phone number: {phone_number}")
            logger.info(f"Payment amount: {payment.amount}")
            
            # Trigger M-Pesa STK Push
            response = api_service.collect.mpesa_stk_push(
                phone_number=phone_number,
                email=payment.order.client.email,
                amount=float(payment.amount),
                narrative=f"Payment for Order #{payment.order.id}"
            )
            
            # ENHANCED: Log the complete response for debugging
            logger.info(f"Complete IntaSend response: {json.dumps(response, indent=2)}")
            
            # ENHANCED: Extract invoice ID and state using multiple methods
            invoice_id = self.get_invoice_id_from_response(response)
            state = self.get_state_from_response(response)
            checkout_id = response.get('id') or response.get('checkout_id')
            
            logger.info(f"Extracted - Invoice ID: {invoice_id}, State: {state}, Checkout ID: {checkout_id}")
            
            # Check if STK Push was successful (handle multiple state formats)
            if state and state.upper() in ['PENDING', 'PROCESSING']:
                # Update payment with IntaSend references
                payment.intasend_checkout_id = checkout_id
                payment.intasend_invoice_id = invoice_id
                payment.status = 'processing'
                payment.save()
                
                logger.info(f"Payment {payment.id} updated with IntaSend references")
                
                return Response({
                    'status': 'success',
                    'message': 'M-Pesa payment initiated successfully',
                    'data': {
                        'checkout_id': checkout_id,
                        'invoice_id': invoice_id,
                        'state': state
                    }
                })
            else:
                # Log the failure details
                logger.error(f"STK Push failed - State: {state}, Response: {response}")
                
                payment.status = 'failed'
                payment.save()
                
                return Response({
                    'status': 'error',
                    'message': f'Failed to initiate M-Pesa payment. State: {state}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error processing M-Pesa payment for payment ID {payment.id}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Update payment status to failed
            payment.status = 'failed'
            payment.save()
            
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_invoice_id_from_response(self, response):
        """Enhanced invoice ID extraction from IntaSend response"""
        return (
            response.get('invoice', {}).get('id') or
            response.get('invoice_id') or
            response.get('data', {}).get('invoice_id') or
            response.get('invoice', {}).get('invoice_id')
        )
    
    def get_state_from_response(self, response):
        """Enhanced state extraction from IntaSend response"""
        return (
            response.get('invoice', {}).get('state') or
            response.get('state') or
            response.get('data', {}).get('state') or
            response.get('status') or
            response.get('invoice', {}).get('status')  # Added for nested status
        )
    

    def process_card_payment(self, payment):
        try:
            # Initialize IntaSend API service
            api_service = APIService(
                token=INTASEND_SECRET_KEY,
                publishable_key=INTASEND_PUBLISHABLE_KEY,
                test=INTASEND_TEST_MODE
            )
            
            # Create a checkout link for card payment
            response = api_service.collect.checkout({
                'first_name': payment.order.client.first_name,
                'last_name': payment.order.client.last_name,
                'email': payment.email,
                'amount': float(payment.amount),
                'currency': 'KES',
                'phone_number': payment.order.client.phone_number,
                'reference': payment.transaction_reference,
                'comment': f"Payment for Order #{payment.order.id}",
                'redirect_url': f"{settings.FRONTEND_URL}/payment/callback"
            })
            
            if response.get('invoice', {}).get('state') == 'PENDING':
                # Update payment with IntaSend references and set status to processing
                payment.intasend_checkout_id = response.get('id')
                payment.intasend_invoice_id = response.get('invoice', {}).get('id')
                payment.status = 'processing'  # Set to processing only after successful checkout creation
                payment.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Card payment initiated successfully',
                    'data': {
                        'payment_link': response.get('url'),
                        'checkout_id': response.get('id'),
                        'invoice_id': response.get('invoice', {}).get('id')
                    }
                })
            else:
                # Update payment status to failed
                payment.status = 'failed'
                payment.save()
                
                return Response({
                    'status': 'error',
                    'message': 'Failed to initiate card payment'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Update payment status to failed
            payment.status = 'failed'
            payment.save()
            
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCallbackView(APIView):
    """
    API endpoint to handle payment callbacks from IntaSend.
    """
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access for callbacks
    
    def get(self, request):
        # Get checkout ID and status from query parameters
        checkout_id = request.query_params.get('checkout_id')
        invoice_id = request.query_params.get('invoice_id')
        status = request.query_params.get('status')
        
        if not (checkout_id or invoice_id):
            return Response({
                'status': 'error',
                'message': 'Checkout ID or Invoice ID not provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the payment by IntaSend references
        try:
            if checkout_id:
                payment = Payment.objects.get(intasend_checkout_id=checkout_id)
            else:
                payment = Payment.objects.get(intasend_invoice_id=invoice_id)
        except Payment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update payment status based on callback status
        if status == 'COMPLETE':
            # Verify the payment with IntaSend
            verification_status = self.verify_payment(payment)
            
            if verification_status:
                payment.status = 'completed'
                payment.save()
                
                # Update order status to completed when payment is successful
                # Only mark as completed if order is in payment_pending status
                order = payment.order
                if order.status == 'payment_pending':
                    order.status = 'completed'
                    order.completed_at = timezone.now()
                    order.save()

                    # Award loyalty and referral points
                    try:
                        from accounts.models import WalletTransaction
                        # 10 points to customer
                        order.client.profile.wallet_points += 10
                        order.client.profile.save(update_fields=['wallet_points'])
                        WalletTransaction.objects.create(
                            user=order.client,
                            points=10,
                            amount_equivalent=10,
                            transaction_type='earn',
                            reference=f'order_{order.id}_completed'
                        )
                        # 20 points to referrer for each completed errand by referred user
                        if order.client.referred_by:
                            referrer = order.client.referred_by
                            referrer.profile.wallet_points += 20
                            referrer.profile.save(update_fields=['wallet_points'])
                            WalletTransaction.objects.create(
                                user=referrer,
                                points=20,
                                amount_equivalent=20,
                                transaction_type='earn',
                                reference=f'referral_order_{order.id}_completed'
                            )
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Failed to award loyalty/referral points for order {order.id}: {e}")
                
                # Also handle handyman orders if this payment is for a handyman service
                from .models import HandymanOrder
                try:
                    handyman_order = HandymanOrder.objects.get(order=order)
                    if handyman_order.status == 'quote_approved':
                        handyman_order.status = 'completed'
                        handyman_order.completed_at = timezone.now()
                        handyman_order.final_payment_complete = True
                        handyman_order.save()
                except HandymanOrder.DoesNotExist:
                    pass  # Not a handyman order, continue normally
                
                return Response({
                    'status': 'success',
                    'message': 'Payment completed successfully',
                    'redirect_url': f"/orders/{payment.order.id}"
                })
            else:
                payment.status = 'failed'
                payment.save()
                
                return Response({
                    'status': 'error',
                    'message': 'Payment verification failed',
                    'redirect_url': f"/payment/{payment.id}"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            payment.status = 'failed'
            payment.save()
            
            return Response({
                'status': 'error',
                'message': 'Payment was not successful',
                'redirect_url': f"/payment/{payment.id}"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def verify_payment(self, payment):
        """
        Verify payment with IntaSend API.
        """
        try:
            # Initialize IntaSend API service
            api_service = APIService(
                token=INTASEND_SECRET_KEY,
                publishable_key=INTASEND_PUBLISHABLE_KEY,
                test=INTASEND_TEST_MODE
            )
            
            # Verify the payment using the invoice ID
            if payment.intasend_invoice_id:
                response = api_service.collect.status(invoice_id=payment.intasend_invoice_id)
                
                if response.get('state') == 'COMPLETE':
                    # Update transaction ID if available
                    if response.get('mpesa_receipt'):
                        payment.transaction_id = response.get('mpesa_receipt')
                        payment.save()
                    return True
            
            return False
        
        except Exception:
            return False

class OrderPaymentStatusView(APIView):
    """
    API endpoint to check payment status for a specific order.
    Optimized for frontend polling with better performance and caching.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            # Create cache key for this order's payment status
            cache_key = f"payment_status_order_{order_id}_user_{request.user.id}"
            
            # Check cache first (cache for 10 seconds to reduce database load)
            cached_data = cache.get(cache_key)
            if cached_data and not request.GET.get('force_refresh'):
                # Add cache hit indicator
                cached_data['from_cache'] = True
                cached_data['last_checked'] = timezone.now().isoformat()
                return Response(cached_data)
            
            # Get the order and verify ownership
            order = get_object_or_404(Order, id=order_id)
            
            # Check if the order belongs to the current user
            if order.client != request.user:
                return Response({
                    'error': 'You do not have permission to view this order.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the most recent payment for this order
            try:
                payment = Payment.objects.filter(order=order).latest('created_at')
                payment_data = {
                    'id': payment.id,
                    'status': payment.status,
                    'amount': str(payment.amount),
                    'payment_method': payment.payment_method,
                    'transaction_reference': payment.transaction_reference,
                    'transaction_id': payment.transaction_id,
                    'created_at': payment.created_at.isoformat(),
                    'updated_at': payment.updated_at.isoformat(),
                    'intasend_checkout_id': payment.intasend_checkout_id,
                    'intasend_invoice_id': payment.intasend_invoice_id,
                }
                
                # Add processing time information
                if payment.status == 'processing':
                    processing_time = timezone.now() - payment.updated_at
                    payment_data['processing_duration_seconds'] = int(processing_time.total_seconds())
                    
                    # Suggest timeout if processing too long (more than 5 minutes)
                    if processing_time.total_seconds() > 300:
                        payment_data['suggest_timeout'] = True
                        payment_data['timeout_message'] = 'Payment has been processing for over 5 minutes. You may want to retry or contact support.'
                
            except Payment.DoesNotExist:
                payment_data = None
            
            # Get order status and related information
            order_data = {
                'id': order.id,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            }
            
            # Check for handyman orders
            handyman_payment_info = None
            try:
                from .models import HandymanOrder
                handyman_order = HandymanOrder.objects.get(order=order)
                handyman_payment_info = {
                    'facilitation_fee_paid': handyman_order.facilitation_fee_paid,
                    'final_payment_complete': handyman_order.final_payment_complete,
                    'approved_service_price': str(handyman_order.approved_service_price) if handyman_order.approved_service_price else None,
                    'status': handyman_order.status,
                }
            except:
                pass
            
            response_data = {
                'order': order_data,
                'payment': payment_data,
                'handyman_payment': handyman_payment_info,
                'last_checked': timezone.now().isoformat(),
                'polling_recommended': payment_data and payment_data['status'] in ['processing', 'pending', 'initiated'],
                'next_check_in_seconds': 5 if (payment_data and payment_data['status'] in ['processing', 'pending']) else 30,
                'from_cache': False,
            }
            
            # Cache the response for 10 seconds (only for non-final statuses)
            if payment_data and payment_data['status'] in ['processing', 'pending', 'initiated']:
                cache.set(cache_key, response_data, 10)  # Cache for 10 seconds
            elif payment_data and payment_data['status'] in ['paid', 'completed', 'failed', 'cancelled']:
                cache.set(cache_key, response_data, 300)  # Cache final statuses for 5 minutes
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error checking payment status for order {order_id}: {str(e)}")
            return Response({
                'error': 'Failed to check payment status',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCancellationView(APIView):
    """
    API endpoint to cancel a payment that's taking too long to process.
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

class PaymentWebhookView(APIView):
    """
    API endpoint to handle payment webhooks from IntaSend.
    """
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access for webhooks
    
    def post(self, request):
        # Log all webhook requests for debugging
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            payload = request.data
            
            # Log webhook receipt
            logger.info(f"Received IntaSend webhook: payload={payload}")
            
            # Handle both old format (event-based) and official IntaSend format (state-based)
            # Official IntaSend format uses direct fields: invoice_id, state, api_ref, etc.
            
            # Check if this is official IntaSend format
            if 'invoice_id' in payload and 'state' in payload:
                # Official IntaSend webhook format
                invoice_id = payload.get('invoice_id')
                state = payload.get('state')
                api_ref = payload.get('api_ref')
                challenge = payload.get('challenge')
                
                logger.info(f"Official IntaSend webhook: invoice_id={invoice_id}, state={state}, api_ref={api_ref}")
                
                if invoice_id:
                    try:
                        payment = Payment.objects.get(intasend_invoice_id=invoice_id)
                        
                        logger.info(f"Processing payment state change for Payment ID: {payment.id}, Order ID: {payment.order.id}")
                        
                        old_status = payment.status
                        
                        # Map IntaSend states to our payment statuses
                        if state == 'COMPLETE':
                            payment.status = 'completed'
                            
                            # Update transaction ID if available (for M-Pesa)
                            if payload.get('account'):  # M-Pesa receipt number
                                payment.transaction_id = payload.get('account')
                            
                            payment.save()
                            logger.info(f"Payment {payment.id} status updated from '{old_status}' to 'completed'")
                            
                            # Update order status to completed when payment is successful
                            order = payment.order
                            if order.status == 'payment_pending':
                                order.status = 'completed'
                                order.completed_at = timezone.now()
                                order.save()
                                logger.info(f"Order {order.id} status updated to 'completed'")

                                # Award loyalty and referral points
                                try:
                                    from accounts.models import WalletTransaction
                                    # 10 points to customer
                                    order.client.profile.wallet_points += 10
                                    order.client.profile.save(update_fields=['wallet_points'])
                                    WalletTransaction.objects.create(
                                        user=order.client,
                                        points=10,
                                        amount_equivalent=10,
                                        transaction_type='earn',
                                        reference=f'order_{order.id}_completed'
                                    )
                                    # 20 points to referrer for each completed errand by referred user
                                    if order.client.referred_by:
                                        referrer = order.client.referred_by
                                        referrer.profile.wallet_points += 20
                                        referrer.profile.save(update_fields=['wallet_points'])
                                        WalletTransaction.objects.create(
                                            user=referrer,
                                            points=20,
                                            amount_equivalent=20,
                                            transaction_type='earn',
                                            reference=f'referral_order_{order.id}_completed'
                                        )
                                except Exception as e:
                                    logger.error(f"Failed to award loyalty/referral points for order {order.id}: {e}")
                            
                            # Handle handyman orders
                            from .models import HandymanOrder
                            try:
                                handyman_order = HandymanOrder.objects.get(order=order)
                                if handyman_order.status == 'quote_approved':
                                    handyman_order.status = 'completed'
                                    handyman_order.completed_at = timezone.now()
                                    handyman_order.final_payment_complete = True
                                    handyman_order.save()
                                    logger.info(f"Handyman order {handyman_order.id} marked as completed")
                            except HandymanOrder.DoesNotExist:
                                pass
                                
                        elif state == 'FAILED':
                            payment.status = 'failed'
                            payment.save()
                            logger.info(f"Payment {payment.id} status updated from '{old_status}' to 'failed'")
                            
                        elif state == 'PROCESSING':
                            payment.status = 'processing'
                            payment.save()
                            logger.info(f"Payment {payment.id} status updated from '{old_status}' to 'processing'")
                            
                        elif state == 'PENDING':
                            payment.status = 'pending'
                            payment.save()
                            logger.info(f"Payment {payment.id} status updated from '{old_status}' to 'pending'")
                            
                    except Payment.DoesNotExist:
                        logger.error(f"Payment with IntaSend invoice ID {invoice_id} not found")
                        pass
            
            # Handle legacy/test format (event-based) for backward compatibility
            elif 'event' in payload:
                event = payload.get('event')
                logger.info(f"Legacy webhook format: event={event}")
                
                if event == 'payment.completed':
                    data = payload.get('data', {})
                    invoice_id = data.get('invoice', {}).get('id')
                    
                    if invoice_id:
                        try:
                            payment = Payment.objects.get(intasend_invoice_id=invoice_id)
                            
                            old_status = payment.status
                            payment.status = 'completed'
                            
                            if data.get('mpesa_receipt'):
                                payment.transaction_id = data.get('mpesa_receipt')
                            
                            payment.save()
                            logger.info(f"Payment {payment.id} status updated from '{old_status}' to 'completed'")
                            
                        except Payment.DoesNotExist:
                            logger.error(f"Payment with IntaSend invoice ID {invoice_id} not found")
                            # Try to handle prepayment-based order creation
                            try:
                                from .models import OrderPrepayment, Order, OrderType, ShoppingItem
                                prepay = OrderPrepayment.objects.filter(intasend_invoice_id=invoice_id).first()
                                if prepay and prepay.status in ['pending', 'processing'] and not prepay.order:
                                    # Mark prepayment as completed
                                    prepay.status = 'completed'
                                    prepay.save(update_fields=['status'])
                                    # Create the actual order now that deposit is paid
                                    order = Order.objects.create(
                                        client=prepay.client,
                                        order_type=prepay.order_type,
                                        title=prepay.title or 'Shopping Order',
                                        description=prepay.description or '',
                                        delivery_address=prepay.delivery_address or '',
                                        delivery_latitude=prepay.delivery_latitude,
                                        delivery_longitude=prepay.delivery_longitude,
                                        status='pending'
                                    )
                                    # Create shopping items if provided
                                    if isinstance(prepay.items, list):
                                        for it in prepay.items:
                                            try:
                                                ShoppingItem.objects.create(
                                                    order=order,
                                                    name=str(it.get('name', 'Item')),
                                                    quantity=int(it.get('quantity', 1)),
                                                    price=float(it.get('price', 0))
                                                )
                                            except Exception:
                                                continue
                                    # Calculate and set price
                                    try:
                                        order.price = order.calculate_price()
                                        order.save(update_fields=['price'])
                                    except Exception:
                                        pass
                                    prepay.order = order
                                    prepay.save(update_fields=['order'])
                                    logger.info(f"Order {order.id} created from prepayment {prepay.transaction_reference}")
                            except Exception as e2:
                                logger.error(f"Failed to create order from prepayment for invoice {invoice_id}: {e2}")
                            pass
                
                elif event in ['payment.failed', 'payment.cancelled']:
                    data = payload.get('data', {})
                    invoice_id = data.get('invoice', {}).get('id')
                    
                    if invoice_id:
                        try:
                            payment = Payment.objects.get(intasend_invoice_id=invoice_id)
                            
                            old_status = payment.status
                            if event == 'payment.cancelled':
                                payment.status = 'cancelled'
                            else:
                                payment.status = 'failed'
                            
                            payment.save()
                            logger.info(f"Payment {payment.id} status updated from '{old_status}' to '{payment.status}'")
                            
                        except Payment.DoesNotExist:
                            logger.error(f"Payment with IntaSend invoice ID {invoice_id} not found for {event} event")
                            # Try to create order for handyman prepayment as well
                            try:
                                from .models import OrderPrepayment, Order, ShoppingItem, HandymanOrder, HandymanServiceType
                                prepay = OrderPrepayment.objects.filter(intasend_invoice_id=invoice_id).first()
                                if prepay and prepay.status in ['pending', 'processing'] and not prepay.order:
                                    prepay.status = 'completed'
                                    prepay.save(update_fields=['status'])
                                    # Create master order
                                    order = Order.objects.create(
                                        client=prepay.client,
                                        order_type=prepay.order_type,
                                        title=prepay.title or 'Handyman Service Request',
                                        description=prepay.description or '',
                                        delivery_address=prepay.delivery_address or '',
                                        delivery_latitude=prepay.delivery_latitude,
                                        delivery_longitude=prepay.delivery_longitude,
                                        status='pending'
                                    )
                                    prepay.order = order
                                    prepay.save(update_fields=['order'])
                                    # If this prepay is for handyman
                                    handyman_payload = None
                                    if isinstance(prepay.items, dict):
                                        handyman_payload = prepay.items.get('handyman')
                                    if handyman_payload:
                                        try:
                                            service_type = HandymanServiceType.objects.get(id=handyman_payload.get('service_type_id'))
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
                                                status='pending'
                                            )
                                        except Exception as e3:
                                            logger.error(f"Failed creating HandymanOrder from prepayment {prepay.transaction_reference}: {e3}")
                            except Exception as e2:
                                logger.error(f"Failed to create order from prepayment for invoice {invoice_id}: {e2}")
                            pass
            
            logger.info(f"Webhook processed successfully")
            return Response({'status': 'success'})
        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)