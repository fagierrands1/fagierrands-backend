"""
Django M-Pesa Integration Test

Tests M-Pesa integration through Django ORM and views.
This test requires Django environment and database access.

Run: python test_django_mpesa.py
"""

import os
import sys
import django
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.mpesa_service import MpesaDarajaService


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


def test_1_service_init():
    """Test 1: Service Initialization"""
    print_header("TEST 1: Service Initialization")
    
    try:
        service = MpesaDarajaService()
        print_success("M-Pesa service initialized")
        print_info(f"Environment: {service.environment}")
        print_info(f"Shortcode: {service.shortcode}")
        print_info(f"Base URL: {service.base_url}")
        
        # Check if credentials are loaded
        if not service.consumer_key or service.consumer_key == 'your_consumer_key_here':
            print_error("Consumer key not configured")
            return False, None
        
        if not service.consumer_secret or service.consumer_secret == 'your_consumer_secret_here':
            print_error("Consumer secret not configured")
            return False, None
        
        print_success("Credentials loaded successfully")
        return True, service
        
    except Exception as e:
        print_error(f"Service initialization failed: {str(e)}")
        return False, None


def test_2_oauth_token(service):
    """Test 2: OAuth Token Generation"""
    print_header("TEST 2: OAuth Token Generation")
    
    try:
        token = service.get_access_token()
        
        if token and len(token) > 0:
            print_success("OAuth token generated")
            print_info(f"Token: {token[:10]}...{token[-10:]}")
            print_info(f"Length: {len(token)} characters")
            return True
        else:
            print_error("Failed to generate token")
            return False
            
    except Exception as e:
        print_error(f"OAuth failed: {str(e)}")
        return False


def test_3_phone_validation(service):
    """Test 3: Phone Number Validation"""
    print_header("TEST 3: Phone Number Validation")
    
    test_cases = [
        ("254758292353", True),  # Your number
        ("0758292353", True),
        ("+254758292353", True),
        ("254712345678", True),
        ("0712345678", True),
        ("123456", False),  # Too short
        ("999999999999", False),  # Invalid prefix
    ]
    
    all_passed = True
    for phone, should_be_valid in test_cases:
        try:
            is_valid = service.validate_phone_number(phone)
            formatted = service.format_phone_number(phone)
            
            if is_valid == should_be_valid:
                status = "✅" if is_valid else "⚠️ "
                print(f"{status} {phone} → {formatted} (Valid: {is_valid})")
            else:
                print_error(f"{phone} → Expected {should_be_valid}, got {is_valid}")
                all_passed = False
                
        except Exception as e:
            print_error(f"{phone} → Error: {str(e)}")
            all_passed = False
    
    return all_passed


def test_4_stk_push_params(service):
    """Test 4: STK Push Parameter Generation"""
    print_header("TEST 4: STK Push Parameters")
    
    try:
        import base64
        
        # Test timestamp generation
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        print_success(f"Timestamp: {timestamp}")
        
        # Test password generation
        password = service.generate_password(timestamp)
        print_success(f"Password: {password[:20]}... ({len(password)} chars)")
        
        # Test phone formatting
        phone = "254758292353"
        formatted = service.format_phone_number(phone)
        print_success(f"Phone: {formatted}")
        
        # Test callback URL
        from django.conf import settings
        callback_url = f"{settings.BASE_URL}/api/orders/payments/mpesa/stk-callback/"
        print_success(f"Callback: {callback_url}")
        
        return True
        
    except Exception as e:
        print_error(f"Parameter generation failed: {str(e)}")
        return False


def test_5_database_connection():
    """Test 5: Database Connection"""
    print_header("TEST 5: Database Connection")
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        print_success("Database connection successful")
        print_info(f"Database: {connection.settings_dict['NAME']}")
        
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return False


def test_6_payment_model():
    """Test 6: Payment Model Structure"""
    print_header("TEST 6: Payment Model")
    
    try:
        from orders.models import Payment
        
        # Check if model has M-Pesa fields
        mpesa_fields = [
            'mpesa_receipt_number',
            'mpesa_transaction_date',
            'mpesa_phone_number',
            'mpesa_checkout_request_id',
            'mpesa_merchant_request_id'
        ]
        
        model_fields = [f.name for f in Payment._meta.get_fields()]
        
        missing = []
        for field in mpesa_fields:
            if field in model_fields:
                print_success(f"Field exists: {field}")
            else:
                print_error(f"Field missing: {field}")
                missing.append(field)
        
        if missing:
            print_error("⚠️  Run migration: python manage.py migrate orders")
            return False
        
        print_success("All M-Pesa fields present")
        return True
        
    except Exception as e:
        print_error(f"Model check failed: {str(e)}")
        return False


def test_7_live_stk_push(service):
    """Test 7: Live STK Push (Optional)"""
    print_header("TEST 7: Live STK Push")
    
    print_info("This will send a REAL STK Push to your phone!")
    print_info("Phone: 254758292353")
    print_info("Amount: KSh 1")
    print()
    
    response = input("Send live STK Push? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print_info("Skipped live test")
        return True
    
    try:
        result = service.stk_push(
            phone_number="254758292353",
            amount=1,
            account_reference="TEST" + datetime.now().strftime('%H%M%S'),
            transaction_desc="M-Pesa Integration Test"
        )
        
        if result.get('success'):
            print_success("STK Push sent successfully!")
            print_info(f"Checkout ID: {result.get('CheckoutRequestID')}")
            print_info(f"Merchant ID: {result.get('MerchantRequestID')}")
            print_info(f"Response: {result.get('ResponseDescription')}")
            print()
            print_info("📱 Check your phone for M-Pesa prompt!")
            print_info("You have 60 seconds to complete payment")
            return True
        else:
            print_error(f"STK Push failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print_error(f"STK Push error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("  DJANGO M-PESA INTEGRATION TEST")
    print("🚀"*35)
    
    results = {}
    
    # Test 1: Service Initialization
    success, service = test_1_service_init()
    results['Service Initialization'] = success
    
    if not success:
        print_error("\n❌ Cannot proceed without service")
        print_info("Check your .env file and credentials")
        return
    
    # Test 2: OAuth Token
    results['OAuth Token'] = test_2_oauth_token(service)
    
    # Test 3: Phone Validation
    results['Phone Validation'] = test_3_phone_validation(service)
    
    # Test 4: STK Push Parameters
    results['STK Push Parameters'] = test_4_stk_push_params(service)
    
    # Test 5: Database Connection
    results['Database Connection'] = test_5_database_connection()
    
    # Test 6: Payment Model
    results['Payment Model'] = test_6_payment_model()
    
    # Test 7: Live STK Push (Optional)
    if all(results.values()):
        results['Live STK Push'] = test_7_live_stk_push(service)
    
    # Print Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, test_passed in results.items():
        if test_passed:
            print_success(test_name)
        else:
            print_error(test_name)
    
    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All tests passed! M-Pesa integration is fully operational!")
        print()
        print_info("Next steps:")
        print_info("1. Deploy to Vercel")
        print_info("2. Update Vercel environment variables")
        print_info("3. Test in production environment")
    else:
        print("⚠️  Some tests failed. Review errors above.")
        
        if not results.get('Payment Model'):
            print()
            print_info("To fix Payment Model:")
            print_info("Run: python manage.py migrate orders")


if __name__ == "__main__":
    main()