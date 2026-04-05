#!/usr/bin/env python
import os
import sys
import django
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@override_settings(ALLOWED_HOSTS=['*'])
def test_registration_endpoint():
    print("=== Testing Registration Endpoint with Override ===")
    
    client = Client()
    
    # Test data similar to what the frontend sends
    import time
    timestamp = str(int(time.time()))
    test_data = {
        'username': f'testuser{timestamp}',
        'email': f'test{timestamp}@example.com',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '+1234567890',
        'user_type': 'user',
        'referral_code': '',  # Empty referral code
    }
    
    try:
        print(f"Sending data: {json.dumps(test_data, indent=2)}")
        
        # Make the POST request to the registration endpoint
        response = client.post(
            '/api/accounts/register/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Try to parse JSON response if possible
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Content (raw): {response.content.decode()}")
        
        if response.status_code == 500:
            print("❌ 500 Internal Server Error detected!")
        elif response.status_code == 201:
            print("✅ Registration successful!")
            # Clean up - delete the test user
            try:
                user = User.objects.get(username=test_data['username'])
                user.delete()
                print("🧹 Test user cleaned up")
            except User.DoesNotExist:
                pass
        elif response.status_code == 400:
            print("❌ 400 Bad Request - validation error")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registration_endpoint()