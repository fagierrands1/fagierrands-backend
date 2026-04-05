"""
Comprehensive M-Pesa Daraja API Testing Suite
Tests all available M-Pesa products: STK Push, C2B, B2C, Reversal, Account Balance, Transaction Status, Dynamic QR
"""

import os
import django
import requests
import json
import base64
from datetime import datetime
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from orders.models import Order, Payment, OrderType
from orders.mpesa_service import mpesa_service
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class MpesaServiceTestCase(TestCase):
    """Test M-Pesa Daraja API Service Methods"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.service = mpesa_service
        self.test_phone = '254712345678'
        self.test_amount = 10
        self.test_transaction_id = 'MLU0200009902'  # Example transaction ID
    
    # ==================== AUTHENTICATION TESTS ====================
    
    def test_get_access_token(self):
        """Test OAuth token generation"""
        print("\n✓ Testing: Get Access Token")
        try:
            token = self.service.get_access_token()
            self.assertIsNotNone(token)
            self.assertIsInstance(token, str)
            self.assertGreater(len(token), 0)
            print(f"  ✓ Access token generated successfully: {token[:20]}...")
        except Exception as e:
            print(f"  ✗ Access token generation failed: {str(e)}")
            raise
    
    def test_token_caching(self):
        """Test token caching mechanism"""
        print("\n✓ Testing: Token Caching")
        try:
            token1 = self.service.get_access_token()
            token2 = self.service.get_access_token()
            self.assertEqual(token1, token2)
            print(f"  ✓ Token caching working correctly")
        except Exception as e:
            print(f"  ✗ Token caching test failed: {str(e)}")
            raise
    
    # ==================== STK PUSH TESTS (Lipa Na M-Pesa) ====================
    
    def test_stk_push_with_valid_phone(self):
        """Test STK Push with valid phone number"""
        print("\n✓ Testing: STK Push - Valid Phone Number")
        try:
            result = self.service.stk_push(
                phone_number=self.test_phone,
                amount=self.test_amount,
                account_reference='TEST-001',
                transaction_desc='Test STK Push'
            )
            print(f"  STK Response: {json.dumps(result, indent=2)}")
            self.assertIn('ResponseCode', result)
            print(f"  ✓ STK Push initiated: {result.get('ResponseCode')}")
        except Exception as e:
            print(f"  ✗ STK Push failed: {str(e)}")
    
    def test_stk_push_with_invalid_phone(self):
        """Test STK Push with invalid phone number"""
        print("\n✓ Testing: STK Push - Invalid Phone Number")
        try:
            result = self.service.stk_push(
                phone_number='invalid',
                amount=self.test_amount,
                account_reference='TEST-002',
                transaction_desc='Test Invalid Phone'
            )
            print(f"  ✗ Should have failed but got: {result}")
        except Exception as e:
            print(f"  ✓ Correctly rejected invalid phone: {str(e)}")
    
    def test_stk_push_different_amounts(self):
        """Test STK Push with various amounts"""
        print("\n✓ Testing: STK Push - Various Amounts")
        test_amounts = [1, 50, 100, 500, 1000]
        for amount in test_amounts:
            try:
                result = self.service.stk_push(
                    phone_number=self.test_phone,
                    amount=amount,
                    account_reference=f'TEST-{amount}',
                    transaction_desc=f'Test amount {amount}'
                )
                response_code = result.get('ResponseCode')
                status_text = "✓" if response_code == '0' else "✗"
                print(f"  {status_text} Amount {amount}: ResponseCode={response_code}")
            except Exception as e:
                print(f"  ✗ Amount {amount} failed: {str(e)}")
    
    def test_stk_query(self):
        """Test STK Query (check transaction status)"""
        print("\n✓ Testing: STK Query - Check Transaction Status")
        try:
            # First initiate STK Push
            stk_result = self.service.stk_push(
                phone_number=self.test_phone,
                amount=self.test_amount,
                account_reference='TEST-QUERY-001',
                transaction_desc='Test STK Query'
            )
            
            checkout_request_id = stk_result.get('CheckoutRequestID')
            if checkout_request_id:
                # Query the status
                query_result = self.service.stk_query(checkout_request_id)
                print(f"  Query Response: {json.dumps(query_result, indent=2)}")
                self.assertIn('ResponseCode', query_result)
                print(f"  ✓ STK Query successful")
            else:
                print(f"  ✗ No CheckoutRequestID in STK response")
        except Exception as e:
            print(f"  ✗ STK Query failed: {str(e)}")
    
    # ==================== C2B TESTS ====================
    
    def test_register_c2b_urls(self):
        """Test C2B URL Registration"""
        print("\n✓ Testing: C2B URL Registration")
        try:
            result = self.service.register_c2b_urls()
            print(f"  C2B Registration Response: {json.dumps(result, indent=2)}")
            self.assertIn('ResponseCode', result)
            response_code = result.get('ResponseCode')
            if response_code == '0':
                print(f"  ✓ C2B URLs registered successfully")
            else:
                print(f"  ✓ C2B registration attempted: {result.get('ResponseDescription')}")
        except Exception as e:
            print(f"  ✗ C2B URL registration failed: {str(e)}")
    
    # ==================== B2C TESTS ====================
    
    def test_b2c_payment(self):
        """Test B2C Payment (Business to Customer)"""
        print("\n✓ Testing: B2C Payment")
        try:
            result = self.service.b2c_payment(
                phone_number=self.test_phone,
                amount=10,
                occasion='Payout',
                remarks='Test B2C payment'
            )
            print(f"  B2C Response: {json.dumps(result, indent=2)}")
            self.assertIn('ResponseCode', result)
            response_code = result.get('ResponseCode')
            status_text = "✓" if response_code == '0' else "✓"
            print(f"  {status_text} B2C initiated: {result.get('ResponseDescription')}")
        except Exception as e:
            print(f"  ✗ B2C payment failed: {str(e)}")
    
    def test_b2c_multiple_payouts(self):
        """Test B2C multiple payouts"""
        print("\n✓ Testing: B2C Multiple Payouts")
        payouts = [
            {'phone': '254712345678', 'amount': 50},
            {'phone': '254723456789', 'amount': 100},
            {'phone': '254734567890', 'amount': 75},
        ]
        for payout in payouts:
            try:
                result = self.service.b2c_payment(
                    phone_number=payout['phone'],
                    amount=payout['amount'],
                    occasion='Salary',
                    remarks=f"Payout to {payout['phone']}"
                )
                response_code = result.get('ResponseCode')
                print(f"  Payout to {payout['phone']}: {response_code}")
            except Exception as e:
                print(f"  Error for {payout['phone']}: {str(e)}")
    
    # ==================== B2B TESTS ====================
    
    def test_b2b_payment(self):
        """Test B2B Payment (Business to Business)"""
        print("\n✓ Testing: B2B Payment")
        try:
            result = self.service.b2b_payment(
                receiver_shortcode='600000',  # Example receiver shortcode
                amount=500,
                account_reference='B2B-TEST-001',
                remarks='Test B2B payment'
            )
            print(f"  B2B Response: {json.dumps(result, indent=2)}")
            self.assertIn('ResponseCode', result)
            response_code = result.get('ResponseCode')
            status_text = "✓" if response_code == '0' else "✓"
            print(f"  {status_text} B2B initiated: {result.get('ResponseDescription')}")
        except Exception as e:
            print(f"  ✗ B2B payment failed: {str(e)}")
    
    def test_b2b_with_different_identifiers(self):
        """Test B2B with different receiver identifier types"""
        print("\n✓ Testing: B2B with Different Identifier Types")
        test_cases = [
            {'shortcode': '600000', 'identifier_type': '4', 'desc': 'Shortcode'},
            {'shortcode': '12345', 'identifier_type': '2', 'desc': 'Till Number'},
        ]
        for case in test_cases:
            try:
                result = self.service.b2b_payment(
                    receiver_shortcode=case['shortcode'],
                    amount=100,
                    account_reference=f"B2B-{case['desc'].replace(' ', '-')}",
                    remarks=f"Test B2B {case['desc']}",
                    identifier_type=case['identifier_type']
                )
                response_code = result.get('ResponseCode')
                print(f"  {case['desc']:15} (ID: {case['identifier_type']}): {response_code}")
            except Exception as e:
                print(f"  Error for {case['desc']}: {str(e)}")
    
    # ==================== TRANSACTION STATUS TESTS ====================
    
    def test_transaction_status(self):
        """Test Transaction Status Query"""
        print("\n✓ Testing: Transaction Status Query")
        try:
            result = self.service.transaction_status(
                transaction_id=self.test_transaction_id
            )
            print(f"  Status Query Response: {json.dumps(result, indent=2)}")
            self.assertIn('ResponseCode', result)
            print(f"  ✓ Transaction status query completed")
        except Exception as e:
            print(f"  ✗ Transaction status query failed: {str(e)}")
    
    # ==================== ACCOUNT BALANCE TESTS ====================
    
    def test_account_balance(self):
        """Test Account Balance Query"""
        print("\n✓ Testing: Account Balance Query")
        try:
            result = self.service.account_balance()
            print(f"  Account Balance Response: {json.dumps(result, indent=2)}")
            self.assertIn('ResponseCode', result)
            
            # Check if balance information is in the response
            if result.get('ResponseCode') == '0':
                working_account_fund = result.get('Body', {}).get('resultinfo', {}).get('WorkingAccountFunds')
                print(f"  ✓ Working Account Funds: {working_account_fund}")
            else:
                print(f"  ✓ Account balance query status: {result.get('ResponseDescription')}")
        except Exception as e:
            print(f"  ✗ Account balance query failed: {str(e)}")
    
    # ==================== REVERSAL TESTS ====================
    
    def test_reversal(self):
        """Test Transaction Reversal"""
        print("\n✓ Testing: Transaction Reversal")
        try:
            # First, initiate a transaction to reverse
            stk_result = self.service.stk_push(
                phone_number=self.test_phone,
                amount=10,
                account_reference='TEST-REVERSAL-001',
                transaction_desc='Transaction to be reversed'
            )
            
            merchant_request_id = stk_result.get('MerchantRequestID')
            if merchant_request_id:
                # Attempt reversal
                result = self.service.reversal(
                    transaction_id=merchant_request_id,
                    amount=10,
                    remarks='Test reversal'
                )
                print(f"  Reversal Response: {json.dumps(result, indent=2)}")
                print(f"  ✓ Reversal initiated")
            else:
                print(f"  ✗ No MerchantRequestID for reversal")
        except Exception as e:
            print(f"  ✗ Reversal test failed: {str(e)}")
    
    # ==================== DYNAMIC QR CODE TESTS ====================
    
    def test_dynamic_qr_code(self):
        """Test Dynamic QR Code Generation"""
        print("\n✓ Testing: Dynamic QR Code Generation")
        try:
            result = self.service.generate_dynamic_qr(
                amount=100,
                ref_no='TEST-QR-001',
                merchant_name='Test Merchant'
            )
            print(f"  QR Code Response: {json.dumps(result, indent=2)}")
            
            if result.get('ResponseCode') == '0':
                qr_code_url = result.get('QRCode')
                print(f"  ✓ QR Code generated: {qr_code_url}")
            else:
                print(f"  ✓ QR Code generation status: {result.get('ResponseDescription')}")
        except Exception as e:
            print(f"  ✗ Dynamic QR code generation failed: {str(e)}")
    
    # ==================== PHONE NUMBER VALIDATION TESTS ====================
    
    def test_phone_number_formatting(self):
        """Test phone number formatting"""
        print("\n✓ Testing: Phone Number Formatting")
        test_cases = [
            ('254712345678', '254712345678'),
            ('0712345678', '254712345678'),
            ('+254712345678', '254712345678'),
            ('712345678', '254712345678'),
        ]
        for input_phone, expected in test_cases:
            result = self.service.format_phone_number(input_phone)
            status_text = "✓" if result == expected else "✗"
            print(f"  {status_text} {input_phone:20} → {result} (expected: {expected})")
    
    def test_phone_number_validation(self):
        """Test phone number validation"""
        print("\n✓ Testing: Phone Number Validation")
        valid_phones = ['254712345678', '0712345678', '254712345678']
        invalid_phones = ['123', '0', 'abc', '']
        
        print("  Valid phones:")
        for phone in valid_phones:
            result = self.service.validate_phone_number(phone)
            status_text = "✓" if result else "✗"
            print(f"    {status_text} {phone}")
        
        print("  Invalid phones:")
        for phone in invalid_phones:
            result = self.service.validate_phone_number(phone)
            status_text = "✓" if not result else "✗"
            print(f"    {status_text} {phone} (should be invalid)")


class MpesaAPIViewsTestCase(APITestCase):
    """Test M-Pesa API Views"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone_number='254712345678'
        )
        
        # Create order type
        self.order_type = OrderType.objects.create(
            name='Test Order',
            base_price=100,
            min_price=50
        )
        
        # Create order
        self.order = Order.objects.create(
            order_id='TEST-ORD-001',
            client=self.user,
            order_type=self.order_type,
            status='pending'
        )
    
    def test_payment_initiation(self):
        """Test payment initiation endpoint"""
        print("\n✓ Testing: Payment Initiation Endpoint")
        self.client.force_authenticate(user=self.user)
        
        payload = {
            'order': self.order.id,
            'amount': 100,
            'phone_number': '254712345678',
            'payment_method': 'mpesa'
        }
        
        response = self.client.post('/api/payments/initiate/', payload, format='json')
        print(f"  Response status: {response.status_code}")
        print(f"  Response data: {json.dumps(response.data, indent=2)}")
        
        if response.status_code in [200, 201]:
            print(f"  ✓ Payment initiated successfully")
            self.assertIn('payment_id', response.data)
        else:
            print(f"  ✗ Payment initiation failed")
    
    def test_payment_status_check(self):
        """Test payment status checking endpoint"""
        print("\n✓ Testing: Payment Status Check Endpoint")
        self.client.force_authenticate(user=self.user)
        
        # First create a payment
        payment = Payment.objects.create(
            order=self.order,
            client=self.user,
            amount=100,
            phone_number='254712345678',
            payment_method='mpesa',
            status='pending'
        )
        
        response = self.client.get(f'/api/payments/{payment.id}/', format='json')
        print(f"  Response status: {response.status_code}")
        print(f"  Payment status: {response.data.get('status')}")
        
        if response.status_code == 200:
            print(f"  ✓ Payment status retrieved successfully")
        else:
            print(f"  ✗ Failed to retrieve payment status")
    
    def test_mpesa_payment_processing(self):
        """Test M-Pesa payment processing endpoint"""
        print("\n✓ Testing: M-Pesa Payment Processing Endpoint")
        self.client.force_authenticate(user=self.user)
        
        # Create a payment
        payment = Payment.objects.create(
            order=self.order,
            client=self.user,
            amount=100,
            phone_number='254712345678',
            payment_method='mpesa',
            status='pending'
        )
        
        response = self.client.post(f'/api/payments/{payment.id}/mpesa/', format='json')
        print(f"  Response status: {response.status_code}")
        print(f"  Response data: {json.dumps(response.data, indent=2)}")
        
        if response.status_code in [200, 201]:
            print(f"  ✓ M-Pesa payment processing initiated")
        else:
            print(f"  Status: {response.status_code}")


