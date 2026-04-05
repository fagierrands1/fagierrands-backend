#!/usr/bin/env python
"""
Test script to verify IntaSend webhook endpoint is working correctly
"""

import requests
import json
import time

def test_webhook_endpoint():
    """Test the webhook endpoint with various payloads"""
    
    webhook_url = "https://fagierrands-server.vercel.app/api/orders/payments/webhook/"
    
    print("🧪 Testing IntaSend Webhook Endpoint")
    print("=" * 50)
    print(f"Webhook URL: {webhook_url}")
    print()
    
    # Test payloads for different events
    test_cases = [
        {
            "name": "Payment Completed",
            "payload": {
                "event": "payment.completed",
                "data": {
                    "invoice": {
                        "id": "test-invoice-completed-123"
                    },
                    "mpesa_receipt": "TEST123456789",
                    "amount": 100.00,
                    "currency": "KES"
                }
            }
        },
        {
            "name": "Payment Failed",
            "payload": {
                "event": "payment.failed",
                "data": {
                    "invoice": {
                        "id": "test-invoice-failed-456"
                    },
                    "reason": "Insufficient funds"
                }
            }
        },
        {
            "name": "Payment Cancelled",
            "payload": {
                "event": "payment.cancelled",
                "data": {
                    "invoice": {
                        "id": "test-invoice-cancelled-789"
                    },
                    "reason": "User cancelled"
                }
            }
        },
        {
            "name": "Unknown Event",
            "payload": {
                "event": "payment.unknown",
                "data": {
                    "invoice": {
                        "id": "test-invoice-unknown-999"
                    }
                }
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                webhook_url,
                json=test_case['payload'],
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'IntaSend-Webhook-Test'
                },
                timeout=10
            )
            
            result = {
                'test': test_case['name'],
                'status_code': response.status_code,
                'response': response.text,
                'success': response.status_code == 200
            }
            
            if result['success']:
                print(f"   ✅ Status: {response.status_code}")
                print(f"   ✅ Response: {response.text}")
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   ❌ Response: {response.text}")
            
            results.append(result)
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'test': test_case['name'],
                'status_code': None,
                'response': str(e),
                'success': False
            })
        
        print()
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("📊 Test Summary")
    print("-" * 30)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("\n🎉 All tests passed! Webhook endpoint is working correctly.")
        print("\n✅ Next steps:")
        print("1. Configure webhook URL in IntaSend dashboard")
        print("2. Enable payment events (completed, failed, cancelled)")
        print("3. Test with real payment to verify end-to-end flow")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} tests failed. Check webhook endpoint configuration.")
    
    return results

def test_webhook_accessibility():
    """Test if webhook endpoint is accessible"""
    
    print("\n🌐 Testing Webhook Accessibility")
    print("-" * 40)
    
    base_url = "https://fagierrands-server.vercel.app"
    endpoints_to_test = [
        "/",
        "/api/",
        "/api/orders/",
        "/api/orders/payments/webhook/"
    ]
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=10)
            print(f"GET {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"GET {endpoint}: ERROR - {str(e)}")

if __name__ == '__main__':
    try:
        # Test webhook accessibility
        test_webhook_accessibility()
        
        # Test webhook endpoint
        test_webhook_endpoint()
        
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()