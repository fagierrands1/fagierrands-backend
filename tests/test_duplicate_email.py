#!/usr/bin/env python
"""
Test script to test login with duplicate email addresses
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

def check_duplicate_emails():
    """Check for duplicate email addresses in the database"""
    print("Checking for duplicate email addresses...")
    
    # Find all email addresses that appear more than once
    from django.db.models import Count
    duplicates = User.objects.values('email').annotate(count=Count('email')).filter(count__gt=1)
    
    if duplicates:
        print("Found duplicate email addresses:")
        for dup in duplicates:
            email = dup['email']
            count = dup['count']
            print(f"  - {email}: {count} users")
            
            # Show all users with this email
            users = User.objects.filter(email=email).order_by('-date_joined')
            for i, user in enumerate(users):
                print(f"    {i+1}. {user.username} (joined: {user.date_joined})")
        
        return duplicates
    else:
        print("No duplicate email addresses found.")
        return []

def test_login_with_duplicate_email():
    """Test login with an email that has duplicates"""
    client = APIClient()
    
    duplicates = check_duplicate_emails()
    
    if not duplicates:
        print("No duplicates to test with.")
        return
    
    # Test with the first duplicate email
    test_email = duplicates[0]['email']
    print(f"\nTesting login with duplicate email: {test_email}")
    
    # Set password for all users with this email
    users = User.objects.filter(email=test_email)
    for user in users:
        user.set_password('testpassword123')
        user.save()
    
    print(f"Set password for {users.count()} users with email {test_email}")
    
    # Test login
    login_data = {
        'email': test_email,
        'password': 'testpassword123'
    }
    
    try:
        response = client.post('/api/accounts/login/', login_data, format='json')
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful despite duplicate emails!")
            print("Response data keys:", list(response.data.keys()))
            print("Logged in user ID:", response.data.get('user_id'))
        else:
            print("❌ Login failed!")
            print("Response data:", response.data)
            
    except Exception as e:
        print(f"Exception during login: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_with_duplicate_email()