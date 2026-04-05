#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.models import User, EmailVerification
from accounts.email_utils import send_verification_email

def test_email_verification_fix():
    print("Testing EmailVerification fix...")
    
    # Test 1: Create EmailVerification object directly
    print("\n1. Testing direct EmailVerification creation:")
    user = User.objects.first()
    if user:
        verification = EmailVerification.objects.create(user=user)
        print(f"   ✓ Created verification with expires_at: {verification.expires_at}")
        print(f"   ✓ Is expired: {verification.is_expired()}")
        verification.delete()  # Clean up
    else:
        print("   ✗ No users found in database")
    
    # Test 2: Test email sending function
    print("\n2. Testing send_verification_email function:")
    test_user = User.objects.filter(email='r.wayne@zova.co.ke').first()
    if test_user:
        print(f"   Found user: {test_user.email}")
        try:
            result = send_verification_email(test_user)
            print(f"   ✓ Email sending result: {result}")
            
            # Check if verification was created properly
            verification = EmailVerification.objects.filter(user=test_user, is_used=False).first()
            if verification:
                print(f"   ✓ Verification created with expires_at: {verification.expires_at}")
                print(f"   ✓ Token: {verification.token}")
            else:
                print("   ✗ No verification object found")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
    else:
        print("   ✗ User r.wayne@zova.co.ke not found")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_email_verification_fix()