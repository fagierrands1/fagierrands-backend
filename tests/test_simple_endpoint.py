#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from rest_framework.test import APIClient
from django.test import Client

def test_endpoints():
    print("=== Testing Different Endpoints ===")
    
    # Test with DRF APIClient
    api_client = APIClient()
    
    # Test with Django Client
    django_client = Client()
    
    # Test a simple GET request first
    print("\n1. Testing GET request to /api/accounts/register/")
    try:
        response = api_client.get('/api/accounts/register/')
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
        if response.status_code == 405:
            print("   ✅ Method Not Allowed (expected for POST-only endpoint)")
        else:
            print(f"   Response: {response.content.decode()[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test POST with minimal data
    print("\n2. Testing POST with minimal data")
    minimal_data = {
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'testpass123',
        'password2': 'testpass123'
    }
    
    try:
        response = api_client.post('/api/accounts/register/', minimal_data, format='json')
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
        print(f"   Response: {response.content.decode()[:500]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test if the URL resolves correctly
    print("\n3. Testing URL resolution")
    try:
        from django.urls import resolve
        resolved = resolve('/api/accounts/register/')
        print(f"   ✅ URL resolves to: {resolved.func}")
        print(f"   View name: {resolved.view_name}")
    except Exception as e:
        print(f"   ❌ URL resolution error: {e}")

if __name__ == "__main__":
    test_endpoints()