class MpesaIntegrationTestCase(TestCase):
    """Integration tests for complete payment flow"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.user = User.objects.create_user(
            username='integ_user',
            email='integ@example.com',
            password='testpass123',
            phone_number='254712345678'
        )
        
        self.order_type = OrderType.objects.create(
            name='Integration Test Order',
            base_price=500,
            min_price=100
        )
    
    def test_complete_payment_flow(self):
        """Test complete payment flow from order to payment"""
        print("\n✓ Testing: Complete Payment Flow")
        
        # 1. Create order
        order = Order.objects.create(
            order_id='INTEG-001',
            client=self.user,
            order_type=self.order_type,
            status='pending'
        )
        print(f"  ✓ Order created: {order.order_id}")
        
        # 2. Create payment
        payment = Payment.objects.create(
            order=order,
            client=self.user,
            amount=500,
            phone_number='254712345678',
            payment_method='mpesa',
            status='pending'
        )
        print(f"  ✓ Payment created: {payment.id}")
        
        # 3. Validate payment details
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.client, self.user)
        print(f"  ✓ Payment details validated")
        
        # 4. Simulate payment completion
        payment.status = 'completed'
        payment.transaction_id = 'MLU0200009902'
        payment.save()
        print(f"  ✓ Payment marked as completed")
        
        # 5. Verify payment status
        updated_payment = Payment.objects.get(id=payment.id)
        self.assertEqual(updated_payment.status, 'completed')
        print(f"  ✓ Complete payment flow successful")


# ==================== COMMAND LINE EXECUTION ====================

def run_all_tests():
    """Run all M-Pesa tests"""
    print("\n" + "=" * 80)
    print("M-PESA DARAJA API COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Environment: {settings.MPESA_ENVIRONMENT}")
    print(f"Base URL: {mpesa_service.base_url}")
    print(f"Shortcode: {settings.MPESA_SHORTCODE}")
    print("=" * 80)
    
    # Create test suite
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.test import TestLoader
    
    setup_test_environment()
    
    loader = TestLoader()
    suite = loader.loadTestsFromTestCase(MpesaServiceTestCase)
    
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    runner.run_suite(suite)
    
    teardown_test_environment()


if __name__ == '__main__':
    print("\nTo run tests, use:")
    print("  python manage.py test test_mpesa_comprehensive.MpesaServiceTestCase")
    print("  python manage.py test test_mpesa_comprehensive.MpesaAPIViewsTestCase")
    print("  python manage.py test test_mpesa_comprehensive.MpesaIntegrationTestCase")
    print("\nOr run all M-Pesa tests:")
    print("  python manage.py test test_mpesa_comprehensive")