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
from django.conf import settings

User = get_user_model()

def test_comprehensive_registration():
    print("=== Comprehensive Registration Test ===")
    print(f"Current DEBUG setting: {settings.DEBUG}")
    print(f"Current ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print()
    
    # Test with the exact data structure the frontend sends
    client = Client()
    
    import time
    timestamp = str(int(time.time()))
    
    # This matches exactly what the frontend SignUp.js sends
    frontend_data = {
        'username': f'testuser{timestamp}',
        'email': f'test{timestamp}@example.com',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '+1234567890',
        'user_type': 'user',  # This is what the frontend sends for 'Client'
        'referral_code': '',  # Empty referral code
    }
    
    print("=== Test 1: Valid Registration Data ===")
    print(f"Sending data: {json.dumps(frontend_data, indent=2)}")
    
    try:
        response = client.post(
            '/api/accounts/register/',
            data=json.dumps(frontend_data),
            content_type='application/json',
            HTTP_HOST='testserver'  # Explicitly set host
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            try:
                response_data = response.json()
                print(f"✅ SUCCESS! Response JSON: {json.dumps(response_data, indent=2)}")
                
                # Verify user was created
                user = User.objects.get(username=frontend_data['username'])
                print(f"✅ User created in database: {user.username}")
                print(f"   - Email: {user.email}")
                print(f"   - First Name: {user.first_name}")
                print(f"   - Last Name: {user.last_name}")
                print(f"   - User Type: {getattr(user, 'user_type', 'Not set')}")
                
                # Check if profile was created
                try:
                    from accounts.models import UserProfile
                    profile = UserProfile.objects.get(user=user)
                    print(f"✅ Profile created: {profile}")
                except:
                    print("⚠️ No profile created or UserProfile model not found")
                
                # Clean up
                user.delete()
                print("🧹 Test user cleaned up")
                
            except Exception as e:
                print(f"❌ Error parsing response: {e}")
                print(f"Raw response: {response.content.decode()}")
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            try:
                response_data = response.json()
                print(f"Error JSON: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Raw response: {response.content.decode()}")
                
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)
    
    # Test 2: Invalid data to check error handling
    print("=== Test 2: Invalid Registration Data (Error Handling) ===")
    
    invalid_data = {
        'username': '',  # Invalid: empty
        'email': 'invalid-email',  # Invalid: bad format
        'password': '123',  # Invalid: too short
        'password2': '456',  # Invalid: doesn't match
        'first_name': '',
        'last_name': '',
        'phone_number': '',
        'user_type': 'invalid_type',
        'referral_code': '',
    }
    
    print(f"Sending invalid data: {json.dumps(invalid_data, indent=2)}")
    
    try:
        response = client.post(
            '/api/accounts/register/',
            data=json.dumps(invalid_data),
            content_type='application/json',
            HTTP_HOST='testserver'
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            try:
                response_data = response.json()
                print(f"✅ Proper validation errors returned: {json.dumps(response_data, indent=2)}")
            except:
                print(f"❌ Expected JSON error response but got: {response.content.decode()}")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
    
    print("\n" + "="*50)
    
    # Test 3: Assistant registration
    print("=== Test 3: Assistant Registration ===")
    
    assistant_data = {
        'username': f'assistant{timestamp}',
        'email': f'assistant{timestamp}@example.com',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'first_name': 'Assistant',
        'last_name': 'User',
        'phone_number': '+1234567890',
        'user_type': 'assistant',  # This is what the frontend sends for 'Assistant'
        'referral_code': '',
    }
    
    print(f"Sending assistant data: {json.dumps(assistant_data, indent=2)}")
    
    try:
        response = client.post(
            '/api/accounts/register/',
            data=json.dumps(assistant_data),
            content_type='application/json',
            HTTP_HOST='testserver'
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            try:
                response_data = response.json()
                print(f"✅ Assistant registration successful: {json.dumps(response_data, indent=2)}")
                
                # Clean up
                user = User.objects.get(username=assistant_data['username'])
                user.delete()
                print("🧹 Assistant test user cleaned up")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ Assistant registration failed")
            try:
                response_data = response.json()
                print(f"Error: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Raw response: {response.content.decode()}")
                
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_comprehensive_registration()