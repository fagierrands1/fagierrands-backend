#!/usr/bin/env python
import os
import sys
import django
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import AssistantVerification

User = get_user_model()

def create_test_data():
    """Create test assistants with different verification statuses"""
    print("Creating test data...")
    
    # Create a handler user for testing
    handler, created = User.objects.get_or_create(
        username='testhandler',
        defaults={
            'email': 'handler@test.com',
            'user_type': 'handler',
            'first_name': 'Test',
            'last_name': 'Handler'
        }
    )
    
    # Create test assistants
    assistants_data = [
        {
            'username': 'rider1',
            'email': 'rider1@test.com',
            'user_type': 'assistant',
            'first_name': 'John',
            'last_name': 'Rider',
            'verification': {
                'user_role': 'rider',
                'full_name': 'John Rider',
                'id_number': 'ID123456',
                'phone_number': '+1234567890',
                'area_of_operation': 'Nairobi',
                'years_of_experience': 'more_than_a_year',
                'status': 'verified',
                'driving_license_number': 'DL123456'
            }
        },
        {
            'username': 'serviceprov1',
            'email': 'sp1@test.com',
            'user_type': 'assistant',
            'first_name': 'Jane',
            'last_name': 'Provider',
            'verification': {
                'user_role': 'service_provider',
                'full_name': 'Jane Provider',
                'id_number': 'ID789012',
                'phone_number': '+1234567891',
                'area_of_operation': 'Mombasa',
                'years_of_experience': 'a_year',
                'status': 'pending',
                'service': 'Plumbing'
            }
        },
        {
            'username': 'serviceprov2',
            'email': 'sp2@test.com',
            'user_type': 'assistant',
            'first_name': 'Bob',
            'last_name': 'Electrician',
            'verification': {
                'user_role': 'service_provider',
                'full_name': 'Bob Electrician',
                'id_number': 'ID345678',
                'phone_number': '+1234567892',
                'area_of_operation': 'Kisumu',
                'years_of_experience': 'more_than_a_year',
                'status': 'verified',
                'service': 'Electrical Work'
            }
        }
    ]
    
    for assistant_data in assistants_data:
        verification_data = assistant_data.pop('verification')
        
        user, created = User.objects.get_or_create(
            username=assistant_data['username'],
            defaults=assistant_data
        )
        
        if created or not hasattr(user, 'verification'):
            verification_data['user'] = user
            AssistantVerification.objects.get_or_create(
                user=user,
                defaults=verification_data
            )
    
    print("Test data created successfully!")
    return handler

def test_assistant_list_view():
    """Test the enhanced assistant list view"""
    print("\n=== Testing Assistant List View ===")
    
    handler = create_test_data()
    client = APIClient()
    client.force_authenticate(user=handler)
    
    # Test basic list
    response = client.get('/api/accounts/user/list/')
    print(f"Basic list status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total assistants: {len(data['results']) if 'results' in data else len(data)}")
        
        # Print first assistant details
        assistants = data['results'] if 'results' in data else data
        if assistants:
            first_assistant = assistants[0]
            print(f"First assistant details:")
            print(f"  Name: {first_assistant.get('first_name')} {first_assistant.get('last_name')}")
            print(f"  Role: {first_assistant.get('user_role')}")
            print(f"  Verification Status: {first_assistant.get('verification_status')}")
            print(f"  Service Type: {first_assistant.get('service_type')}")
            print(f"  Area: {first_assistant.get('area_of_operation')}")
    
    # Test filtering by verification status
    print("\nTesting filters...")
    
    # Filter by verified status
    response = client.get('/api/accounts/user/list/?verification_status=verified')
    if response.status_code == 200:
        data = response.json()
        verified_count = len(data['results']) if 'results' in data else len(data)
        print(f"Verified assistants: {verified_count}")
    
    # Filter by user role
    response = client.get('/api/accounts/user/list/?user_role=service_provider')
    if response.status_code == 200:
        data = response.json()
        sp_count = len(data['results']) if 'results' in data else len(data)
        print(f"Service providers: {sp_count}")
    
    # Filter by service type
    response = client.get('/api/accounts/user/list/?service_type=plumbing')
    if response.status_code == 200:
        data = response.json()
        plumber_count = len(data['results']) if 'results' in data else len(data)
        print(f"Plumbers: {plumber_count}")

def test_assistant_stats_view():
    """Test the assistant statistics view"""
    print("\n=== Testing Assistant Stats View ===")
    
    handler = create_test_data()
    client = APIClient()
    client.force_authenticate(user=handler)
    
    response = client.get('/api/accounts/assistants/stats/')
    print(f"Stats status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Statistics:")
        print(f"  Total assistants: {stats.get('total_assistants')}")
        print(f"  Verification status: {stats.get('verification_status')}")
        print(f"  Roles: {stats.get('roles')}")
        print(f"  Service types: {stats.get('service_types')}")
    else:
        print(f"Error: {response.text}")

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    
    test_usernames = ['testhandler', 'rider1', 'serviceprov1', 'serviceprov2']
    for username in test_usernames:
        try:
            user = User.objects.get(username=username)
            user.delete()
            print(f"Deleted user: {username}")
        except User.DoesNotExist:
            pass

if __name__ == "__main__":
    try:
        test_assistant_list_view()
        test_assistant_stats_view()
    finally:
        cleanup_test_data()