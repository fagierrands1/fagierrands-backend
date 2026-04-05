#!/usr/bin/env python
"""
Test script to verify dashboard endpoints are working correctly
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

User = get_user_model()

def test_dashboard_endpoints():
    """Test all dashboard endpoints"""
    client = Client()
    
    print("Testing Dashboard Endpoints...")
    print("=" * 50)
    
    # Test admin dashboard overview (should work without auth for testing)
    print("\n1. Testing Admin Dashboard Overview:")
    try:
        response = client.get('/api/dashboard/overview/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Create test users for other endpoints
    try:
        # Create test client user
        client_user = User.objects.create_user(
            username='testclient',
            email='client@test.com',
            password='testpass123',
            user_type='user',
            first_name='Test',
            last_name='Client'
        )
        
        # Create test assistant user
        assistant_user = User.objects.create_user(
            username='testassistant',
            email='assistant@test.com',
            password='testpass123',
            user_type='assistant',
            first_name='Test',
            last_name='Assistant'
        )
        
        # Create test handler user
        handler_user = User.objects.create_user(
            username='testhandler',
            email='handler@test.com',
            password='testpass123',
            user_type='handler',
            first_name='Test',
            last_name='Handler'
        )
        
        print("\n   Test users created successfully")
        
    except Exception as e:
        print(f"   Error creating test users: {str(e)}")
        # Try to get existing users
        try:
            client_user = User.objects.get(username='testclient')
            assistant_user = User.objects.get(username='testassistant')
            handler_user = User.objects.get(username='testhandler')
            print("   Using existing test users")
        except User.DoesNotExist:
            print("   Could not create or find test users")
            return
    
    # Test client stats endpoint
    print("\n2. Testing Client Stats Endpoint:")
    try:
        client.force_login(client_user)
        response = client.get('/api/accounts/client/stats/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test assistant stats endpoint
    print("\n3. Testing Assistant Stats Endpoint:")
    try:
        client.force_login(assistant_user)
        response = client.get('/api/accounts/assistant/dashboard-stats/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test handler stats endpoint
    print("\n4. Testing Handler Stats Endpoint:")
    try:
        client.force_login(handler_user)
        response = client.get('/api/accounts/handler/stats/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test available orders endpoint
    print("\n5. Testing Available Orders Endpoint:")
    try:
        client.force_login(assistant_user)
        response = client.get('/api/orders/available/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available orders count: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"   Error: {response.content.decode()}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Dashboard endpoint testing completed!")

if __name__ == '__main__':
    test_dashboard_endpoints()