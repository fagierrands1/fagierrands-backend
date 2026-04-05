#!/usr/bin/env python
import os
import sys
import django

# Add the project path to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from admin_dashboard.views import DashboardOverviewView
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

def test_dashboard_overview():
    try:
        # Create a request factory
        factory = RequestFactory()
        
        # Create a mock user with admin privileges
        user = User(username='testadmin', is_staff=True, is_superuser=True)
        
        # Create a GET request
        request = factory.get('/api/dashboard/overview/')
        request.user = user
        
        # Create the view and call it
        view = DashboardOverviewView()
        response = view.get(request)
        
        print("Dashboard Overview View Test:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Data Keys: {list(response.data.keys()) if hasattr(response, 'data') else 'No data'}")
        
        if response.status_code == 200:
            print("✓ View is working correctly")
        else:
            print("✗ View returned an error")
            print(f"Response: {response.data if hasattr(response, 'data') else 'No data'}")
            
    except Exception as e:
        print(f"✗ Error testing dashboard view: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_dashboard_overview()