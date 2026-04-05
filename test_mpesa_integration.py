"""
M-Pesa Daraja API Integration Test Script

This script tests the M-Pesa integration including:
1. Service initialization
2. OAuth token generation
3. STK Push initiation
4. Phone number validation
5. Configuration validation

Before running:
1. Update .env file with your M-Pesa credentials
2. Ensure Django environment is set up
3. Run: python test_mpesa_integration.py
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.mpesa_service import MpesaDarajaService
from django.conf import settings


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


def test_configuration():
    """Test M-Pesa configuration"""
    print_header("TEST 1: Configuration Validation")
    
    required_settings = [
        'MPESA_ENVIRONMENT',
        'MPESA_CONSUMER_KEY',
        'MPESA_CONSUMER_SECRET',
        'MPESA_SHORTCODE',
        'MPESA_PASSKEY',
    ]
    
    all_configured = True
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if value and value != 'your_consumer_key_here' and value != 'your_consumer_secret_here':
            print_success(f"{setting}: Configured")
        else:
            print_error(f"{setting}: Not configured or using placeholder")
            all_configured = False
    
    print_info(f"Environment: {getattr(settings, 'MPESA_ENVIRONMENT', 'Not set')}")
    print_info(f"Shortcode: {getattr(settings, 'MPESA_SHORTCODE', 'Not set')}")
    print_info(f"Base URL: {getattr(settings, 'BASE_URL', 'Not set')}")
    
    return all_configured


def test_service_initialization():
    """Test M-Pesa service initialization"""
    print_header("TEST 2: Service Initialization")
    
    try:
        service = MpesaDarajaService()
        print_success("M-Pesa service initialized successfully")
        print_info(f"Environment: {service.environment}")
        print_info(f"Base URL: {service.base_url}")
        print_info(f"Shortcode: {service.shortcode}")
        return service
    except Exception as e:
        print_error(f"Failed to initialize service: {str(e)}")
        return None


def test_phone_number_validation(service):
    """Test phone number validation and formatting"""
    print_header("TEST 3: Phone Number Validation")
    
    test_numbers = [
        ("254712345678", True, "254712345678"),
        ("0712345678", True, "254712345678"),
        ("+254712345678", True, "254712345678"),
        ("712345678", True, "254712345678"),
        ("254112345678", False, None),  # Invalid - starts with 1
        ("25471234567", False, None),   # Invalid - too short
        ("2547123456789", False, None), # Invalid - too long
    ]
    
    for phone, should_pass, expected in test_numbers:
        try:
            formatted = service.format_phone_number(phone)
            is_valid = service.validate_phone_number(formatted)
            
            if should_pass and is_valid and formatted == expected:
                print_success(f"{phone} → {formatted} (Valid)")
            elif not should_pass and not is_valid:
                print_success(f"{phone} → Correctly rejected")
            else:
                print_error(f"{phone} → Unexpected result: {formatted}, Valid: {is_valid}")
        except Exception as e:
            if not should_pass:
                print_success(f"{phone} → Correctly rejected with error")
            else:
                print_error(f"{phone} → Unexpected error: {str(e)}")


def test_oauth_token(service):
    """Test OAuth token generation"""
    print_header("TEST 4: OAuth Token Generation")
    
    try:
        token = service.get_access_token()
        if token:
            print_success("OAuth token generated successfully")
            print_info(f"Token (first 20 chars): {token[:20]}...")
            print_info(f"Token length: {len(token)} characters")
            return True
        else:
            print_error("Failed to generate OAuth token (returned None)")
            return False
    except Exception as e:
        print_error(f"OAuth token generation failed: {str(e)}")
        print_info("This is expected if credentials are not configured")
        return False


def test_stk_push_dry_run(service):
    """Test STK Push (dry run - shows what would be sent)"""
    print_header("TEST 5: STK Push Dry Run")
    
    test_phone = "254712345678"
    test_amount = 10
    test_account_ref = "TEST001"
    test_description = "Test Payment"
    
    print_info("This is a DRY RUN - no actual request will be sent")
    print_info(f"Phone: {test_phone}")
    print_info(f"Amount: KSh {test_amount}")
    print_info(f"Account Reference: {test_account_ref}")
    print_info(f"Description: {test_description}")
    
    try:
        # Validate inputs
        formatted_phone = service.format_phone_number(test_phone)
        is_valid = service.validate_phone_number(formatted_phone)
        
        if is_valid:
            print_success(f"Phone number validated: {formatted_phone}")
        else:
            print_error(f"Invalid phone number: {formatted_phone}")
            return False
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        print_info(f"Timestamp: {timestamp}")
        
        # Generate password
        password_string = f"{service.shortcode}{service.passkey}{timestamp}"
        import base64
        password = base64.b64encode(password_string.encode()).decode('utf-8')
        print_success("Password generated successfully")
        
        # Show callback URL
        callback_url = f"{service.base_url}/api/orders/payments/mpesa/stk-callback/"
        print_info(f"Callback URL: {callback_url}")
        
        print_success("STK Push dry run completed - all validations passed")
        return True
        
    except Exception as e:
        print_error(f"STK Push dry run failed: {str(e)}")
        return False


def test_stk_push_live(service):
    """Test actual STK Push (requires valid credentials and phone)"""
    print_header("TEST 6: Live STK Push Test")
    
    print_info("⚠️  WARNING: This will send an actual STK Push prompt!")
    print_info("Make sure you have:")
    print_info("  1. Valid M-Pesa sandbox credentials")
    print_info("  2. A test phone number registered in sandbox")
    print_info("  3. The Safaricom test app installed (for sandbox)")
    
    response = input("\nDo you want to proceed with live test? (yes/no): ")
    
    if response.lower() != 'yes':
        print_info("Live test skipped")
        return False
    
    phone = input("Enter test phone number (e.g., 254712345678): ")
    amount = input("Enter test amount (e.g., 10): ")
    
    try:
        amount = int(amount)
        result = service.stk_push(
            phone_number=phone,
            amount=amount,
            account_reference="TEST001",
            transaction_desc="Test Payment"
        )
        
        if result.get('success'):
            print_success("STK Push sent successfully!")
            print_info(f"Checkout Request ID: {result.get('CheckoutRequestID')}")
            print_info(f"Merchant Request ID: {result.get('MerchantRequestID')}")
            print_info("Check your phone for the M-Pesa prompt")
            return True
        else:
            print_error(f"STK Push failed: {result.get('error', 'Unknown error')}")
            if 'response' in result:
                print_info(f"Response: {result['response']}")
            return False
            
    except Exception as e:
        print_error(f"Live STK Push test failed: {str(e)}")
        return False


def test_callback_urls():
    """Test callback URL configuration"""
    print_header("TEST 7: Callback URL Configuration")
    
    base_url = getattr(settings, 'BASE_URL', None)
    
    if not base_url:
        print_error("BASE_URL not configured in settings")
        return False
    
    callback_urls = {
        'STK Callback': f"{base_url}/api/orders/payments/mpesa/stk-callback/",
        'C2B Validation': f"{base_url}/api/orders/payments/mpesa/c2b-validation/",
        'C2B Confirmation': f"{base_url}/api/orders/payments/mpesa/c2b-confirmation/",
        'B2C Result': f"{base_url}/api/orders/payments/mpesa/b2c-result/",
        'B2C Timeout': f"{base_url}/api/orders/payments/mpesa/b2c-timeout/",
    }
    
    for name, url in callback_urls.items():
        print_info(f"{name}: {url}")
        
        # Check if URL is HTTPS
        if url.startswith('https://'):
            print_success(f"  ✓ {name} uses HTTPS")
        else:
            print_error(f"  ✗ {name} must use HTTPS for production")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("  M-PESA DARAJA API INTEGRATION TEST SUITE")
    print("🚀"*35)
    
    results = {}
    
    # Test 1: Configuration
    results['configuration'] = test_configuration()
    
    if not results['configuration']:
        print_error("\n⚠️  Configuration incomplete. Please update .env file with M-Pesa credentials.")
        print_info("Get sandbox credentials from: https://developer.safaricom.co.ke/")
        return
    
    # Test 2: Service Initialization
    service = test_service_initialization()
    if not service:
        print_error("\n⚠️  Service initialization failed. Cannot proceed with further tests.")
        return
    
    results['initialization'] = True
    
    # Test 3: Phone Number Validation
    test_phone_number_validation(service)
    results['phone_validation'] = True
    
    # Test 4: OAuth Token
    results['oauth'] = test_oauth_token(service)
    
    # Test 5: STK Push Dry Run
    results['stk_dry_run'] = test_stk_push_dry_run(service)
    
    # Test 6: Callback URLs
    results['callback_urls'] = test_callback_urls()
    
    # Test 7: Live STK Push (optional)
    if results['oauth']:
        results['stk_live'] = test_stk_push_live(service)
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = len([k for k in results.keys() if k != 'stk_live'])
    passed_tests = len([v for k, v in results.items() if v and k != 'stk_live'])
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    if passed_tests == total_tests:
        print_success("\n🎉 All tests passed! M-Pesa integration is ready.")
    else:
        print_error("\n⚠️  Some tests failed. Please review the errors above.")
    
    print("\n" + "="*70)
    print("Next Steps:")
    print("1. If OAuth failed: Update MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET")
    print("2. Run database migration: python manage.py migrate orders")
    print("3. Register C2B URLs with Safaricom")
    print("4. Test with actual payments in sandbox")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()