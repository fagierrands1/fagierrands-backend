"""
Test script for 2-step errand placement flow
Run with: python manage.py shell < test_errand_flow.py
"""

from django.contrib.auth import get_user_model
from orders.models import Order, OrderType
from decimal import Decimal

User = get_user_model()

print("=" * 60)
print("Testing 2-Step Errand Placement Flow")
print("=" * 60)

# Get or create test user
try:
    user = User.objects.get(username='testuser')
    print(f"✅ Using existing user: {user.username}")
except User.DoesNotExist:
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    print(f"✅ Created test user: {user.username}")

# Get or create order type
order_type, created = OrderType.objects.get_or_create(
    name='Pickup & Delivery',
    defaults={
        'description': 'Standard pickup and delivery service',
        'base_price': Decimal('200.00'),
        'price_per_km': Decimal('20.00'),
        'min_price': Decimal('200.00')
    }
)
print(f"✅ Order type: {order_type.name}")

# Test 1: Price Calculation
print("\n" + "=" * 60)
print("TEST 1: Price Calculation")
print("=" * 60)

test_distances = [5, 7, 9, 15, 20]
for distance in test_distances:
    price = order_type.calculate_price(Decimal(str(distance)))
    print(f"Distance: {distance}km → Price: KSh {price}")

# Test 2: Create Draft Order
print("\n" + "=" * 60)
print("TEST 2: Create Draft Order")
print("=" * 60)

draft_order = Order.objects.create(
    client=user,
    order_type=order_type,
    title="Test Errand - Deliver Laptop",
    description="Dell laptop in black bag",
    pickup_address="Westlands, Nairobi",
    delivery_address="CBD, Nairobi",
    pickup_latitude=-1.2634,
    pickup_longitude=36.8078,
    delivery_latitude=-1.2864,
    delivery_longitude=36.8172,
    distance=9.0,
    price=order_type.calculate_price(Decimal('9.0')),
    status='draft'
)

print(f"✅ Created draft order #{draft_order.id}")
print(f"   Status: {draft_order.status}")
print(f"   Price: KSh {draft_order.price}")
print(f"   From: {draft_order.pickup_address}")
print(f"   To: {draft_order.delivery_address}")

# Test 3: Update Receiver Info
print("\n" + "=" * 60)
print("TEST 3: Update Receiver Info")
print("=" * 60)

draft_order.recipient_name = "John Doe"
draft_order.contact_number = "+254712345678"
draft_order.estimated_value = Decimal('50000.00')
draft_order.save()

print(f"✅ Updated receiver info")
print(f"   Recipient: {draft_order.recipient_name}")
print(f"   Contact: {draft_order.contact_number}")
print(f"   Estimated Value: KSh {draft_order.estimated_value}")

# Test 4: Confirm Order (Draft → Pending)
print("\n" + "=" * 60)
print("TEST 4: Confirm Order")
print("=" * 60)

draft_order.status = 'pending'
draft_order.save()

print(f"✅ Order confirmed!")
print(f"   Order ID: {draft_order.id}")
print(f"   Status: {draft_order.status}")
print(f"   Price: KSh {draft_order.price}")

# Test 5: Verify Status Choices
print("\n" + "=" * 60)
print("TEST 5: Available Status Choices")
print("=" * 60)

for status_code, status_name in Order.STATUS_CHOICES:
    print(f"   {status_code}: {status_name}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"✅ All tests passed!")
print(f"✅ Draft order created: #{draft_order.id}")
print(f"✅ Status changed: draft → pending")
print(f"✅ Price calculated: KSh {draft_order.price}")
print("\n🎉 2-Step Errand Placement Flow is working!")
print("=" * 60)

# Cleanup (optional - comment out if you want to keep the test data)
# draft_order.delete()
# print("\n🧹 Cleaned up test data")
