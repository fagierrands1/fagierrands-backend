"""
M-Pesa Daraja API Payment Views
Replaces IntaSend payment integration
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
from .mpesa_service import mpesa_service
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class InitiatePaymentView(generics.CreateAPIView):
    """
    API endpoint to initiate a payment for an order using M-Pesa
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


class MpesaPaymentView(APIView):
    """
    API endpoint to process a payment through M-Pesa Daraja API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            logger.info(f"Processing M-Pesa payment request for payment ID: {payment_id}")
            
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
                    'message': 'Phone number is required for M-Pesa payment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not mpesa_service.validate_phone_number(payment.phone_number):
                return Response({
                    'status': 'error',
                    'message': 'Invalid phone number format. Please use a valid Kenyan mobile number.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process M-Pesa payment
            return self.process_mpesa_payment(payment)
            
        except Exception as e:
            logger.error(f"Error in MpesaPaymentView.post for payment ID {payment_id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_mpesa_payment(self, payment):
        """
        Process M-Pesa STK Push payment via NCBA
        """
        try:
            logger.info(f"Processing NCBA STK Push for payment ID: {payment.id}")
            
            from .ncba_service import NCBAService
            ncba_service = NCBAService()
            
            # Format phone number
            phone_number = payment.phone_number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # Determine amount to charge (use final_amount if available, otherwise amount)
            amount_to_charge = payment.final_amount if payment.final_amount and payment.final_amount > 0 else payment.amount
            
            logger.info(f"Phone: {phone_number}, Amount: {amount_to_charge}")
            
            # Initiate STK Push via NCBA
            response = ncba_service.initiate_stk_push(
                phone_number=phone_number,
                amount=float(amount_to_charge),
                account_no=f"Order-{payment.order.id}"
            )
            
            logger.info(f"NCBA STK Push response: {json.dumps(response, indent=2)}")
            
            # Check response
            status_code = response.get('StatusCode')
            
            if status_code == '0':
                # Success - STK Push sent
                transaction_id = response.get('TransactionID')
                reference_id = response.get('ReferenceID')
                
                # Update payment with NCBA references
                payment.mpesa_checkout_request_id = transaction_id # Reusing field for TransactionID
                payment.status = 'processing'
                payment.save()
                
                logger.info(f"Payment {payment.id} updated with NCBA references")
                
                return Response({
                    'status': 'success',
                    'message': 'NCBA payment initiated successfully. Please check your phone for the payment prompt.',
                    'data': {
                        'transaction_id': transaction_id,
                        'reference_id': reference_id,
                        'customer_message': response.get('StatusDescription', 'Please check your phone')
                    }
                })
            else:
                # Failed to initiate STK Push
                error_message = response.get('StatusDescription', 'Failed to initiate NCBA payment')
                logger.error(f"NCBA STK Push failed: {error_message}")
                
                payment.status = 'failed'
                payment.save()
                
                return Response({
                    'status': 'error',
                    'message': error_message
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
                'message': f'Failed to process M-Pesa payment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MpesaWebhookHandler:
    """
    Comprehensive M-Pesa webhook handler for all webhook types.
    Handles STK Push callbacks, C2B validations/confirmations, and B2C results.
    Supports both regular payments and prepayments.
    """

    @staticmethod
    def handle_stk_callback(payload):
        """
        Handle M-Pesa STK Push callback for both regular payments and prepayments
        """
        logger.info("=" * 80)
        logger.info("Processing M-Pesa STK Push callback")

        try:
            # Extract callback data
            body = payload.get('Body', {})
            stk_callback = body.get('stkCallback', {})

            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')

            logger.info(f"Merchant Request ID: {merchant_request_id}")
            logger.info(f"Checkout Request ID: {checkout_request_id}")
            logger.info(f"Result Code: {result_code}")
            logger.info(f"Result Description: {result_desc}")

            # Try to find payment by checkout request ID first
            payment = None
            prepayment = None

            try:
                payment = Payment.objects.get(mpesa_checkout_request_id=checkout_request_id)
                logger.info(f"Found regular payment: ID={payment.id}, Order ID={payment.order.id}")
            except Payment.DoesNotExist:
                # Try to find prepayment
                try:
                    prepayment = OrderPrepayment.objects.get(mpesa_checkout_request_id=checkout_request_id)
                    logger.info(f"Found prepayment: ID={prepayment.id}, Transaction Ref={prepayment.transaction_reference}")
                except OrderPrepayment.DoesNotExist:
                    logger.error(f"No payment or prepayment found for CheckoutRequestID: {checkout_request_id}")
                    return {'ResultCode': 0, 'ResultDesc': 'Accepted'}

            # Process based on result code
            if result_code == 0:
                # Payment successful
                logger.info("Payment successful - processing callback metadata")

                # Extract callback metadata
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])

                # Parse metadata
                metadata = {}
                for item in items:
                    name = item.get('Name')
                    value = item.get('Value')
                    metadata[name] = value

                logger.info(f"Callback metadata: {json.dumps(metadata, indent=2)}")

                with db_transaction.atomic():
                    if payment:
                        # Handle regular payment
                        MpesaWebhookHandler._process_regular_payment_success(payment, metadata)
                    elif prepayment:
                        # Handle prepayment
                        MpesaWebhookHandler._process_pre_payment_success(prepayment, metadata, checkout_request_id)

            else:
                # Payment failed or cancelled
                logger.warning(f"Payment failed/cancelled: {result_desc}")
                if payment:
                    payment.status = 'failed'
                    payment.save()
                    logger.info(f"Regular payment {payment.id} marked as failed")
                elif prepayment:
                    prepayment.status = 'failed'
                    prepayment.save()
                    logger.info(f"Prepayment {prepayment.id} marked as failed")

            # Clear cache if we have an order
            if payment and payment.order:
                cache_key = f"payment_status_order_{payment.order.id}_user_{payment.order.client.id}"
                cache.delete(cache_key)

            # Return success response to M-Pesa
            return {'ResultCode': 0, 'ResultDesc': 'Accepted'}

        except Exception as e:
            logger.error(f"Error processing M-Pesa STK callback: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Still return success to M-Pesa to avoid retries
            return {'ResultCode': 0, 'ResultDesc': 'Accepted'}

    @staticmethod
    def _process_regular_payment_success(payment, metadata):
        """Process successful regular payment"""
        payment.status = 'completed'
        payment.transaction_id = metadata.get('MpesaReceiptNumber')
        payment.mpesa_receipt_number = metadata.get('MpesaReceiptNumber')
        payment.mpesa_transaction_date = metadata.get('TransactionDate')
        payment.mpesa_phone_number = metadata.get('PhoneNumber')
        payment.save()

        logger.info(f"Regular payment {payment.id} marked as completed")

        # Update order status
        order = payment.order
        if order.status == 'payment_pending':
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.save()
            logger.info(f"Order {order.id} marked as completed")

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
                logger.info(f"Awarded 10 points to customer {order.client.id}")

                # 20 points to referrer
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
                    logger.info(f"Awarded 20 points to referrer {referrer.id}")
            except Exception as e:
                logger.error(f"Failed to award loyalty/referral points: {e}")

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

    @staticmethod
    def _process_pre_payment_success(prepayment, metadata, checkout_request_id):
        """Process successful prepayment and use existing order if available"""
        prepayment.status = 'completed'
        prepayment.mpesa_receipt_number = metadata.get('MpesaReceiptNumber')
        prepayment.mpesa_checkout_request_id = checkout_request_id
        prepayment.save()

        logger.info(f"Prepayment {prepayment.id} marked as completed")

        # Check if prepayment already has an associated order
        if prepayment.order:
            # Use existing order
            order = prepayment.order
            logger.info(f"Using existing order {order.id} for prepayment {prepayment.transaction_reference}")

            # Update order status to completed since payment is successful
            if order.status == 'payment_pending':
                order.status = 'completed'
                order.completed_at = timezone.now()
                order.save()
                logger.info(f"Order {order.id} marked as completed")

        else:
            # Create the actual order from prepayment data (fallback for legacy prepayments)
            try:
                order = Order.objects.create(
                    client=prepayment.client,
                    order_type=prepayment.order_type,
                    title=prepayment.title or 'Shopping Order',
                    description=prepayment.description or '',
                    delivery_address=prepayment.delivery_address or '',
                    delivery_latitude=prepayment.delivery_latitude,
                    delivery_longitude=prepayment.delivery_longitude,
                    status='completed'  # Order starts as completed since payment succeeded
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
                            logger.info(f"Created shopping item: {item_data.get('name')}")
                        except Exception as e:
                            logger.error(f"Failed to create shopping item: {e}")
                            continue

                # Calculate and set price
                try:
                    order.price = order.calculate_price()
                    order.save(update_fields=['price'])
                    logger.info(f"Order {order.id} price calculated: {order.price}")
                except Exception as e:
                    logger.error(f"Failed to calculate order price: {e}")

                # Link the order back to prepayment
                prepayment.order = order
                prepayment.save(update_fields=['order'])

                logger.info(f"Order {order.id} created from prepayment {prepayment.transaction_reference}")

            except Exception as e:
                logger.error(f"Failed to create order from prepayment {prepayment.id}: {e}")
                # Don't re-raise - prepayment is still marked as completed

    @staticmethod
    def handle_c2b_validation(payload):
        """
        Handle M-Pesa C2B validation request
        Return ResultCode 0 to accept, non-zero to reject
        """
        logger.info("Processing M-Pesa C2B validation request")
        logger.info(f"Validation payload: {json.dumps(payload, indent=2)}")

        # Extract transaction details for validation
        trans_amount = payload.get('TransAmount')
        bill_ref_number = payload.get('BillRefNumber')
        msisdn = payload.get('MSISDN')

        logger.info(f"C2B Validation - Amount: {trans_amount}, Bill Ref: {bill_ref_number}, MSISDN: {msisdn}")

        # Add your validation logic here
        # For example, check if bill_ref_number exists, amount is valid, etc.

        # For now, accept all requests
        return {
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }

    @staticmethod
    def handle_c2b_confirmation(payload):
        """
        Handle M-Pesa C2B confirmation
        """
        logger.info("=" * 80)
        logger.info("Processing M-Pesa C2B confirmation")

        try:
            # Extract payment details
            transaction_type = payload.get('TransactionType')
            trans_id = payload.get('TransID')
            trans_time = payload.get('TransTime')
            trans_amount = payload.get('TransAmount')
            business_short_code = payload.get('BusinessShortCode')
            bill_ref_number = payload.get('BillRefNumber')
            invoice_number = payload.get('InvoiceNumber')
            org_account_balance = payload.get('OrgAccountBalance')
            third_party_trans_id = payload.get('ThirdPartyTransID')
            msisdn = payload.get('MSISDN')
            first_name = payload.get('FirstName')
            middle_name = payload.get('MiddleName')
            last_name = payload.get('LastName')

            logger.info(f"C2B Transaction ID: {trans_id}")
            logger.info(f"Amount: {trans_amount}")
            logger.info(f"Bill Ref: {bill_ref_number}")
            logger.info(f"Phone: {msisdn}")

            # Try to find payment by transaction reference (bill_ref_number)
            try:
                payment = Payment.objects.get(transaction_reference=bill_ref_number)
                logger.info(f"Found payment: ID={payment.id}, Order ID={payment.order.id}")

                # Update payment
                with db_transaction.atomic():
                    payment.status = 'completed'
                    payment.transaction_id = trans_id
                    payment.mpesa_receipt_number = trans_id
                    payment.mpesa_transaction_date = trans_time
                    payment.mpesa_phone_number = msisdn
                    payment.save()

                    logger.info(f"Payment {payment.id} marked as completed")

                    # Update order
                    order = payment.order
                    if order.status == 'payment_pending':
                        order.status = 'completed'
                        order.completed_at = timezone.now()
                        order.save()
                        logger.info(f"Order {order.id} marked as completed")

            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for Bill Ref: {bill_ref_number}")

            # Return success response
            return {
                'ResultCode': 0,
                'ResultDesc': 'Accepted'
            }

        except Exception as e:
            logger.error(f"Error processing C2B confirmation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Still return success to avoid retries
            return {
                'ResultCode': 0,
                'ResultDesc': 'Accepted'
            }

    @staticmethod
    def handle_b2c_result(payload):
        """
        Handle M-Pesa B2C result callback
        """
        logger.info("=" * 80)
        logger.info("Processing M-Pesa B2C result")
        logger.info(f"B2C result payload: {json.dumps(payload, indent=2)}")

        # Process B2C result
        # This would be used for payouts to assistants/handlers
        # Add your B2C result processing logic here

        return {
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }

    @staticmethod
    def handle_b2c_timeout(payload):
        """
        Handle M-Pesa B2C timeout callback
        """
        logger.info("Processing M-Pesa B2C timeout")
        logger.info(f"B2C timeout payload: {json.dumps(payload, indent=2)}")

        # Process B2C timeout
        # Add your B2C timeout processing logic here

        return {
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }


class MpesaSTKCallbackView(APIView):
    """
    API endpoint to handle M-Pesa STK Push callbacks
    """
    permission_classes = [permissions.AllowAny]  # M-Pesa callbacks are unauthenticated

    def head(self, request, *args, **kwargs):
        """Respond to HEAD requests for callback URL validation probes."""
        return Response(status=status.HTTP_200_OK)

    def post(self, request):
        """
        Handle M-Pesa STK Push callback using the comprehensive handler
        """
        response = MpesaWebhookHandler.handle_stk_callback(request.data)
        return Response(response)


class MpesaC2BValidationView(APIView):
    """
    API endpoint to handle M-Pesa C2B validation requests
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Validate C2B payment request
        Return ResultCode 0 to accept, non-zero to reject
        """
        logger.info("Received M-Pesa C2B validation request")
        logger.info(f"Validation payload: {json.dumps(request.data, indent=2)}")
        
        # You can add validation logic here
        # For now, accept all requests
        
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        })


class MpesaC2BConfirmationView(APIView):
    """
    API endpoint to handle M-Pesa C2B confirmation requests
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Handle C2B payment confirmation
        """
        logger.info("=" * 80)
        logger.info("Received M-Pesa C2B confirmation")
        
        try:
            payload = request.data
            logger.info(f"Confirmation payload: {json.dumps(payload, indent=2)}")
            
            # Extract payment details
            transaction_type = payload.get('TransactionType')
            trans_id = payload.get('TransID')
            trans_time = payload.get('TransTime')
            trans_amount = payload.get('TransAmount')
            business_short_code = payload.get('BusinessShortCode')
            bill_ref_number = payload.get('BillRefNumber')
            invoice_number = payload.get('InvoiceNumber')
            org_account_balance = payload.get('OrgAccountBalance')
            third_party_trans_id = payload.get('ThirdPartyTransID')
            msisdn = payload.get('MSISDN')
            first_name = payload.get('FirstName')
            middle_name = payload.get('MiddleName')
            last_name = payload.get('LastName')
            
            logger.info(f"Transaction ID: {trans_id}")
            logger.info(f"Amount: {trans_amount}")
            logger.info(f"Bill Ref: {bill_ref_number}")
            logger.info(f"Phone: {msisdn}")
            
            # Try to find payment by transaction reference (bill_ref_number)
            # Bill ref number should match payment.transaction_reference
            try:
                payment = Payment.objects.get(transaction_reference=bill_ref_number)
                logger.info(f"Found payment: ID={payment.id}, Order ID={payment.order.id}")
                
                # Update payment
                with db_transaction.atomic():
                    payment.status = 'completed'
                    payment.transaction_id = trans_id
                    payment.mpesa_receipt_number = trans_id
                    payment.mpesa_transaction_date = trans_time
                    payment.mpesa_phone_number = msisdn
                    payment.save()
                    
                    logger.info(f"Payment {payment.id} marked as completed")
                    
                    # Update order
                    order = payment.order
                    if order.status == 'payment_pending':
                        order.status = 'completed'
                        order.completed_at = timezone.now()
                        order.save()
                        logger.info(f"Order {order.id} marked as completed")
                
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for Bill Ref: {bill_ref_number}")
            
            # Return success response
            return Response({
                'ResultCode': 0,
                'ResultDesc': 'Accepted'
            })
            
        except Exception as e:
            logger.error(f"Error processing C2B confirmation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Still return success to avoid retries
            return Response({
                'ResultCode': 0,
                'ResultDesc': 'Accepted'
            })


class MpesaB2CResultView(APIView):
    """
    API endpoint to handle M-Pesa B2C result callbacks
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Handle B2C payment result
        """
        logger.info("=" * 80)
        logger.info("Received M-Pesa B2C result")
        logger.info(f"B2C result payload: {json.dumps(request.data, indent=2)}")
        
        # Process B2C result
        # This would be used for payouts to assistants/handlers
        
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        })


class MpesaB2CTimeoutView(APIView):
    """
    API endpoint to handle M-Pesa B2C timeout callbacks
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Handle B2C payment timeout
        """
        logger.info("Received M-Pesa B2C timeout")
        logger.info(f"B2C timeout payload: {json.dumps(request.data, indent=2)}")
        
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        })


class OrderPaymentStatusView(APIView):
    """
    API endpoint to check payment status for a specific order
    Optimized for frontend polling with better performance and caching
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
                    'mpesa_checkout_request_id': payment.mpesa_checkout_request_id,
                    'mpesa_receipt_number': payment.mpesa_receipt_number,
                }
                
                # Add processing time information
                if payment.status == 'processing' and payment.mpesa_checkout_request_id:
                    # Trigger a background check or do it synchronously if not checked recently
                    last_query_key = f"ncba_query_last_checked_{payment.id}"
                    if not cache.get(last_query_key):
                        try:
                            from .ncba_service import NCBAService
                            ncba_service = NCBAService()
                            query_resp = ncba_service.stk_query(payment.mpesa_checkout_request_id)
                            
                            # NCBA Response: {"status": "SUCCESS", "description": "Success"}
                            ncba_status = query_resp.get('status')
                            if ncba_status == 'SUCCESS':
                                with db_transaction.atomic():
                                    payment.status = 'completed'
                                    payment.save()
                                    
                                    # Update order if needed
                                    order = payment.order
                                    if order.status == 'payment_pending':
                                        order.status = 'completed'
                                        order.completed_at = timezone.now()
                                        order.save()
                                    
                                    payment_data['status'] = 'completed'
                            elif ncba_status == 'FAILED':
                                payment.status = 'failed'
                                payment.save()
                                payment_data['status'] = 'failed'
                                
                            # Cache the fact that we checked for 5 seconds
                            cache.set(last_query_key, True, 5)
                        except Exception as e:
                            logger.error(f"Failed to query NCBA status: {str(e)}")

                    processing_time = timezone.now() - payment.updated_at
                    payment_data['processing_duration_seconds'] = int(processing_time.total_seconds())
                    
                    # If processing for more than 5 minutes, mark as potentially stuck
                    if processing_time.total_seconds() > 300:
                        payment_data['potentially_stuck'] = True
                
                response_data = {
                    'order_id': order.id,
                    'order_status': order.status,
                    'payment': payment_data,
                    'has_payment': True,
                    'payment_type': 'regular'
                }
                
                # Cache the response for 10 seconds
                cache.set(cache_key, response_data, 10)
                
                return Response(response_data)
                
            except Payment.DoesNotExist:
                # Try to check for OrderPrepayment (Shopping orders)
                try:
                    prepayment = OrderPrepayment.objects.filter(order=order).latest('created_at')
                    prepayment_data = {
                        'id': prepayment.id,
                        'status': prepayment.status,
                        'amount': str(prepayment.deposit_amount),
                        'payment_method': prepayment.payment_method,
                        'transaction_reference': prepayment.transaction_reference,
                        'created_at': prepayment.created_at.isoformat(),
                        'updated_at': prepayment.updated_at.isoformat(),
                        'mpesa_checkout_request_id': prepayment.mpesa_checkout_request_id,
                    }

                    # Add NCBA polling for prepayment
                    if prepayment.status == 'processing' and prepayment.mpesa_checkout_request_id:
                        last_query_key = f"ncba_query_last_checked_prepay_{prepayment.id}"
                        if not cache.get(last_query_key):
                            try:
                                from .ncba_service import NCBAService
                                ncba_service = NCBAService()
                                query_resp = ncba_service.stk_query(prepayment.mpesa_checkout_request_id)
                                
                                ncba_status = query_resp.get('status')
                                if ncba_status == 'SUCCESS':
                                    with db_transaction.atomic():
                                        prepayment.status = 'completed'
                                        prepayment.save()
                                        
                                        # Shopping orders might need specific logic when deposit is paid
                                        # but typically the order status remains unchanged or moves to next stage
                                        prepayment_data['status'] = 'completed'
                                elif ncba_status == 'FAILED':
                                    prepayment.status = 'failed'
                                    prepayment.save()
                                    prepayment_data['status'] = 'failed'
                                    
                                cache.set(last_query_key, True, 5)
                            except Exception as e:
                                logger.error(f"Failed to query NCBA status for prepayment: {str(e)}")

                    response_data = {
                        'order_id': order.id,
                        'order_status': order.status,
                        'payment': prepayment_data,
                        'has_payment': True,
                        'payment_type': 'prepayment'
                    }
                    
                    cache.set(cache_key, response_data, 10)
                    return Response(response_data)

                except OrderPrepayment.DoesNotExist:
                    response_data = {
                        'order_id': order.id,
                        'order_status': order.status,
                        'has_payment': False,
                        'message': 'No payment or prepayment found for this order'
                    }
                    
                    # Cache for shorter time if no payment
                    cache.set(cache_key, response_data, 5)
                    
                    return Response(response_data)
                
        except Exception as e:
            logger.error(f"Error checking payment status for order {order_id}: {str(e)}")
            return Response({
                'error': 'Failed to check payment status',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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