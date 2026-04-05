#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.serializers import RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

def test_registration_direct():
    print("=== Testing Registration Serializer Directly ===")
    
    # Test data similar to what the frontend sends
    import time
    timestamp = str(int(time.time()))
    test_data = {
        'username': f'testuser{timestamp}',
        'email': f'test{timestamp}@example.com',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '+1234567890',
        'user_type': 'user',
        'referral_code': '',  # Empty referral code
    }
    
    try:
        # Test the serializer directly
        serializer = RegisterSerializer(data=test_data)
        
        print(f"Is valid: {serializer.is_valid()}")
        
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
            return
        
        # Try to create the user
        user = serializer.save()
        print(f"✅ User created successfully: {user.username}")
        print(f"User ID: {user.id}")
        print(f"User type: {user.user_type}")
        
        # Clean up - delete the test user
        user.delete()
        print("🧹 Test user cleaned up")
        
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registration_direct()