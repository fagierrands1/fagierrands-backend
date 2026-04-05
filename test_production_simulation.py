#!/usr/bin/env python
import os
import sys
import django
import json

# Simulate production environment
os.environ['DEBUG'] = 'False'
os.environ['ALLOWED_HOSTS'] = 'fagierrands-server.vercel.app,fagierrands-x9ow.vercel.app,localhost,127.0.0.1,fagierrands.onrender.com,fagierrands.vercel.app,testserver'

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

def test_production_settings():
    print("=== Testing Production Settings ===")
    print(f"DEBUG setting: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print()

@override_settings(DEBUG=False, ALLOWED_HOSTS=['*'])
def test_registration_production_mode():
    print("=== Testing Registration in Production Mode (DEBUG=False) ===")
    
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
            print("This suggests there's still an issue that needs to be fixed.")
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

def test_error_handling():
    print("\n=== Testing Error Handling with Invalid Data ===")
    
    client = Client()
    
    # Test with invalid data to see how errors are handled
    invalid_data = {
        'username': '',  # Invalid: empty username
        'email': 'invalid-email',  # Invalid: bad email format
        'password': '123',  # Invalid: too short
        'password2': '456',  # Invalid: doesn't match
    }
    
    try:
        response = client.post(
            '/api/accounts/register/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        
        # Check if we get proper JSON error response
        try:
            response_data = response.json()
            print(f"Error Response JSON: {json.dumps(response_data, indent=2)}")
            print("✅ Proper JSON error response received")
        except:
            print(f"Response Content (raw): {response.content.decode()}")
            if response.status_code == 400 and 'html' in response.content.decode().lower():
                print("❌ Getting HTML error page instead of JSON - DEBUG might still be True")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_production_settings()
    test_registration_production_mode()
    test_error_handling()