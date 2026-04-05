#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.serializers import AssistantVerificationSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

def test_service_provider_validation():
    print("=== Testing Service Provider Validation ===")
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser_verification',
        email='test_verification@example.com',
        password='testpass123',
        user_type='assistant'
    )
    
    # Test data for service provider
    test_cases = [
        {
            'name': 'Valid service provider with service',
            'data': {
                'user': user.id,
                'user_role': 'service_provider',
                'full_name': 'Test Provider',
                'id_number': '123456789',
                'phone_number': '+1234567890',
                'area_of_operation': 'Test Area',
                'years_of_experience': 'a_year',
                'service': 'Plumbing',  # Valid service
                'id_front_url': 'https://example.com/id_front.jpg',
                'id_back_url': 'https://example.com/id_back.jpg',
                'selfie_url': 'https://example.com/selfie.jpg',
                'certificate_url': 'https://example.com/certificate.jpg',
            }
        },
        {
            'name': 'Service provider with empty service',
            'data': {
                'user': user.id,
                'user_role': 'service_provider',
                'full_name': 'Test Provider',
                'id_number': '123456789',
                'phone_number': '+1234567890',
                'area_of_operation': 'Test Area',
                'years_of_experience': 'a_year',
                'service': '',  # Empty service
                'id_front_url': 'https://example.com/id_front.jpg',
                'id_back_url': 'https://example.com/id_back.jpg',
                'selfie_url': 'https://example.com/selfie.jpg',
                'certificate_url': 'https://example.com/certificate.jpg',
            }
        },
        {
            'name': 'Service provider without service field',
            'data': {
                'user': user.id,
                'user_role': 'service_provider',
                'full_name': 'Test Provider',
                'id_number': '123456789',
                'phone_number': '+1234567890',
                'area_of_operation': 'Test Area',
                'years_of_experience': 'a_year',
                # No service field
                'id_front_url': 'https://example.com/id_front.jpg',
                'id_back_url': 'https://example.com/id_back.jpg',
                'selfie_url': 'https://example.com/selfie.jpg',
                'certificate_url': 'https://example.com/certificate.jpg',
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        serializer = AssistantVerificationSerializer(data=test_case['data'])
        
        print(f"Is valid: {serializer.is_valid()}")
        
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
        else:
            print("✅ Validation passed")
    
    # Clean up
    user.delete()
    print("\n🧹 Test user cleaned up")

if __name__ == "__main__":
    test_service_provider_validation()