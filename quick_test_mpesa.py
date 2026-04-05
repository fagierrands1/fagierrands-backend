"""
Quick M-Pesa Testing Script
Run this directly for rapid testing without Django test framework
Usage: python quick_test_mpesa.py
"""

import os
import django
import sys
import json

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.mpesa_service import mpesa_service

# Try to import colorama, fall back to plain text if not available
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    print("Note: Install 'colorama' for colored output: pip install colorama")
    # Define dummy color classes
    class Colors:
        def __getattr__(self, name):
            return ""
    Fore = Colors()
    Back = Colors()
    Style = Colors()
    COLORS_AVAILABLE = False

# Test configuration
TEST_PHONE = '254712345678'
TEST_AMOUNT = 10


def print_header(title):
    """Print formatted header"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{title:^80}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")


def print_success(msg):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")


def print_error(msg):
    """Print error message"""
    print(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")


def print_info(msg):
    """Print info message"""
    print(f"{Fore.YELLOW}ℹ {msg}{Style.RESET_ALL}")


def print_response(data):
    """Print formatted JSON response"""
    print(f"{Fore.LIGHTBLACK_EX}{json.dumps(data, indent=2)}{Style.RESET_ALL}")


def test_authentication():
    """Test 1: Authentication & Token Generation"""
    print_header("TEST 1: AUTHENTICATION & TOKEN GENERATION")
    
    try:
        print_info("Attempting to get access token...")
        token = mpesa_service.get_access_token()
        print_success(f"Token obtained successfully")
        print_info(f"Token (first 30 chars): {token[:30]}...")
        print_info(f"Token length: {len(token)} characters")
        return True
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        return False


def test_stk_push():
    """Test 2: STK Push (Lipa Na M-Pesa)"""
    print_header("TEST 2: STK PUSH (LIPA NA M-PESA)")
    
    try:
        print_info(f"Phone: {TEST_PHONE}")
        print_info(f"Amount: {TEST_AMOUNT} KES")
        print_info(f"Reference: TEST-STK-001")
        
        result = mpesa_service.stk_push(
            phone_number=TEST_PHONE,
            amount=TEST_AMOUNT,
            account_reference='TEST-STK-001',
            transaction_desc='Quick test STK Push'
        )
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("STK Push initiated successfully")
            checkout_id = result.get('CheckoutRequestID')
            print_info(f"Checkout Request ID: {checkout_id}")
        else:
            print_error(f"STK Push failed with code {response_code}")
            print_info(f"Description: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_phone_formatting():
    """Test 3: Phone Number Formatting"""
    print_header("TEST 3: PHONE NUMBER FORMATTING")
    
    test_cases = [
        ('254712345678', '254712345678', 'Already formatted'),
        ('0712345678', '254712345678', 'Leading zero'),
        ('+254712345678', '254712345678', 'With + prefix'),
        ('712345678', '254712345678', 'Short format'),
    ]
    
    all_passed = True
    for input_phone, expected, description in test_cases:
        try:
            result = mpesa_service.format_phone_number(input_phone)
            if result == expected:
                print_success(f"{description:20} | {input_phone:20} → {result}")
            else:
                print_error(f"{description:20} | Expected {expected}, got {result}")
                all_passed = False
        except Exception as e:
            print_error(f"{description:20} | Exception: {str(e)}")
            all_passed = False
    
    return all_passed


def test_phone_validation():
    """Test 4: Phone Number Validation"""
    print_header("TEST 4: PHONE NUMBER VALIDATION")
    
    valid_phones = [
        ('254712345678', 'Format: 254XXXXXXXXX'),
        ('0712345678', 'Format: 0XXXXXXXXX'),
        ('+254712345678', 'Format: +254XXXXXXXXX'),
    ]
    
    invalid_phones = [
        ('123', 'Too short'),
        ('abc', 'Non-numeric'),
        ('254812345678', 'Invalid Kenyan number (starts with 8)'),
        ('', 'Empty string'),
    ]
    
    print(f"{Fore.CYAN}Valid Kenyan Numbers:{Style.RESET_ALL}")
    all_passed = True
    for phone, description in valid_phones:
        try:
            is_valid = mpesa_service.validate_phone_number(phone)
            if is_valid:
                print_success(f"{description:35} | {phone}")
            else:
                print_error(f"{description:35} | {phone} (validation failed)")
                all_passed = False
        except Exception as e:
            print_error(f"{description:35} | Exception: {str(e)}")
            all_passed = False
    
    print(f"\n{Fore.CYAN}Invalid Numbers (should reject):{Style.RESET_ALL}")
    for phone, description in invalid_phones:
        try:
            is_valid = mpesa_service.validate_phone_number(phone)
            if not is_valid:
                print_success(f"{description:35} | Correctly rejected: '{phone}'")
            else:
                print_error(f"{description:35} | Should have rejected: '{phone}'")
                all_passed = False
        except Exception as e:
            print_success(f"{description:35} | Correctly raised exception")
    
    return all_passed


def test_account_balance():
    """Test 5: Account Balance Query"""
    print_header("TEST 5: ACCOUNT BALANCE QUERY")
    
    try:
        print_info("Querying account balance...")
        result = mpesa_service.account_balance()
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("Account balance query successful")
            print_info("Processing result...")
        else:
            print_info(f"Status: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_b2c_payment():
    """Test 6: B2C Payment (Payout)"""
    print_header("TEST 6: B2C PAYMENT (PAYOUT)")
    
    try:
        print_info(f"Phone: {TEST_PHONE}")
        print_info(f"Amount: {TEST_AMOUNT} KES")
        print_info(f"Occasion: Test Payout")
        
        result = mpesa_service.b2c_payment(
            phone_number=TEST_PHONE,
            amount=TEST_AMOUNT,
            occasion='Test',
            remarks='Quick test B2C payment'
        )
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("B2C Payment initiated successfully")
        else:
            print_info(f"Response Code: {response_code}")
            print_info(f"Description: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_b2b_payment():
    """Test 7: B2B Payment"""
    print_header("TEST 7: B2B PAYMENT")
    
    try:
        print_info("Receiver: 600000 (Shortcode)")
        print_info("Amount: 500 KES")
        print_info("Account Reference: B2B-QUICK-TEST")
        
        result = mpesa_service.b2b_payment(
            receiver_shortcode='600000',
            amount=500,
            account_reference='B2B-QUICK-TEST',
            remarks='Quick test B2B payment'
        )
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("B2B Payment initiated successfully")
        else:
            print_info(f"Response Code: {response_code}")
            print_info(f"Description: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_dynamic_qr():
    """Test 8: Dynamic QR Code Generation"""
    print_header("TEST 8: DYNAMIC QR CODE GENERATION")
    
    try:
        print_info("Amount: 100 KES")
        print_info("Reference: QR-QUICK-TEST")
        print_info("Merchant: Test Merchant")
        
        result = mpesa_service.generate_dynamic_qr(
            amount=100,
            ref_no='QR-QUICK-TEST',
            merchant_name='Test Merchant'
        )
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("Dynamic QR Code generated successfully")
            qr_code = result.get('QRCode')
            print_info(f"QR Code: {qr_code[:50]}..." if qr_code else "No QR Code in response")
        else:
            print_info(f"Response Code: {response_code}")
            print_info(f"Description: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_c2b_registration():
    """Test 9: C2B URL Registration"""
    print_header("TEST 9: C2B URL REGISTRATION")
    
    try:
        print_info("Registering C2B validation and confirmation URLs...")
        result = mpesa_service.register_c2b_urls()
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("C2B URLs registered successfully")
        else:
            print_info(f"Response Code: {response_code}")
            print_info(f"Description: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_transaction_status():
    """Test 10: Transaction Status Query"""
    print_header("TEST 10: TRANSACTION STATUS QUERY")
    
    try:
        # Use example transaction ID
        transaction_id = 'MLU0200009902'
        print_info(f"Querying transaction ID: {transaction_id}")
        
        result = mpesa_service.transaction_status(transaction_id)
        
        response_code = result.get('ResponseCode')
        if response_code == '0':
            print_success("Transaction status retrieved successfully")
        else:
            print_info(f"Response Code: {response_code}")
            print_info(f"Description: {result.get('ResponseDescription')}")
        
        print_response(result)
        return True
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"{Fore.GREEN}Passed: {passed}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {percentage:.1f}%")
    
    if percentage == 100:
        print(f"{Fore.GREEN}✓ ALL TESTS PASSED!{Style.RESET_ALL}")
    elif percentage >= 80:
        print(f"{Fore.YELLOW}⚠ MOST TESTS PASSED{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ MULTIPLE TEST FAILURES{Style.RESET_ALL}")


def main():
    """Run all tests"""
    print_header("M-PESA DARAJA API QUICK TEST SUITE")
    print(f"Environment: Production" if 'production' in str(mpesa_service.environment).lower() else f"Environment: Sandbox")
    print(f"Shortcode: {mpesa_service.shortcode}")
    print(f"Base URL: {mpesa_service.base_url}")
    
    tests = [
        ("Authentication", test_authentication),
        ("Phone Formatting", test_phone_formatting),
        ("Phone Validation", test_phone_validation),
        ("STK Push", test_stk_push),
        ("Account Balance", test_account_balance),
        ("B2C Payment", test_b2c_payment),
        ("B2B Payment", test_b2b_payment),
        ("Dynamic QR Code", test_dynamic_qr),
        ("C2B Registration", test_c2b_registration),
        ("Transaction Status", test_transaction_status),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except KeyboardInterrupt:
            print_error("\nTests interrupted by user")
            break
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {str(e)}")
            results.append(False)
    
    print_summary(results)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests cancelled by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Fatal error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)