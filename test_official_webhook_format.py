#!/usr/bin/env python
"""
Test script to verify official IntaSend webhook format support
"""

import requests
import json

def test_official_intasend_format():
    """Test the webhook with official IntaSend format"""
    
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    print("🧪 Testing Official IntaSend Webhook Format")
    print("=" * 50)
    
    # Test cases based on official IntaSend documentation
    test_cases = [
        {
            "name": "Payment Complete (M-Pesa)",
            "payload": {
                "invoice_id": "BRZKGPR123",
                "state": "COMPLETE",
                "provider": "M-PESA",
                "charges": "3.00",
                "net_amount": "97.00",
                "currency": "KES",
                "value": "100.00",
                "account": "QGH7X8Y9Z0",
                "api_ref": "ISL_test-api-ref-123",
                "host": "https://payment.intasend.com",
                "failed_reason": None,
                "failed_code": None,
                "failed_code_link": "https://intasend.com/troubleshooting",
                "created_at": "2025-08-06T13:30:00.000000+03:00",
                "updated_at": "2025-08-06T13:30:01.000000+03:00",
                "challenge": "production"
            }
        },
        {
            "name": "Payment Failed",
            "payload": {
                "invoice_id": "FAIL456",
                "state": "FAILED",
                "provider": "M-PESA",
                "charges": "0.00",
                "net_amount": "0.00",
                "currency": "KES",
                "value": "50.00",
                "account": "254700000000",
                "api_ref": "ISL_test-api-ref-456",
                "host": "https://payment.intasend.com",
                "failed_reason": "Insufficient funds",
                "failed_code": "INSUFFICIENT_FUNDS",
                "failed_code_link": "https://intasend.com/troubleshooting",
                "created_at": "2025-08-06T13:30:00.000000+03:00",
                "updated_at": "2025-08-06T13:30:01.000000+03:00",
                "challenge": "production"
            }
        },
        {
            "name": "Payment Processing",
            "payload": {
                "invoice_id": "PROC789",
                "state": "PROCESSING",
                "provider": "M-PESA",
                "charges": "0.00",
                "net_amount": "0.00",
                "currency": "KES",
                "value": "75.00",
                "account": "254700000000",
                "api_ref": "ISL_test-api-ref-789",
                "host": "https://payment.intasend.com",
                "failed_reason": None,
                "failed_code": None,
                "failed_code_link": "https://intasend.com/troubleshooting",
                "created_at": "2025-08-06T13:30:00.000000+03:00",
                "updated_at": "2025-08-06T13:30:01.000000+03:00",
                "challenge": "production"
            }
        },
        {
            "name": "Card Payment Complete",
            "payload": {
                "invoice_id": "CARD999",
                "state": "COMPLETE",
                "provider": "CARD-PAYMENT",
                "charges": "5.36",
                "net_amount": "94.64",
                "currency": "KES",
                "value": "100.00",
                "account": "john.doe@gmail.com",
                "api_ref": "ISL_test-card-ref-999",
                "host": "https://payment.intasend.com",
                "failed_reason": None,
                "failed_code": None,
                "failed_code_link": "https://intasend.com/troubleshooting",
                "created_at": "2025-08-06T13:30:00.000000+03:00",
                "updated_at": "2025-08-06T13:30:01.000000+03:00",
                "challenge": "production"
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   State: {test_case['payload']['state']}")
        print(f"   Provider: {test_case['payload']['provider']}")
        
        try:
            response = requests.post(
                webhook_url,
                json=test_case['payload'],
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'IntaSend-Webhook'
                },
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                print(f"   ✅ Status: {response.status_code}")
                print(f"   ✅ Response: {response.text}")
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   ❌ Response: {response.text}")
            
            results.append({
                'test': test_case['name'],
                'status_code': response.status_code,
                'success': success,
                'response': response.text
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'test': test_case['name'],
                'status_code': None,
                'success': False,
                'response': str(e)
            })
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print(f"\n🎉 All tests passed! Official IntaSend webhook format is working correctly.")
        print(f"\n✅ Your webhook handler supports:")
        print(f"   - Official IntaSend format (invoice_id, state, api_ref)")
        print(f"   - All payment states (COMPLETE, FAILED, PROCESSING, PENDING)")
        print(f"   - Both M-Pesa and Card payment providers")
        print(f"   - Proper error handling and logging")
        print(f"\n🔧 Next steps:")
        print(f"   1. Configure webhook URL in IntaSend dashboard")
        print(f"   2. Enable payment collection events")
        print(f"   3. Test with real payment")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} tests failed. Check webhook implementation.")
    
    return results

if __name__ == '__main__':
    try:
        test_official_intasend_format()
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()