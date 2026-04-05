#!/usr/bin/env python
"""
Demo script for Email Verification System
Run this script to see how the email verification system works.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import EmailVerification
from accounts.email_utils import send_verification_email, verify_email_token
from django.utils import timezone

User = get_user_model()

def demo_email_verification():
    print("🚀 Email Verification System Demo")
    print("=" * 50)
    
    # Create a test user
    print("\n1. Creating test user...")
    test_email = "demo@example.com"
    
    # Delete existing user if exists
    User.objects.filter(email=test_email).delete()
    
    user = User.objects.create_user(
        username='demouser',
        email=test_email,
        password='demopass123',
        first_name='Demo',
        last_name='User'
    )
    print(f"✅ Created user: {user.username} ({user.email})")
    print(f"   Email verified: {user.email_verified}")
    
    # Create email verification
    print("\n2. Creating email verification token...")
    verification = EmailVerification.objects.create(user=user)
    print(f"✅ Created verification token: {verification.token}")
    print(f"   Expires at: {verification.expires_at}")
    print(f"   Is expired: {verification.is_expired()}")
    print(f"   Is used: {verification.is_used}")
    
    # Simulate email verification
    print("\n3. Simulating email verification...")
    success, message, verified_user = verify_email_token(verification.token)
    
    if success:
        print(f"✅ {message}")
        print(f"   User email verified: {verified_user.email_verified}")
        
        # Check verification status
        verification.refresh_from_db()
        print(f"   Token is now used: {verification.is_used}")
    else:
        print(f"❌ {message}")
    
    # Try to verify again (should fail)
    print("\n4. Trying to verify again with same token...")
    success, message, verified_user = verify_email_token(verification.token)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    # Show verification URLs
    print("\n5. Email verification URLs:")
    print(f"   Verification URL: /api/accounts/verify-email/{verification.token}/")
    print(f"   Resend URL: /api/accounts/resend-verification/")
    print(f"   Check status URL: /api/accounts/check-email-verification/")
    
    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("1. Configure email settings in environment variables")
    print("2. Test with real email by registering a new user")
    print("3. Check the admin panel for verification management")
    
    # Cleanup
    print("\n🧹 Cleaning up demo data...")
    user.delete()
    print("✅ Demo user deleted")

if __name__ == "__main__":
    demo_email_verification()