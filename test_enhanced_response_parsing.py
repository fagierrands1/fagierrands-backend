#!/usr/bin/env python
"""
Test Enhanced IntaSend Response Parsing
Verify the fix handles different response formats
"""

def test_enhanced_parsing():
    """Test the enhanced response parsing functions"""
    
    print("🧪 Testing Enhanced IntaSend Response Parsing")
    print("=" * 50)
    
    # Define the parsing functions (same as in views_payment.py)
    def get_invoice_id_from_response(response):
        """Enhanced invoice ID extraction from IntaSend response"""
        return (
            response.get('invoice', {}).get('id') or
            response.get('invoice_id') or
            response.get('data', {}).get('invoice_id') or
            response.get('invoice', {}).get('invoice_id')
        )
    
    def get_state_from_response(response):
        """Enhanced state extraction from IntaSend response"""
        return (
            response.get('invoice', {}).get('state') or
            response.get('state') or
            response.get('data', {}).get('state') or
            response.get('status')
        )
    
    # Test different response formats
    test_cases = [
        {
            "name": "Format 1: Nested Invoice (Original Expected)",
            "response": {
                "id": "checkout_123",
                "invoice": {
                    "id": "invoice_456",
                    "state": "PENDING"
                }
            },
            "expected_invoice_id": "invoice_456",
            "expected_state": "PENDING"
        },
        {
            "name": "Format 2: Direct Fields",
            "response": {
                "id": "checkout_789",
                "invoice_id": "invoice_101112",
                "state": "PROCESSING"
            },
            "expected_invoice_id": "invoice_101112",
            "expected_state": "PROCESSING"
        },
        {
            "name": "Format 3: Nested in Data",
            "response": {
                "id": "checkout_456",
                "data": {
                    "invoice_id": "invoice_131415",
                    "state": "PENDING"
                }
            },
            "expected_invoice_id": "invoice_131415",
            "expected_state": "PENDING"
        },
        {
            "name": "Format 4: Alternative Nesting",
            "response": {
                "id": "checkout_789",
                "invoice": {
                    "invoice_id": "invoice_161718",
                    "status": "PROCESSING"
                }
            },
            "expected_invoice_id": "invoice_161718",
            "expected_state": "PROCESSING"
        },
        {
            "name": "Format 5: Status Instead of State",
            "response": {
                "id": "checkout_999",
                "invoice_id": "invoice_192021",
                "status": "PENDING"
            },
            "expected_invoice_id": "invoice_192021",
            "expected_state": "PENDING"
        },
        {
            "name": "Format 6: Your Actual Case (Missing Invoice ID)",
            "response": {
                "id": "ee1b03f4-e618-4eff-b4c1-f5b64e24324b",
                "invoice": {
                    "state": "PENDING"
                    # Missing 'id' field - this was your issue
                }
            },
            "expected_invoice_id": None,
            "expected_state": "PENDING"
        }
    ]
    
    # Run tests
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        response = test_case['response']
        expected_invoice_id = test_case['expected_invoice_id']
        expected_state = test_case['expected_state']
        
        # Test invoice ID extraction
        actual_invoice_id = get_invoice_id_from_response(response)
        invoice_id_correct = actual_invoice_id == expected_invoice_id
        
        # Test state extraction
        actual_state = get_state_from_response(response)
        state_correct = actual_state == expected_state
        
        # Results
        print(f"   Response: {response}")
        print(f"   Expected Invoice ID: {expected_invoice_id}")
        print(f"   Actual Invoice ID:   {actual_invoice_id}")
        print(f"   Invoice ID Test:     {'✅ PASS' if invoice_id_correct else '❌ FAIL'}")
        
        print(f"   Expected State: {expected_state}")
        print(f"   Actual State:   {actual_state}")
        print(f"   State Test:     {'✅ PASS' if state_correct else '❌ FAIL'}")
        
        if invoice_id_correct and state_correct:
            print(f"   Overall: ✅ PASS")
            passed_tests += 1
        else:
            print(f"   Overall: ❌ FAIL")
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 20)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! Enhanced parsing is working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Review the parsing logic.")
    
    # Specific analysis for your case
    print(f"\n🔍 Analysis of Your Issue (Format 6):")
    print("-" * 35)
    print("Your IntaSend response likely looked like:")
    print("  - Checkout ID: Present ✅")
    print("  - Invoice ID: Missing ❌ (this was the problem)")
    print("  - State: Present ✅")
    print("")
    print("With enhanced parsing:")
    print("  - Will extract whatever is available")
    print("  - Will log complete response for debugging")
    print("  - Will handle gracefully if invoice ID is missing")
    print("  - Will still allow webhook to work with checkout ID")

if __name__ == '__main__':
    test_enhanced_parsing()
    
    print(f"\n💡 Next Steps:")
    print("-" * 15)
    print("1. ✅ Enhanced parsing is now in your code")
    print("2. 🧪 Test with new payment using Postman")
    print("3. 📊 Check logs for complete IntaSend response")
    print("4. 🔗 Configure webhook in IntaSend dashboard")
    print("5. 🎯 Monitor success rates")