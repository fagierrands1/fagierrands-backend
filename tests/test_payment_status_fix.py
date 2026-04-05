#!/usr/bin/env python
"""
Test script to verify that order status is correctly updated based on payment status.
This tests the fix for the issue where order status was changing to completed even when payment was cancelled.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json
import uuid

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import Order, OrderType, Payment
from accounts.models import User

def test_payment_callback_scenarios():
    """Test different payment callback scenarios"""
    print("Testing payment callback scenarios...")
    
    # Create test user (or get existing one)
    try:
        user = User.objects.create_user(
            username='testuser_payment',
            email='test_payment@example.com',
            password='testpass123'
        )
        created_user = True
    except:
        user = User.objects.get(email='test_payment@example.com')
        created_user = False
    
    # Create test order type
    order_type, _ = OrderType.objects.get_or_create(
        name='Pickup & Delivery',
        defaults={'base_price': Decimal('580.00')}
    )
    
    # Create test order
    order = Order.objects.create(
        client=user,
        order_type=order_type,
        title='Test Order',
        description='Test order for payment status testing',
        status='in_progress',
        price=Decimal('580.00')
    )
    
    # Create test payment with unique references
    unique_id = str(uuid.uuid4())[:8]
    payment = Payment.objects.create(
        order=order,
        client=user,
        amount=Decimal('580.00'),
        payment_method='mpesa',
        status='pending',
        transaction_reference=f'TEST-REF-{unique_id}',
        intasend_invoice_id=f'test-invoice-{unique_id}'
    )
    
    print(f"Created test order with ID: {order.id}, initial status: {order.status}")
    print(f"Created test payment with ID: {payment.id}, initial status: {payment.status}")
    
    # Test 1: Payment completed webhook
    print("\n--- Test 1: Payment Completed Webhook ---")
    client = Client()
    
    webhook_data = {
        'event': 'payment.completed',
        'data': {
            'invoice': {'id': f'test-invoice-{unique_id}'},
            'mpesa_receipt': 'TEST-RECEIPT-123'
        }
    }
    
    response = client.post(
        '/api/orders/payments/webhook/',
        data=json.dumps(webhook_data),
        content_type='application/json'
    )
    
    # Refresh objects from database
    order.refresh_from_db()
    payment.refresh_from_db()
    
    print(f"Webhook response status: {response.status_code}")
    print(f"Payment status after completion webhook: {payment.status}")
    print(f"Order status after completion webhook: {order.status}")
    print(f"Order completed_at: {order.completed_at}")
    
    # Verify the fix worked
    assert payment.status == 'completed', f"Expected payment status 'completed', got '{payment.status}'"
    assert order.status == 'completed', f"Expected order status 'completed', got '{order.status}'"
    assert order.completed_at is not None, "Expected order.completed_at to be set"
    
    print("✅ Test 1 PASSED: Order status correctly updated to completed when payment completed")
    
    # Test 2: Payment cancelled webhook
    print("\n--- Test 2: Payment Cancelled Webhook ---")
    
    # Reset order and payment for next test
    order.status = 'in_progress'
    order.completed_at = None
    order.save()
    
    payment.status = 'pending'
    payment.save()
    
    webhook_data = {
        'event': 'payment.cancelled',
        'data': {
            'invoice': {'id': f'test-invoice-{unique_id}'}
        }
    }
    
    response = client.post(
        '/api/orders/payments/webhook/',
        data=json.dumps(webhook_data),
        content_type='application/json'
    )
    
    # Refresh objects from database
    order.refresh_from_db()
    payment.refresh_from_db()
    
    print(f"Webhook response status: {response.status_code}")
    print(f"Payment status after cancellation webhook: {payment.status}")
    print(f"Order status after cancellation webhook: {order.status}")
    print(f"Order completed_at: {order.completed_at}")
    
    # Verify the fix worked - order should NOT be completed when payment is cancelled
    assert payment.status == 'cancelled', f"Expected payment status 'cancelled', got '{payment.status}'"
    assert order.status == 'in_progress', f"Expected order status to remain 'in_progress', got '{order.status}'"
    assert order.completed_at is None, "Expected order.completed_at to remain None when payment cancelled"
    
    print("✅ Test 2 PASSED: Order status correctly remained unchanged when payment cancelled")
    
    # Test 3: Payment failed webhook
    print("\n--- Test 3: Payment Failed Webhook ---")
    
    # Reset payment for next test
    payment.status = 'pending'
    payment.save()
    
    webhook_data = {
        'event': 'payment.failed',
        'data': {
            'invoice': {'id': f'test-invoice-{unique_id}'}
        }
    }
    
    response = client.post(
        '/api/orders/payments/webhook/',
        data=json.dumps(webhook_data),
        content_type='application/json'
    )
    
    # Refresh objects from database
    order.refresh_from_db()
    payment.refresh_from_db()
    
    print(f"Webhook response status: {response.status_code}")
    print(f"Payment status after failed webhook: {payment.status}")
    print(f"Order status after failed webhook: {order.status}")
    print(f"Order completed_at: {order.completed_at}")
    
    # Verify the fix worked - order should NOT be completed when payment fails
    assert payment.status == 'failed', f"Expected payment status 'failed', got '{payment.status}'"
    assert order.status == 'in_progress', f"Expected order status to remain 'in_progress', got '{order.status}'"
    assert order.completed_at is None, "Expected order.completed_at to remain None when payment failed"
    
    print("✅ Test 3 PASSED: Order status correctly remained unchanged when payment failed")
    
    # Cleanup
    order.delete()
    if created_user:
        user.delete()
    
    print("\n🎉 All tests passed! The payment status fix is working correctly.")
    print("Summary:")
    print("- ✅ Order status updates to 'completed' when payment is completed")
    print("- ✅ Order status remains unchanged when payment is cancelled")
    print("- ✅ Order status remains unchanged when payment fails")

if __name__ == '__main__':
    try:
        test_payment_callback_scenarios()
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)