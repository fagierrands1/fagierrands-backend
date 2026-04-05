#!/usr/bin/env python
"""
Debug script to investigate authentication issues
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

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password

User = get_user_model()

def debug_user_authentication():
    """Debug authentication for users with duplicate email"""
    email = "wayneryan164@gmail.com"
    
    print("=" * 60)
    print("AUTHENTICATION DEBUG")
    print("=" * 60)
    
    # Get all users with this email
    users = User.objects.filter(email=email).order_by('-date_joined')
    
    print(f"Found {users.count()} users with email: {email}")
    print()
    
    for i, user in enumerate(users):
        print(f"User {i+1}:")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Is Staff: {user.is_staff}")
        print(f"  Is Superuser: {user.is_superuser}")
        print(f"  Date Joined: {user.date_joined}")
        print(f"  Last Login: {user.last_login}")
        print(f"  Password Hash: {user.password[:50]}...")
        print(f"  Has Usable Password: {user.has_usable_password()}")
        
        # Try to authenticate with different passwords
        print(f"  Authentication Tests:")
        
        # Test with common passwords
        test_passwords = ['password', 'admin', 'wayneryan164', 'admin123', 'password123']
        
        for password in test_passwords:
            try:
                auth_result = authenticate(username=user.username, password=password)
                if auth_result:
                    print(f"    ✅ Password '{password}' works!")
                    break
                else:
                    print(f"    ❌ Password '{password}' failed")
            except Exception as e:
                print(f"    ⚠️  Password '{password}' caused error: {e}")
        
        print()
    
    # Check if there are any custom authentication backends
    print("Authentication Backends:")
    for backend in settings.AUTHENTICATION_BACKENDS:
        print(f"  - {backend}")
    
    print()

def test_password_setting():
    """Test setting a new password for the most recent user"""
    email = "wayneryan164@gmail.com"
    users = User.objects.filter(email=email).order_by('-date_joined')
    
    if not users:
        print("No users found with that email")
        return
    
    user = users.first()
    print(f"Setting new password for user: {user.username}")
    
    # Set a known password
    new_password = "temppassword123"
    user.set_password(new_password)
    user.save()
    
    print(f"Password set to: {new_password}")
    
    # Test authentication
    auth_result = authenticate(username=user.username, password=new_password)
    if auth_result:
        print("✅ Authentication successful with new password!")
    else:
        print("❌ Authentication still failing with new password")
    
    # Test direct password check
    if user.check_password(new_password):
        print("✅ Direct password check successful!")
    else:
        print("❌ Direct password check failed")

if __name__ == '__main__':
    debug_user_authentication()
    print("\n" + "=" * 60)
    print("SETTING NEW PASSWORD FOR TESTING")
    print("=" * 60)
    test_password_setting()