#!/usr/bin/env python
"""
Script to help identify which account a user should use
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

def analyze_user_accounts():
    """Analyze the duplicate user accounts"""
    email = "wayneryan164@gmail.com"
    users = User.objects.filter(email=email).order_by('-date_joined')
    
    print("=" * 60)
    print(f"ACCOUNT ANALYSIS FOR: {email}")
    print("=" * 60)
    
    for i, user in enumerate(users, 1):
        print(f"\n🔍 Account {i}:")
        print(f"   Username: {user.username}")
        print(f"   User ID: {user.id}")
        print(f"   User Type: {user.user_type}")
        print(f"   Is Staff: {user.is_staff}")
        print(f"   Is Superuser: {user.is_superuser}")
        print(f"   Date Joined: {user.date_joined}")
        print(f"   Last Login: {user.last_login or 'Never'}")
        print(f"   Is Active: {user.is_active}")
        
        # Check for related data
        try:
            from orders.models import Order
            order_count = Order.objects.filter(user=user).count()
            print(f"   Orders: {order_count}")
        except:
            print(f"   Orders: Unable to check")
        
        # Determine account purpose
        if user.is_staff or user.is_superuser:
            print(f"   🔑 Type: ADMIN ACCOUNT")
        else:
            print(f"   👤 Type: Regular User Account")
        
        # Check which account is more likely to be the "main" account
        if i == 1:  # Most recent
            print(f"   📅 Status: MOST RECENT (used by login system)")
        else:
            print(f"   📅 Status: Older account")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    recent_user = users.first()
    older_user = users.last() if users.count() > 1 else None
    
    if older_user and older_user.is_staff:
        print("🤔 SITUATION ANALYSIS:")
        print(f"   - You have an ADMIN account (username: {older_user.username})")
        print(f"   - You have a REGULAR account (username: {recent_user.username})")
        print(f"   - The system will use the REGULAR account for login")
        print()
        print("💡 SOLUTIONS:")
        print("   1. Use the REGULAR account password if you remember it")
        print("   2. Reset password for the REGULAR account")
        print("   3. Delete the duplicate account you don't need")
        print("   4. Log in with the ADMIN account using username instead of email")
    else:
        print("💡 SOLUTIONS:")
        print("   1. Try to remember the password for the most recent account")
        print("   2. Reset password for your account")
        print("   3. Clean up duplicate accounts")

def suggest_immediate_fix():
    """Suggest immediate fixes"""
    print("\n" + "=" * 60)
    print("IMMEDIATE FIXES AVAILABLE")
    print("=" * 60)
    
    print("🔧 Option 1: Reset password for the current account")
    print("   - This will allow you to log in immediately")
    print("   - Run the password reset script")
    print()
    
    print("🔧 Option 2: Log in with username instead of email")
    print("   - Try logging in with 'admin' as username if you remember that password")
    print("   - Try logging in with 'wayneryan164' as username if you remember that password")
    print()
    
    print("🔧 Option 3: Use the admin panel")
    print("   - If you have access to Django admin, you can reset passwords there")

if __name__ == '__main__':
    analyze_user_accounts()
    suggest_immediate_fix()