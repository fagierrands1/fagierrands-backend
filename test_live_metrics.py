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

from admin_dashboard.views import LiveMetricsView, DashboardOverviewView
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

def test_live_metrics():
    try:
        # Create a request factory
        factory = RequestFactory()
        
        # Create a mock user with admin privileges
        user = User(username='testadmin', is_staff=True, is_superuser=True)
        
        # Test Live Metrics View
        print("=== TESTING LIVE METRICS VIEW ===")
        request = factory.get('/api/dashboard/live-metrics/')
        request.user = user
        
        view = LiveMetricsView()
        response = view.get(request)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Live Metrics View is working!")
            print("Response Data:")
            for key, value in response.data.items():
                print(f"  {key}: {value}")
        else:
            print("✗ Live Metrics View returned an error")
            print(f"Response: {response.data if hasattr(response, 'data') else 'No data'}")
        
        print("\n" + "="*50 + "\n")
        
        # Test Dashboard Overview View
        print("=== TESTING DASHBOARD OVERVIEW VIEW ===")
        request = factory.get('/api/dashboard/overview/')
        request.user = user
        
        view = DashboardOverviewView()
        response = view.get(request)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Dashboard Overview View is working!")
            print("Key Metrics:")
            data = response.data
            print(f"  Total Users: {data.get('total_users', 'N/A')}")
            print(f"  Total Orders: {data.get('total_orders', 'N/A')}")
            print(f"  Total Revenue: {data.get('total_revenue', 'N/A')}")
            print(f"  Completed Orders (30 days): {data.get('completed_orders_last_30_days', 'N/A')}")
            print(f"  Average Order Value: {data.get('avg_order_value', 'N/A')}")
        else:
            print("✗ Dashboard Overview View returned an error")
            print(f"Response: {response.data if hasattr(response, 'data') else 'No data'}")
            
    except Exception as e:
        print(f"✗ Error testing views: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_live_metrics()