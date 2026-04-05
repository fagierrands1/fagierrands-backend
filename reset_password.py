#!/usr/bin/env python
"""
Quick password reset script
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

User = get_user_model()

def reset_password():
    """Reset password for the admin account"""
    # Use the second admin user to avoid duplicate email issues
    user = User.objects.filter(user_type='admin', username='lll').first()
    
    if not user:
        # Fallback to any admin user
        user = User.objects.filter(user_type='admin').first()
    
    print(f"Resetting password for user: {user.username}")
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    
    # Set a temporary password
    temp_password = "admin123"
    user.set_password(temp_password)
    user.save()
    
    print("\n" + "=" * 50)
    print("PASSWORD RESET SUCCESSFUL!")
    print("=" * 50)
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"New Password: {temp_password}")
    print("=" * 50)
    print("\nSECURITY NOTE:")
    print("   - This is a temporary password")
    print("   - Please change it after logging in")
    print("   - Use this to log in via the app")

if __name__ == '__main__':
    reset_password()