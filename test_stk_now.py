#!/usr/bin/env python
"""
STK Push Test - Real Time
Tests STK push with your actual phone number
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.mpesa_service import MpesaDarajaService
import json

def test_stk_push():
    """Test STK push with your phone number"""
    
    # Your phone number
    phone = '254758292353'  # Replace with your actual phone number for testing
    amount = 1  # KES 1 - minimal amount for testing
    account_ref = 'TEST123'
    description = 'Test STK Push'
    
    print('\n' + '='*70)
    print('🔔 STK PUSH TEST - REAL PHONE')
    print('='*70)
    print(f'📱 Phone Number: {phone}')
    print(f'💰 Amount: KES {amount}')
    print(f'📝 Description: {description}')
    print('='*70 + '\n')
    
    try:
        mpesa = MpesaDarajaService()
        
        print('⏳ Sending STK push to your phone...\n')
        result = mpesa.stk_push(phone, amount, account_ref, description)
        
        print('📋 Response:')
        print('-'*70)
        print(json.dumps(result, indent=2))
        print('-'*70 + '\n')
        
        # Check response
        if result.get('ResponseCode') == '0':
            print('✅ SUCCESS! Your phone should show the M-Pesa prompt now.')
            print(f'\n📌 Checkout Request ID: {result.get("CheckoutRequestID")}')
            print('\n💡 Next steps:')
            print('   1. Check your phone for the M-Pesa popup')
            print('   2. Enter your M-Pesa PIN')
            print('   3. Transaction will complete (or ask for additional verification)')
            
            checkout_id = result.get("CheckoutRequestID")
            if checkout_id:
                print(f'\n🔍 You can check status with: {checkout_id}')
        else:
            error_msg = result.get('ResponseDescription', 'Unknown error')
            response_code = result.get('ResponseCode', 'N/A')
            print(f'❌ Failed with code {response_code}')
            print(f'❌ Error: {error_msg}')
            
            # Common error codes
            error_guide = {
                '1': 'Insufficient balance',
                '8': 'System timeout - please retry',
                '27': 'The initiator must be allowed to pay themselves',
                '201': 'Invalid phone number format',
                '5001': 'Bad Request',
            }
            
            if response_code in error_guide:
                print(f'💡 Hint: {error_guide[response_code]}')
        
        return result
        
    except Exception as e:
        print(f'❌ Exception occurred: {str(e)}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = test_stk_push()
    
    print('\n' + '='*70)
    if result and result.get('ResponseCode') == '0':
        print('✅ Test completed successfully!')
    else:
        print('❌ Test failed or encountered an error')
    print('='*70 + '\n')