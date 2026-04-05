#!/usr/bin/env python
"""
Standalone debug script for Order 349
Run with: python debug_order_349_standalone.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Order, OrderType
from decimal import Decimal

try:
    order = Order.objects.get(id=349)
    
    print("=" * 80)
    print(f"ORDER #{order.id} - {order.title}")
    print("=" * 80)
    
    print(f"\n📋 ORDER TYPE:")
    print(f"   Name: {order.order_type.name}")
    print(f"   Base Price: {order.order_type.base_price}")
    print(f"   Price per km: {order.order_type.price_per_km}")
    print(f"   Min Price: {order.order_type.min_price}")
    
    print(f"\n📍 LOCATION & DISTANCE:")
    print(f"   Pickup: ({order.pickup_latitude}, {order.pickup_longitude}) - {order.pickup_address}")
    print(f"   Delivery: ({order.delivery_latitude}, {order.delivery_longitude}) - {order.delivery_address}")
    print(f"   Distance: {order.distance} km")
    
    print(f"\n💰 PRICING:")
    print(f"   Current Price in DB: {order.price} KES")
    print(f"   Price Finalized: {order.price_finalized}")
    
    print(f"\n🛒 ITEMS:")
    items = order.shopping_items.all()
    if items.exists():
        total_items = Decimal('0')
        for item in items:
            item_total = item.price * item.quantity
            total_items += item_total
            print(f"   - {item.name}: {item.quantity} × {item.price} = {item_total}")
        print(f"   TOTAL ITEMS: {total_items} KES")
    else:
        print(f"   No items")
    
    print(f"\n🔢 RECALCULATE PRICE:")
    recalc_price = order.calculate_price()
    print(f"   Calculated Price: {recalc_price} KES")
    if order.price:
        print(f"   Difference from DB: {order.price - recalc_price} KES")
    
    print(f"\n🎯 OrderType.calculate_price() METHOD:")
    if order.distance:
        distance_price = order.order_type.calculate_price(Decimal(str(order.distance)))
        print(f"   For {order.distance} km: {distance_price} KES")
    else:
        print(f"   No distance - would use base price")
    
    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("=" * 80)
    
    if order.price == Decimal('200.00') or order.price == 200:
        print("⚠️  Order has 200 KES price (BELOW MINIMUM 250)")
        print("\nPossible causes:")
        print("1. Order type misconfigured (base_price or min_price is 200)")
        print("2. Old buggy code didn't enforce minimum in this order type")
        print("3. Service fee (200) was confused with total price")
    
    if order.price and recalc_price and order.price != recalc_price:
        print(f"\n⚠️  DB price ({order.price}) != calculated price ({recalc_price})")
        print("   This means calculate_price() logic has changed or order has stale data")
    
    if order.distance and order.distance <= 5:
        expected = Decimal('250')
        if order.price and order.price < expected:
            print(f"\n❌ ERROR: Distance {order.distance}km should cost >= 250, but got {order.price}")
    
    print("\n" + "=" * 80)
    
except Order.DoesNotExist:
    print("❌ Order 349 not found in database")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
