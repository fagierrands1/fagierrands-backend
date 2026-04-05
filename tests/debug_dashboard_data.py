#!/usr/bin/env python
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Add the project path to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from django.db.models import Sum, Count

User = get_user_model()

def debug_database_data():
    print("=== DATABASE DEBUG INFORMATION ===\n")
    
    # Check Users
    print("1. USER DATA:")
    total_users = User.objects.count()
    print(f"   Total Users: {total_users}")
    
    if total_users > 0:
        recent_users = User.objects.order_by('-date_joined')[:5]
        print("   Recent Users:")
        for user in recent_users:
            print(f"     - {user.username} (joined: {user.date_joined}, type: {getattr(user, 'user_type', 'N/A')})")
    print()
    
    # Check Orders
    print("2. ORDER DATA:")
    total_orders = Order.objects.count()
    print(f"   Total Orders: {total_orders}")
    
    if total_orders > 0:
        # Check order statuses
        print("   Orders by Status:")
        statuses = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
        for status in statuses:
            print(f"     - {status['status']}: {status['count']}")
        
        print("\n   Recent Orders:")
        recent_orders = Order.objects.order_by('-created_at')[:5]
        for order in recent_orders:
            print(f"     - ID: {order.id}, Status: {order.status}, Price: {order.price}, Created: {order.created_at}")
            print(f"       Completed: {order.completed_at}, Title: {order.title}")
    
    print()
    
    # Check date ranges for live metrics
    now = timezone.now()
    today = now.date()
    thirty_days_ago = today - timedelta(days=30)
    
    print("3. DATE RANGE ANALYSIS:")
    print(f"   Today: {today}")
    print(f"   30 days ago: {thirty_days_ago}")
    print(f"   Current time: {now}")
    
    # Check orders in different time ranges
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_last_30_days = Order.objects.filter(created_at__date__gte=thirty_days_ago).count()
    completed_today = Order.objects.filter(status='completed', completed_at__date=today).count()
    completed_last_30_days = Order.objects.filter(status='completed', completed_at__date__gte=thirty_days_ago).count()
    
    print(f"   Orders created today: {orders_today}")
    print(f"   Orders created in last 30 days: {orders_last_30_days}")
    print(f"   Orders completed today: {completed_today}")
    print(f"   Orders completed in last 30 days: {completed_last_30_days}")
    
    # Check revenue
    revenue_today = Order.objects.filter(
        status='completed', 
        completed_at__date=today
    ).aggregate(total=Sum('price'))['total'] or 0
    
    total_revenue = Order.objects.filter(status='completed').aggregate(total=Sum('price'))['total'] or 0
    
    print(f"   Revenue today: {revenue_today}")
    print(f"   Total revenue: {total_revenue}")
    
    print()
    
    # Check what statuses are actually being used
    print("4. LIVE METRICS SIMULATION:")
    active_orders = Order.objects.filter(status__in=['pending', 'accepted', 'in_progress']).count()
    print(f"   Active orders (pending/accepted/in_progress): {active_orders}")
    
    # Check if there are orders with different status names
    all_statuses = Order.objects.values_list('status', flat=True).distinct()
    print(f"   All unique statuses in database: {list(all_statuses)}")
    
    # Check users logged in recently
    recent_login_users = User.objects.filter(last_login__gte=now - timedelta(minutes=30)).count()
    print(f"   Users logged in last 30 minutes: {recent_login_users}")
    
    # Check for handyman users
    handyman_users = User.objects.filter(user_type='handyman').count() if hasattr(User.objects.first(), 'user_type') else 0
    print(f"   Handyman users: {handyman_users}")
    
    print("\n=== END DEBUG ===")

if __name__ == '__main__':
    debug_database_data()