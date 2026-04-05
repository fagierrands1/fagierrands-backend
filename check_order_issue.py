import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order, OrderPrepayment, Payment, ShoppingItem
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print("=" * 80)
print("CHECKING ORDER ISSUE FOR johnnderitunduhiu@outlook.com")
print("=" * 80)

# Check if user exists
user = User.objects.filter(email='johnnderitunduhiu@outlook.com').first()
print(f"\n1. User Check:")
print(f"   User found: {user}")
if user:
    print(f"   User ID: {user.id}")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
else:
    print("   ❌ User not found in database!")
    print("\n   Checking for similar emails...")
    similar = User.objects.filter(email__icontains='johnn')
    for u in similar:
        print(f"   - {u.email}")

# Check recent prepayments
print(f"\n2. Recent Prepayments (last 7 days):")
recent = timezone.now() - timedelta(days=7)
prepays = OrderPrepayment.objects.filter(created_at__gte=recent).order_by('-created_at')[:20]
if prepays:
    for p in prepays:
        client_email = p.client.email if p.client else "No client"
        print(f"   ID: {p.id}")
        print(f"   Client: {client_email}")
        print(f"   Title: {p.title}")
        print(f"   Deposit: KSh {p.deposit_amount}")
        print(f"   Total: KSh {p.total_amount}")
        print(f"   Status: {p.status}")
        print(f"   Invoice ID: {p.intasend_invoice_id}")
        print(f"   Order Created: {p.order_id if p.order else 'No'}")
        print(f"   Created: {p.created_at}")
        print(f"   Items: {p.items}")
        print("   " + "-" * 70)
else:
    print("   No recent prepayments found")

# Check recent payments
print(f"\n3. Recent Payments (last 7 days):")
payments = Payment.objects.filter(payment_date__gte=recent).order_by('-payment_date')[:20]
if payments:
    for pay in payments:
        client_email = pay.client.email if pay.client else "No client"
        print(f"   ID: {pay.id}")
        print(f"   Client: {client_email}")
        print(f"   Amount: KSh {pay.amount}")
        print(f"   Status: {pay.status}")
        print(f"   Invoice ID: {pay.intasend_invoice_id}")
        print(f"   Order ID: {pay.order_id if pay.order else 'No order'}")
        print(f"   Date: {pay.payment_date}")
        print("   " + "-" * 70)
else:
    print("   No recent payments found")

# Check recent orders
print(f"\n4. Recent Orders (last 7 days):")
orders = Order.objects.filter(created_at__gte=recent).order_by('-created_at')[:20]
if orders:
    for o in orders:
        client_email = o.client.email if o.client else "No client"
        print(f"   ID: {o.id}")
        print(f"   Client: {client_email}")
        print(f"   Title: {o.title}")
        print(f"   Type: {o.order_type.name if o.order_type else 'No type'}")
        print(f"   Price: KSh {o.price}")
        print(f"   Status: {o.status}")
        print(f"   Created: {o.created_at}")
        items = ShoppingItem.objects.filter(order=o)
        if items:
            print(f"   Items:")
            for item in items:
                print(f"     - {item.name}: {item.quantity} x KSh {item.price}")
        print("   " + "-" * 70)
else:
    print("   No recent orders found")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)