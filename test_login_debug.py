#!/usr/bin/env python
"""
Debug script to test the login functionality
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
from rest_framework import status
import json

User = get_user_model()

def test_login_endpoint():
    """Test the login endpoint to identify the issue"""
    client = APIClient()
    
    # First, check if any users exist
    print("Checking users in database...")
    users = User.objects.all()
    print(f"Found {users.count()} users in database")
    
    if users.count() == 0:
        print("No users found. Creating a test user...")
        # Create a test user
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        print(f"Created test user: {test_user.username}")
    else:
        print("Users found:")
        for user in users[:3]:  # Show first 3 users
            print(f"  - {user.username} ({user.email})")
    
    # Test the login endpoint with existing user
    print("\nTesting login endpoint...")
    # Get the first user to test with
    first_user = users.first()
    print(f"Testing with user: {first_user.email}")
    
    login_data = {
        'email': first_user.email,
        'password': 'wrongpassword'  # Using wrong password first to see behavior
    }
    
    try:
        response = client.post('/api/accounts/login/', login_data, format='json')
        print(f"Login response status: {response.status_code}")
        print(f"Login response data: {response.data}")
        
        if response.status_code == 500:
            print("500 error occurred. Checking logs...")
            # Try to get more details about the error
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Exception during login test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_endpoint()