#!/usr/bin/env python
"""
Test script to verify login with proper credentials
"""
import os
import sys
import django
from django.conf import settings

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json

User = get_user_model()

def test_login_with_valid_credentials():
    """Test login with valid credentials"""
    client = APIClient()
    
    # Get an existing user
    user = User.objects.first()
    if not user:
        print("No users found in database")
        return
    
    print(f"Testing with user: {user.email}")
    
    # Set a known password for this user for testing
    user.set_password('testpassword123')
    user.save()
    print("Password set for user")
    
    # Test login
    login_data = {
        'email': user.email,
        'password': 'testpassword123'
    }
    
    try:
        response = client.post('/api/accounts/login/', login_data, format='json')
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            print("Response data keys:", list(response.data.keys()))
        else:
            print("❌ Login failed!")
            print("Response data:", response.data)
            
    except Exception as e:
        print(f"Exception during login: {str(e)}")
        import traceback
        traceback.print_exc()

def test_malformed_request():
    """Test with malformed request to reproduce 500 error"""
    client = APIClient()
    
    print("\nTesting malformed requests...")
    
    # Test with empty data
    try:
        response = client.post('/api/accounts/login/', {}, format='json')
        print(f"Empty data - Status: {response.status_code}")
    except Exception as e:
        print(f"Empty data caused exception: {e}")
    
    # Test with None values
    try:
        response = client.post('/api/accounts/login/', {'email': None, 'password': None}, format='json')
        print(f"None values - Status: {response.status_code}")
    except Exception as e:
        print(f"None values caused exception: {e}")
    
    # Test with invalid JSON
    try:
        response = client.post('/api/accounts/login/', 'invalid json', content_type='application/json')
        print(f"Invalid JSON - Status: {response.status_code}")
    except Exception as e:
        print(f"Invalid JSON caused exception: {e}")

if __name__ == '__main__':
    test_login_with_valid_credentials()
    test_malformed_request()