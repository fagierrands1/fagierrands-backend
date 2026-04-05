#!/usr/bin/env python
"""
Setup script for Postman testing
This script prepares the system for email verification testing
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import EmailVerification
from django.conf import settings

User = get_user_model()

def setup_postman_testing():
    print("🔧 Setting up Postman Testing Environment")
    print("=" * 50)
    
    # 1. Configure email backend for testing
    print("\n1. Configuring email backend for testing...")
    print("   Current EMAIL_BACKEND:", settings.EMAIL_BACKEND)
    
    if 'console' not in settings.EMAIL_BACKEND.lower():
        print("   💡 Tip: For testing without real emails, add this to settings.py:")
        print("   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")
    
    # 2. Create a test user for Postman
    print("\n2. Creating test user for Postman...")
    test_email = "postman@test.com"
    test_username = "postmantest"
    
    # Delete existing test user if exists
    User.objects.filter(username=test_username).delete()
    User.objects.filter(email=test_email).delete()
    
    user = User.objects.create_user(
        username=test_username,
        email=test_email,
        password='testpass123',
        first_name='Postman',
        last_name='Test'
    )
    print(f"   ✅ Created test user: {user.username} ({user.email})")
    
    # 3. Create verification token
    print("\n3. Creating verification token...")
    verification = EmailVerification.objects.create(user=user)
    print(f"   ✅ Token created: {verification.token}")
    print(f"   📅 Expires: {verification.expires_at}")
    
    # 4. Display testing information
    print("\n4. Postman Testing Information:")
    print("   📋 Collection file: Fagi_Errands_Email_Verification.postman_collection.json")
    print("   🌐 Base URL: http://localhost:8000")
    print("   👤 Test Username:", test_username)
    print("   📧 Test Email:", test_email)
    print("   🔑 Test Password: testpass123")
    print("   🎫 Verification Token:", verification.token)
    
    # 5. Display verification URL
    verification_url = f"http://localhost:8000/api/accounts/verify-email/{verification.token}/"
    print(f"\n5. Manual Verification URL:")
    print(f"   {verification_url}")
    
    # 6. Display API endpoints
    print("\n6. API Endpoints to test:")
    endpoints = [
        ("POST", "/api/accounts/register/", "Register new user"),
        ("POST", "/api/accounts/login/", "Login user"),
        ("GET", "/api/accounts/check-email-verification/", "Check verification status"),
        ("POST", "/api/accounts/resend-verification/", "Resend verification email"),
        ("GET", f"/api/accounts/verify-email/{verification.token}/", "Verify email (browser)")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:4} {endpoint:40} - {description}")
    
    # 7. Environment variables for Postman
    print("\n7. Postman Environment Variables:")
    env_vars = {
        "base_url": "http://localhost:8000",
        "test_email": test_email,
        "test_username": test_username,
        "verification_token": str(verification.token)
    }
    
    for key, value in env_vars.items():
        print(f"   {key}: {value}")
    
    print("\n🚀 Setup Complete!")
    print("\nNext Steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Import the Postman collection")
    print("3. Set up environment variables in Postman")
    print("4. Run the requests in order")
    print("5. Test the verification URL in browser")
    
    return {
        'user': user,
        'verification_token': verification.token,
        'verification_url': verification_url
    }

if __name__ == "__main__":
    setup_postman_testing()