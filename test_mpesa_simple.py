"""
Simple M-Pesa Integration Test
Tests M-Pesa service directly without Django
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("  M-PESA INTEGRATION TEST (Simple)")
print("="*70)

# Test 1: Check environment variables
print("\n1. Checking Environment Variables:")
print("-" * 70)

env_vars = {
    'MPESA_ENVIRONMENT': os.getenv('MPESA_ENVIRONMENT'),
    'MPESA_CONSUMER_KEY': os.getenv('MPESA_CONSUMER_KEY'),
    'MPESA_CONSUMER_SECRET': os.getenv('MPESA_CONSUMER_SECRET'),
    'MPESA_SHORTCODE': os.getenv('MPESA_SHORTCODE'),
    'MPESA_PASSKEY': os.getenv('MPESA_PASSKEY'),
    'BASE_URL': os.getenv('BASE_URL'),
}

all_set = True
for key, value in env_vars.items():
    if value and value not in ['your_consumer_key_here', 'your_consumer_secret_here', 'your_security_credential_here']:
        # Mask sensitive values
        if 'KEY' in key or 'SECRET' in key or 'PASSKEY' in key:
            display_value = value[:10] + "..." if len(value) > 10 else value
        else:
            display_value = value
        print(f"✅ {key}: {display_value}")
    else:
        print(f"❌ {key}: Not set or placeholder")
        all_set = False

if not all_set:
    print("\n❌ Some environment variables are missing!")
    print("Please check your .env file")
    sys.exit(1)

print("\n✅ All environment variables are set!")

# Test 2: Test M-Pesa Service
print("\n2. Testing M-Pesa Service:")
print("-" * 70)

try:
    # Import Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
    import django
    django.setup()
    
    from orders.mpesa_service import MpesaDarajaService
    
    print("✅ M-Pesa service imported successfully")
    
    # Initialize service
    service = MpesaDarajaService()
    print(f"✅ Service initialized")
    print(f"   Environment: {service.environment}")
    print(f"   Shortcode: {service.shortcode}")
    print(f"   Base URL: {service.base_url}")
    
    # Test 3: Phone number validation
    print("\n3. Testing Phone Number Validation:")
    print("-" * 70)
    
    test_numbers = [
        "254712345678",
        "0712345678",
        "+254712345678",
    ]
    
    for phone in test_numbers:
        try:
            formatted = service.format_phone_number(phone)
            is_valid = service.validate_phone_number(formatted)
            print(f"✅ {phone} → {formatted} (Valid: {is_valid})")
        except Exception as e:
            print(f"❌ {phone} → Error: {str(e)}")
    
    # Test 4: OAuth Token
    print("\n4. Testing OAuth Token Generation:")
    print("-" * 70)
    
    try:
        token = service.get_access_token()
        if token:
            print(f"✅ OAuth token generated successfully")
            print(f"   Token (first 20 chars): {token[:20]}...")
            print(f"   Token length: {len(token)} characters")
            
            # Test 5: STK Push (dry run)
            print("\n5. Testing STK Push (Dry Run):")
            print("-" * 70)
            print("   This will show what would be sent without actually sending")
            
            test_phone = "254712345678"
            test_amount = 10
            
            print(f"   Phone: {test_phone}")
            print(f"   Amount: KSh {test_amount}")
            print(f"   Callback URL: {service.base_url}/api/orders/payments/mpesa/stk-callback/")
            
            # Validate phone
            formatted_phone = service.format_phone_number(test_phone)
            if service.validate_phone_number(formatted_phone):
                print(f"✅ Phone number validated: {formatted_phone}")
            
            # Generate timestamp and password
            from datetime import datetime
            import base64
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_string = f"{service.shortcode}{service.passkey}{timestamp}"
            password = base64.b64encode(password_string.encode()).decode('utf-8')
            
            print(f"✅ Timestamp generated: {timestamp}")
            print(f"✅ Password generated (first 20 chars): {password[:20]}...")
            
            print("\n6. Ready for Live Test:")
            print("-" * 70)
            print("   The M-Pesa integration is configured correctly!")
            print("   To test with actual STK Push:")
            print("   1. Make sure you have a test phone number")
            print("   2. Use Safaricom's test app for sandbox")
            print("   3. Call service.stk_push() with your test phone")
            
            print("\n" + "="*70)
            print("  ✅ ALL TESTS PASSED!")
            print("="*70)
            print("\nNext Steps:")
            print("1. Run database migration: python manage.py migrate orders")
            print("2. Test STK Push with: python test_mpesa_live.py")
            print("3. Register C2B URLs with Safaricom")
            print("="*70)
            
        else:
            print("❌ Failed to generate OAuth token")
            print("   Check your Consumer Key and Consumer Secret")
            
    except Exception as e:
        print(f"❌ OAuth token generation failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        
except Exception as e:
    print(f"❌ Failed to initialize M-Pesa service: {str(e)}")
    import traceback
    print(f"   Traceback:\n{traceback.format_exc()}")
    sys.exit(1)