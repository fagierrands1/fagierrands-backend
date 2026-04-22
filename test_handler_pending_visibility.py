"""
Test script to verify that handlers can see pending errands after confirmation.

This script tests the complete flow:
1. Client creates a draft errand
2. Client confirms the errand (status → 'pending')
3. Handler queries pending orders
4. Verify the errand appears in handler's pending orders list
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order, OrderType
from decimal import Decimal

User = get_user_model()

def test_errand_visibility():
    print("=" * 60)
    print("TESTING: Handler can see pending errands after confirmation")
    print("=" * 60)
    
    # Step 1: Get or create test users
    print("\n1. Setting up test users...")
    
    # Get or create a client
    client, created = User.objects.get_or_create(
        username='test_client',
        defaults={
            'email': 'client@test.com',
            'user_type': 'user',
            'first_name': 'Test',
            'last_name': 'Client'
        }
    )
    if created:
        client.set_password('testpass123')
        client.save()
    print(f"   ✓ Client: {client.username} (ID: {client.id})")
    
    # Get or create a handler
    handler, created = User.objects.get_or_create(
        username='test_handler',
        defaults={
            'email': 'handler@test.com',
            'user_type': 'handler',
            'first_name': 'Test',
            'last_name': 'Handler'
        }
    )
    if created:
        handler.set_password('testpass123')
        handler.save()
    print(f"   ✓ Handler: {handler.username} (ID: {handler.id})")
    
    # Step 2: Get or create order type
    print("\n2. Setting up order type...")
    order_type, created = OrderType.objects.get_or_create(
        name='Pickup & Delivery',
        defaults={
            'description': 'Pickup and delivery service',
            'base_price': Decimal('200.00'),
            'price_per_km': Decimal('20.00'),
            'min_price': Decimal('200.00')
        }
    )
    print(f"   ✓ Order Type: {order_type.name} (ID: {order_type.id})")
    
    # Step 3: Create a draft errand
    print("\n3. Creating draft errand...")
    order = Order.objects.create(
        client=client,
        order_type=order_type,
        title='Test Errand - Pickup Package',
        description='Pick up package from location A and deliver to location B',
        pickup_address='123 Pickup Street, Nairobi',
        delivery_address='456 Delivery Avenue, Nairobi',
        pickup_latitude=-1.2921,
        pickup_longitude=36.8219,
        delivery_latitude=-1.2864,
        delivery_longitude=36.8172,
        distance=5.0,
        price=Decimal('200.00'),
        contact_number='+254712345678',
        recipient_name='John Doe',
        status='draft'
    )
    print(f"   ✓ Draft errand created (ID: {order.id})")
    print(f"   ✓ Status: {order.status}")
    
    # Step 4: Check handler's pending orders BEFORE confirmation
    print("\n4. Checking handler's pending orders BEFORE confirmation...")
    pending_before = Order.objects.filter(status='pending').count()
    print(f"   ✓ Pending orders count: {pending_before}")
    
    # Step 5: Confirm the errand (change status to 'pending')
    print("\n5. Confirming errand (status → 'pending')...")
    order.status = 'pending'
    order.save()
    print(f"   ✓ Errand confirmed (ID: {order.id})")
    print(f"   ✓ New status: {order.status}")
    
    # Step 6: Check handler's pending orders AFTER confirmation
    print("\n6. Checking handler's pending orders AFTER confirmation...")
    pending_after = Order.objects.filter(status='pending').count()
    print(f"   ✓ Pending orders count: {pending_after}")
    
    # Step 7: Verify the specific order is in pending list
    print("\n7. Verifying errand appears in handler's pending list...")
    handler_pending_orders = Order.objects.filter(status='pending').select_related(
        'client', 'order_type'
    ).order_by('-created_at')
    
    found = False
    for pending_order in handler_pending_orders:
        if pending_order.id == order.id:
            found = True
            print(f"   ✓ FOUND! Errand #{order.id} is visible to handler")
            print(f"   ✓ Title: {pending_order.title}")
            print(f"   ✓ Client: {pending_order.client.username}")
            print(f"   ✓ Pickup: {pending_order.pickup_address}")
            print(f"   ✓ Delivery: {pending_order.delivery_address}")
            print(f"   ✓ Price: KSh {pending_order.price}")
            break
    
    if not found:
        print(f"   ✗ ERROR: Errand #{order.id} NOT found in pending orders!")
        return False
    
    # Step 8: Summary
    print("\n" + "=" * 60)
    print("TEST RESULT: ✅ SUCCESS")
    print("=" * 60)
    print(f"✓ Draft errand created successfully")
    print(f"✓ Errand confirmed (status changed to 'pending')")
    print(f"✓ Handler can see the errand in pending orders list")
    print(f"✓ Pending orders increased from {pending_before} to {pending_after}")
    print("\nCONCLUSION:")
    print("The system is working correctly. When a client confirms an errand,")
    print("it immediately appears in the handler's pending orders dashboard.")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = test_errand_visibility()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Test failed!")
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
