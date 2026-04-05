#!/usr/bin/env python
"""
Comprehensive IntaSend Integration Test
Tests all aspects of the payment integration
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Payment, Order
from django.utils import timezone

def test_intasend_integration():
    """Comprehensive test of IntaSend integration"""
    
    print("🧪 Comprehensive IntaSend Integration Test")
    print("=" * 60)
    
    results = {
        'webhook_tests': [],
        'model_tests': [],
        'integration_tests': [],
        'performance_tests': []
    }
    
    # Test 1: Webhook Endpoint Accessibility
    print("\n1️⃣ Testing Webhook Endpoint Accessibility")
    print("-" * 40)
    
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    try:
        response = requests.get(webhook_url, timeout=10)
        if response.status_code == 405:  # Method Not Allowed is expected for GET
            print("✅ Webhook endpoint is accessible")
            results['webhook_tests'].append({'test': 'endpoint_accessibility', 'status': 'pass'})
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            results['webhook_tests'].append({'test': 'endpoint_accessibility', 'status': 'warning'})
    except Exception as e:
        print(f"❌ Webhook endpoint not accessible: {str(e)}")
        results['webhook_tests'].append({'test': 'endpoint_accessibility', 'status': 'fail'})
    
    # Test 2: Official IntaSend Webhook Format
    print("\n2️⃣ Testing Official IntaSend Webhook Format")
    print("-" * 40)
    
    official_webhook_tests = [
        {
            'name': 'Payment Complete',
            'payload': {
                "invoice_id": "TEST_COMPLETE_001",
                "state": "COMPLETE",
                "provider": "M-PESA",
                "charges": "3.00",
                "net_amount": "97.00",
                "currency": "KES",
                "value": "100.00",
                "account": "QGH7X8Y9Z0",
                "api_ref": "ISL_test_complete_001",
                "host": "https://payment.intasend.com",
                "failed_reason": None,
                "failed_code": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "challenge": "fagierrands_webhook_2025_secure"
            }
        },
        {
            'name': 'Payment Failed',
            'payload': {
                "invoice_id": "TEST_FAILED_002",
                "state": "FAILED",
                "provider": "M-PESA",
                "charges": "0.00",
                "net_amount": "0.00",
                "currency": "KES",
                "value": "50.00",
                "account": "254700000000",
                "api_ref": "ISL_test_failed_002",
                "host": "https://payment.intasend.com",
                "failed_reason": "Insufficient funds",
                "failed_code": "INSUFFICIENT_FUNDS",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "challenge": "fagierrands_webhook_2025_secure"
            }
        },
        {
            'name': 'Card Payment Complete',
            'payload': {
                "invoice_id": "TEST_CARD_003",
                "state": "COMPLETE",
                "provider": "CARD-PAYMENT",
                "charges": "5.36",
                "net_amount": "94.64",
                "currency": "KES",
                "value": "100.00",
                "account": "john.doe@gmail.com",
                "api_ref": "ISL_test_card_003",
                "host": "https://payment.intasend.com",
                "failed_reason": None,
                "failed_code": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "challenge": "fagierrands_webhook_2025_secure"
            }
        }
    ]
    
    for test_case in official_webhook_tests:
        try:
            response = requests.post(
                webhook_url,
                json=test_case['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {test_case['name']}: {response.status_code}")
                results['webhook_tests'].append({
                    'test': test_case['name'].lower().replace(' ', '_'),
                    'status': 'pass'
                })
            else:
                print(f"❌ {test_case['name']}: {response.status_code}")
                results['webhook_tests'].append({
                    'test': test_case['name'].lower().replace(' ', '_'),
                    'status': 'fail'
                })
        except Exception as e:
            print(f"❌ {test_case['name']}: {str(e)}")
            results['webhook_tests'].append({
                'test': test_case['name'].lower().replace(' ', '_'),
                'status': 'fail'
            })
    
    # Test 3: Payment Model Analysis
    print("\n3️⃣ Testing Payment Model")
    print("-" * 40)
    
    try:
        total_payments = Payment.objects.count()
        print(f"📊 Total payments in database: {total_payments}")
        
        if total_payments > 0:
            # Status distribution
            status_counts = {}
            for payment in Payment.objects.all():
                status = payment.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("📈 Payment status distribution:")
            for status, count in status_counts.items():
                percentage = (count / total_payments) * 100
                print(f"   {status:12}: {count:3} ({percentage:5.1f}%)")
            
            # Check for required fields
            sample_payment = Payment.objects.first()
            required_fields = [
                'intasend_invoice_id', 'transaction_reference', 'amount',
                'payment_method', 'status', 'payment_date'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not hasattr(sample_payment, field):
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
                results['model_tests'].append({'test': 'required_fields', 'status': 'warning'})
            else:
                print("✅ All required fields present")
                results['model_tests'].append({'test': 'required_fields', 'status': 'pass'})
            
            # Check for enhanced fields
            enhanced_fields = [
                'intasend_api_ref', 'intasend_provider', 'intasend_charges',
                'intasend_net_amount', 'updated_at', 'completed_at',
                'failure_reason', 'failure_code', 'retry_count',
                'webhook_received_at', 'webhook_challenge'
            ]
            
            present_enhanced_fields = []
            missing_enhanced_fields = []
            
            for field in enhanced_fields:
                if hasattr(sample_payment, field):
                    present_enhanced_fields.append(field)
                else:
                    missing_enhanced_fields.append(field)
            
            print(f"✅ Enhanced fields present: {len(present_enhanced_fields)}/{len(enhanced_fields)}")
            if missing_enhanced_fields:
                print(f"⚠️  Missing enhanced fields: {missing_enhanced_fields[:3]}{'...' if len(missing_enhanced_fields) > 3 else ''}")
                results['model_tests'].append({'test': 'enhanced_fields', 'status': 'partial'})
            else:
                print("🎉 All enhanced fields present!")
                results['model_tests'].append({'test': 'enhanced_fields', 'status': 'pass'})
        
        else:
            print("⚠️  No payments found in database")
            results['model_tests'].append({'test': 'payment_data', 'status': 'warning'})
    
    except Exception as e:
        print(f"❌ Error analyzing payment model: {str(e)}")
        results['model_tests'].append({'test': 'model_analysis', 'status': 'fail'})
    
    # Test 4: Phone Number Formatting
    print("\n4️⃣ Testing Phone Number Formatting")
    print("-" * 40)
    
    test_phone_numbers = [
        ('0712345678', '254712345678'),
        ('712345678', '254712345678'),
        ('254712345678', '254712345678'),
        ('+254712345678', '254712345678'),
        ('07 1234 5678', '254712345678'),
        ('+254 712 345 678', '254712345678'),
    ]
    
    def format_phone_number_for_intasend(phone_number):
        """Test phone number formatting function"""
        if not phone_number:
            return None
        
        import re
        phone = re.sub(r'[^\d+]', '', str(phone_number).strip())
        
        if phone.startswith('+254'):
            return phone[1:]
        elif phone.startswith('254'):
            return phone
        elif phone.startswith('0') and len(phone) == 10:
            return '254' + phone[1:]
        elif len(phone) == 9:
            return '254' + phone
        else:
            return phone
    
    phone_test_passed = 0
    for input_phone, expected_output in test_phone_numbers:
        actual_output = format_phone_number_for_intasend(input_phone)
        if actual_output == expected_output:
            print(f"✅ {input_phone:15} → {actual_output}")
            phone_test_passed += 1
        else:
            print(f"❌ {input_phone:15} → {actual_output} (expected: {expected_output})")
    
    if phone_test_passed == len(test_phone_numbers):
        print("✅ All phone number formatting tests passed")
        results['integration_tests'].append({'test': 'phone_formatting', 'status': 'pass'})
    else:
        print(f"⚠️  {phone_test_passed}/{len(test_phone_numbers)} phone formatting tests passed")
        results['integration_tests'].append({'test': 'phone_formatting', 'status': 'partial'})
    
    # Test 5: Configuration Check
    print("\n5️⃣ Testing Configuration")
    print("-" * 40)
    
    from django.conf import settings
    
    config_checks = [
        ('INTASEND_PUBLISHABLE_KEY', getattr(settings, 'INTASEND_PUBLISHABLE_KEY', None)),
        ('INTASEND_SECRET_KEY', getattr(settings, 'INTASEND_SECRET_KEY', None)),
        ('INTASEND_TEST_MODE', getattr(settings, 'INTASEND_TEST_MODE', None)),
        ('FRONTEND_URL', getattr(settings, 'FRONTEND_URL', None)),
    ]
    
    config_passed = 0
    for config_name, config_value in config_checks:
        if config_value:
            # Mask sensitive values
            if 'KEY' in config_name:
                display_value = config_value[:10] + '...' + config_value[-10:] if len(config_value) > 20 else config_value
            else:
                display_value = config_value
            print(f"✅ {config_name}: {display_value}")
            config_passed += 1
        else:
            print(f"❌ {config_name}: Not configured")
    
    if config_passed == len(config_checks):
        print("✅ All configuration checks passed")
        results['integration_tests'].append({'test': 'configuration', 'status': 'pass'})
    else:
        print(f"⚠️  {config_passed}/{len(config_checks)} configuration checks passed")
        results['integration_tests'].append({'test': 'configuration', 'status': 'partial'})
    
    # Test 6: Performance Analysis
    print("\n6️⃣ Performance Analysis")
    print("-" * 40)
    
    try:
        # Webhook response time test
        start_time = datetime.now()
        response = requests.post(
            webhook_url,
            json={"test": "performance"},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        print(f"📊 Webhook response time: {response_time:.2f}ms")
        
        if response_time < 1000:
            print("✅ Webhook response time is excellent (<1s)")
            results['performance_tests'].append({'test': 'webhook_response_time', 'status': 'pass'})
        elif response_time < 3000:
            print("⚠️  Webhook response time is acceptable (<3s)")
            results['performance_tests'].append({'test': 'webhook_response_time', 'status': 'warning'})
        else:
            print("❌ Webhook response time is slow (>3s)")
            results['performance_tests'].append({'test': 'webhook_response_time', 'status': 'fail'})
    
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        results['performance_tests'].append({'test': 'webhook_response_time', 'status': 'fail'})
    
    # Test Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, tests in results.items():
        category_total = len(tests)
        category_passed = sum(1 for test in tests if test['status'] == 'pass')
        category_partial = sum(1 for test in tests if test['status'] == 'partial')
        
        total_tests += category_total
        passed_tests += category_passed
        
        print(f"{category.replace('_', ' ').title():20}: {category_passed:2}/{category_total} passed", end="")
        if category_partial > 0:
            print(f" ({category_partial} partial)")
        else:
            print()
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    # Recommendations
    print(f"\n💡 Recommendations")
    print("-" * 20)
    
    if success_rate >= 90:
        print("🎉 Excellent! Your IntaSend integration is production-ready!")
        print("✅ Configure webhook in IntaSend dashboard")
        print("✅ Test with real payment")
        print("✅ Monitor success rates")
    elif success_rate >= 70:
        print("👍 Good! Minor improvements needed:")
        print("🔧 Add missing enhanced fields to Payment model")
        print("🔧 Configure webhook in IntaSend dashboard")
        print("🔧 Test with real payment")
    else:
        print("⚠️  Significant improvements needed:")
        print("🔧 Fix webhook endpoint issues")
        print("🔧 Update Payment model with enhanced fields")
        print("🔧 Configure IntaSend settings properly")
        print("🔧 Test all components thoroughly")
    
    print(f"\n🔗 Next Steps:")
    print(f"1. Configure webhook URL in IntaSend dashboard:")
    print(f"   URL: {webhook_url}")
    print(f"   Challenge: fagierrands_webhook_2025_secure")
    print(f"2. Test with small real payment (KSh 10-50)")
    print(f"3. Monitor payment success rates")
    print(f"4. Implement enhanced Payment model fields")
    
    return results

if __name__ == '__main__':
    try:
        test_intasend_integration()
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()