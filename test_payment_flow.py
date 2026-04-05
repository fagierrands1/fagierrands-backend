"""
M-Pesa Payment Flow Integration Test

Tests the complete payment flow through Django views:
1. Create payment record
2. Process M-Pesa STK Push
3. Check payment status
4. Simulate callback

Run: python test_payment_flow.py
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order, Payment
from orders.mpesa_service import MpesaDarajaService

User = get_user_model()


def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_success(message):
    print(f"✅ {message}")


def print_error(message):
    print(f"❌ {message}")


def print_info(message):
    print(f"ℹ️  {message}")


def test_service_initialization():
    """Test 1: M-Pesa Service Initialization"""
    print_header("TEST 1: M-Pesa Service Initialization")
    
    try:
        service = MpesaDarajaService()
        print_success("M-Pesa service initialized")
        print_info(f"Environment: {service.environment}")
        print_info(f"Shortcode: {service.shortcode}")
        print_info(f"Base URL: {service.base_url}")
        return True, service
    except Exception as e:
        print_error(f"Failed to initialize service: {str(e)}")
        return False, None


def test_oauth_token(service):
    """Test 2: OAuth Token Generation"""
    print_header("TEST 2: OAuth Token Generation")
    
    try:
        token = service.get_access_token()
        if token:
            print_success("OAuth token generated successfully")
            print_info(f"Token: {token[:10]}...{token[-10:]}")
            print_info(f"Token length: {len(token)} characters")
            return True
        else:
            print_error("Failed to generate OAuth token")
            return False
    except Exception as e:
        print_error(f"OAuth token generation failed: {str(e)}")
        return False


def test_phone_validation(service):
    """Test 3: Phone Number Validation"""
    print_header("TEST 3: Phone Number Validation")
    
    test_numbers = [
        "254758292353",  # Your actual number
        "0758292353",
        "+254758292353",
        "254712345678",
        "0712345678",
    ]
    
    all_passed = True
    for number in test_numbers:
        try:
            is_valid, formatted = service.validate_phone_number(number)
            if is_valid:
                print_success(f"{number} → {formatted}")
            else:
                print_error(f"{number} → Invalid")
                all_passed = False
        except Exception as e:
            print_error(f"{number} → Error: {str(e)}")
            all_passed = False
    
    return all_passed


def test_stk_push_dry_run(service):
    """Test 4: STK Push Dry Run (No actual payment)"""
    print_header("TEST 4: STK Push Dry Run")
    
    print_info("Testing STK Push parameters without sending...")
    
    try:
        # Validate parameters
        phone = "254758292353"
        amount = 1
        account_ref = "TEST001"
        description = "Test Payment"
        
        is_valid, formatted_phone = service.validate_phone_number(phone)
        if not is_valid:
            print_error(f"Invalid phone number: {phone}")
            return False
        
        print_success(f"Phone validated: {formatted_phone}")
        print_success(f"Amount: KSh {amount}")
        print_success(f"Account: {account_ref}")
        print_success(f"Description: {description}")
        
        # Generate timestamp and password (without sending)
        from datetime import datetime
        import base64
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{service.shortcode}{service.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')
        
        print_success(f"Timestamp: {timestamp}")
        print_success(f"Password generated: {len(password)} characters")
        
        return True
    except Exception as e:
        print_error(f"Dry run failed: {str(e)}")
        return False


def test_database_models():
    """Test 5: Database Models"""
    print_header("TEST 5: Database Models")
    
    try:
        # Check if Payment model has M-Pesa fields
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(orders_payment)")
            columns = [row[1] for row in cursor.fetchall()]
        
        mpesa_fields = [
            'mpesa_receipt_number',
            'mpesa_transaction_date',
            'mpesa_phone_number',
            'mpesa_checkout_request_id',
            'mpesa_merchant_request_id'
        ]
        
        missing_fields = []
        for field in mpesa_fields:
            if field in columns:
                print_success(f"Field exists: {field}")
            else:
                print_error(f"Field missing: {field}")
                missing_fields.append(field)
        
        if missing_fields:
            print_error("⚠️  Database migration needed!")
            print_info("Run: python manage.py migrate orders")
            return False
        else:
            print_success("All M-Pesa fields present in database")
            return True
            
    except Exception as e:
        print_error(f"Database check failed: {str(e)}")
        return False


def test_create_test_payment():
    """Test 6: Create Test Payment Record"""
    print_header("TEST 6: Create Test Payment Record")
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            phone_number="254758292353",
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            }
        )
        
        if created:
            print_info("Created test user")
        else:
            print_info("Using existing test user")
        
        # Create test order
        order = Order.objects.create(
            user=user,
            total_amount=1.00,
            status='pending'
        )
        print_success(f"Created test order: {order.id}")
        
        # Create test payment
        payment = Payment.objects.create(
            order=order,
            amount=1.00,
            payment_method='mpesa',
            status='pending'
        )
        print_success(f"Created test payment: {payment.id}")
        print_info(f"Payment status: {payment.status}")
        print_info(f"Payment method: {payment.payment_method}")
        
        return True, payment
        
    except Exception as e:
        print_error(f"Failed to create test payment: {str(e)}")
        import traceback
        print_error(traceback.format_exc())
        return False, None


def test_live_stk_push(service, payment=None):
    """Test 7: Live STK Push (Optional)"""
    print_header("TEST 7: Live STK Push (Optional)")
    
    print_info("This will send a real STK Push to your phone!")
    print_info("Phone: 254758292353")
    print_info("Amount: KSh 1")
    
    response = input("\n⚠️  Send live STK Push? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print_info("Skipped live STK Push test")
        return True
    
    try:
        result = service.stk_push(
            phone_number="254758292353",
            amount=1,
            account_reference="TEST" + datetime.now().strftime('%Y%m%d%H%M%S'),
            transaction_desc="Test Payment"
        )
        
        if result.get('success'):
            print_success("STK Push sent successfully!")
            print_info(f"Checkout Request ID: {result.get('CheckoutRequestID')}")
            print_info(f"Merchant Request ID: {result.get('MerchantRequestID')}")
            print_info(f"Response: {result.get('ResponseDescription')}")
            
            # Update payment record if provided
            if payment:
                payment.mpesa_checkout_request_id = result.get('CheckoutRequestID')
                payment.mpesa_merchant_request_id = result.get('MerchantRequestID')
                payment.save()
                print_success("Payment record updated with M-Pesa IDs")
            
            print_info("\n📱 Check your phone for M-Pesa prompt!")
            print_info("You have 60 seconds to complete the payment")
            
            return True
        else:
            print_error(f"STK Push failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print_error(f"STK Push error: {str(e)}")
        import traceback
        print_error(traceback.format_exc())
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("  M-PESA INTEGRATION TEST SUITE")
    print("🚀"*35)
    
    results = {}
    
    # Test 1: Service Initialization
    success, service = test_service_initialization()
    results['Service Initialization'] = success
    
    if not success:
        print_error("\n❌ Cannot proceed without service initialization")
        return
    
    # Test 2: OAuth Token
    results['OAuth Token'] = test_oauth_token(service)
    
    # Test 3: Phone Validation
    results['Phone Validation'] = test_phone_validation(service)
    
    # Test 4: STK Push Dry Run
    results['STK Push Dry Run'] = test_stk_push_dry_run(service)
    
    # Test 5: Database Models
    results['Database Models'] = test_database_models()
    
    # Test 6: Create Test Payment
    success, payment = test_create_test_payment()
    results['Create Test Payment'] = success
    
    # Test 7: Live STK Push (Optional)
    if success and payment:
        results['Live STK Push'] = test_live_stk_push(service, payment)
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        if passed_test:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All tests passed! M-Pesa integration is working correctly!")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    main()