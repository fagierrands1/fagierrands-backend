#!/usr/bin/env python
"""
Direct database query for Order 349 using psycopg2
"""
import psycopg2
from decimal import Decimal

DATABASE_URL = "postgresql://postgres.dxesmzogjpxswxhsomgf:OnFRtf0SmpHwgNaQ@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("QUERYING ORDER 349 FROM DATABASE")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            o.id, o.title, o.price, o.distance, o.price_finalized,
            o.order_type_id, o.status,
            ot.name, ot.base_price, ot.price_per_km, ot.min_price
        FROM orders_order o
        LEFT JOIN orders_ordertype ot ON o.order_type_id = ot.id
        WHERE o.id = 349
    """)
    
    result = cursor.fetchone()
    
    if result:
        (order_id, title, price, distance, price_finalized,
         order_type_id, status, ot_name, base_price, price_per_km, min_price) = result
        
        print(f"\n📋 ORDER #{order_id}")
        print(f"   Title: {title}")
        print(f"   Status: {status}")
        
        print(f"\n📦 ORDER TYPE:")
        print(f"   ID: {order_type_id}")
        print(f"   Name: {ot_name}")
        print(f"   Base Price: {base_price}")
        print(f"   Price/km: {price_per_km}")
        print(f"   Min Price: {min_price}")
        
        print(f"\n📍 DISTANCE & PRICING:")
        print(f"   Distance: {distance} km")
        print(f"   Price in DB: {price} KES")
        print(f"   Price Finalized: {price_finalized}")
        
        print(f"\n🛒 SHOPPING ITEMS:")
        cursor.execute("""
            SELECT name, quantity, price FROM orders_shoppingitem WHERE order_id = 349
        """)
        items = cursor.fetchall()
        if items:
            total_items = Decimal('0')
            for name, qty, item_price in items:
                item_total = qty * item_price
                total_items += item_total
                print(f"   - {name}: {qty} × {item_price} = {item_total}")
            print(f"   TOTAL: {total_items} KES")
        else:
            print("   No items")
        
        print("\n" + "=" * 80)
        print("ANALYSIS:")
        print("=" * 80)
        
        if price == 200 or price == Decimal('200.00'):
            print("⚠️  ORDER HAS 200 KES (BELOW 250 MINIMUM)")
            print("\nChecking order type configuration:")
            if base_price and base_price < 250:
                print(f"   ❌ Order type base_price is {base_price} (should be 250)")
            if min_price and min_price < 250:
                print(f"   ❌ Order type min_price is {min_price} (should be 250)")
        
        if distance and distance <= 5:
            print(f"\n✓ Distance is {distance}km (≤ 5km), should be 250 KES minimum")
            if price and price < 250:
                print(f"   ❌ But price is {price} (INVALID)")
        elif distance and distance > 5:
            expected_min = Decimal(str(base_price)) if base_price else Decimal('250')
            expected_additional = (Decimal(str(distance)) - 5) * (Decimal(str(price_per_km)) if price_per_km else Decimal('30'))
            expected = expected_min + expected_additional
            print(f"\n✓ Distance is {distance}km (> 5km)")
            print(f"   Expected price: {expected_min} + {expected_additional} = {expected} KES")
            if price:
                print(f"   Actual price: {price} KES")
                if price != expected:
                    print(f"   ❌ MISMATCH: {abs(price - expected)} KES difference")
        
        print("\n" + "=" * 80)
    else:
        print("❌ Order 349 not found")
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
