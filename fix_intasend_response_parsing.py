#!/usr/bin/env python
"""
Fix IntaSend Response Parsing Issue
The issue is that IntaSend API response format might be different than expected
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

def analyze_intasend_response_format():
    """Analyze the expected vs actual IntaSend response format"""
    
    print("🔍 IntaSend API Response Format Analysis")
    print("=" * 50)
    
    print("📊 Current Code Expects:")
    print("-" * 25)
    print("response = {")
    print("  'id': 'checkout_id',")
    print("  'invoice': {")
    print("    'id': 'invoice_id',")
    print("    'state': 'PENDING'")
    print("  }")
    print("}")
    
    print("\n🔍 Possible Actual Response Formats:")
    print("-" * 35)
    
    print("Format 1 (Current expectation):")
    print("response.get('invoice', {}).get('id')  # Gets invoice ID")
    print("response.get('invoice', {}).get('state')  # Gets state")
    
    print("\nFormat 2 (Direct invoice_id):")
    print("response.get('invoice_id')  # Direct invoice ID")
    print("response.get('state')  # Direct state")
    
    print("\nFormat 3 (Different nesting):")
    print("response.get('data', {}).get('invoice_id')")
    print("response.get('data', {}).get('state')")
    
    print("\n🔧 Enhanced Response Parsing:")
    print("-" * 30)
    
    enhanced_parsing_code = '''
def get_invoice_id_from_response(response):
    """Enhanced invoice ID extraction from IntaSend response"""
    
    # Try multiple possible locations for invoice ID
    invoice_id = None
    
    # Method 1: Nested invoice object (current)
    if response.get('invoice', {}).get('id'):
        invoice_id = response.get('invoice', {}).get('id')
    
    # Method 2: Direct invoice_id field
    elif response.get('invoice_id'):
        invoice_id = response.get('invoice_id')
    
    # Method 3: In data object
    elif response.get('data', {}).get('invoice_id'):
        invoice_id = response.get('data', {}).get('invoice_id')
    
    # Method 4: In invoice object with different key
    elif response.get('invoice', {}).get('invoice_id'):
        invoice_id = response.get('invoice', {}).get('invoice_id')
    
    return invoice_id

def get_state_from_response(response):
    """Enhanced state extraction from IntaSend response"""
    
    # Try multiple possible locations for state
    state = None
    
    # Method 1: Nested invoice object (current)
    if response.get('invoice', {}).get('state'):
        state = response.get('invoice', {}).get('state')
    
    # Method 2: Direct state field
    elif response.get('state'):
        state = response.get('state')
    
    # Method 3: In data object
    elif response.get('data', {}).get('state'):
        state = response.get('data', {}).get('state')
    
    # Method 4: Status field instead of state
    elif response.get('status'):
        state = response.get('status')
    
    return state
'''
    
    print(enhanced_parsing_code)
    
    print("\n🎯 Recommended Fix:")
    print("-" * 20)
    print("1. Add enhanced response parsing to handle multiple formats")
    print("2. Add detailed logging of actual IntaSend responses")
    print("3. Test with small amount to see actual response format")
    print("4. Update the payment processing code")

def create_enhanced_payment_processing():
    """Create enhanced payment processing with better response handling"""
    
    enhanced_code = '''
def process_mpesa_payment(self, payment):
    """Enhanced M-Pesa payment processing with robust response handling"""
    try:
        logger.info(f"Processing M-Pesa payment for payment ID: {payment.id}")
        
        # Initialize IntaSend API service
        api_service = APIService(
            token=INTASEND_SECRET_KEY,
            publishable_key=INTASEND_PUBLISHABLE_KEY,
            test=INTASEND_TEST_MODE
        )
        
        # Format phone number
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
        
        # ENHANCED: Extract invoice ID using multiple methods
        invoice_id = self.get_invoice_id_from_response(response)
        state = self.get_state_from_response(response)
        checkout_id = response.get('id') or response.get('checkout_id')
        
        logger.info(f"Extracted - Invoice ID: {invoice_id}, State: {state}, Checkout ID: {checkout_id}")
        
        # Check if STK Push was successful
        if state in ['PENDING', 'PROCESSING', 'pending', 'processing']:
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
        logger.error(f"Error processing M-Pesa payment: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        payment.status = 'failed'
        payment.save()
        
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_invoice_id_from_response(self, response):
    """Enhanced invoice ID extraction"""
    return (
        response.get('invoice', {}).get('id') or
        response.get('invoice_id') or
        response.get('data', {}).get('invoice_id') or
        response.get('invoice', {}).get('invoice_id')
    )

def get_state_from_response(self, response):
    """Enhanced state extraction"""
    return (
        response.get('invoice', {}).get('state') or
        response.get('state') or
        response.get('data', {}).get('state') or
        response.get('status')
    )
'''
    
    return enhanced_code

if __name__ == '__main__':
    analyze_intasend_response_format()
    
    print(f"\n💡 Immediate Actions:")
    print("-" * 20)
    print("1. 🔧 Update payment processing with enhanced response parsing")
    print("2. 📊 Test with small payment to see actual IntaSend response")
    print("3. 🔗 Configure webhook in IntaSend dashboard")
    print("4. 📝 Add detailed logging for debugging")
    
    print(f"\n🎯 Root Cause of Your Issue:")
    print("-" * 30)
    print("❌ IntaSend API returned response in different format than expected")
    print("❌ Invoice ID was not extracted properly (returned None)")
    print("❌ Without invoice ID, webhook cannot match the payment")
    print("❌ Payment gets stuck in 'processing' status forever")
    
    print(f"\n✅ Solution:")
    print("-" * 10)
    print("1. Enhanced response parsing (handles multiple formats)")
    print("2. Better error logging (see actual response format)")
    print("3. Webhook configuration (for automatic updates)")
    print("4. Fallback handling (graceful failure recovery)")