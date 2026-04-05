from django.core.management.base import BaseCommand
from orders.models import OrderType, Order, ShoppingItem
from accounts.models import User
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test pricing calculations to ensure consistency'

    def handle(self, *args, **options):
        self.stdout.write('Testing pricing calculations...')
        
        # Get or create a test order type
        order_type, created = OrderType.objects.get_or_create(
            name='Test Delivery',
            defaults={
                'base_price': Decimal('200.00'),
                'price_per_km': Decimal('20.00'),
                'min_price': Decimal('200.00')
            }
        )
        
        # Get or create a test user
        try:
            user = User.objects.get(username='test_pricing_user')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='test_pricing_user',
                email='test_pricing@example.com',
                first_name='Test',
                last_name='User'
            )
        
        # Test Case 1: Pickup/Delivery order, distance <= 7km
        self.stdout.write('\n=== Test Case 1: Pickup/Delivery, 3km distance ===')
        order1 = Order.objects.create(
            client=user,
            order_type=order_type,
            title='Test Order 1',
            description='Test pickup/delivery order',
            distance=3.0
        )
        price1 = order1.calculate_price()
        self.stdout.write(f'Expected: 200.00, Actual: {price1}')
        
        # Test Case 2: Pickup/Delivery order, distance > 7km
        self.stdout.write('\n=== Test Case 2: Pickup/Delivery, 10km distance ===')
        order2 = Order.objects.create(
            client=user,
            order_type=order_type,
            title='Test Order 2',
            description='Test pickup/delivery order, long distance',
            distance=10.0
        )
        price2 = order2.calculate_price()
        expected2 = 200 + (3 * 20)  # 200 base + (10-7) * 20
        self.stdout.write(f'Expected: {expected2}.00, Actual: {price2}')
        
        # Test Case 3: Shopping order with items, distance > 7km
        self.stdout.write('\n=== Test Case 3: Shopping with items, 10km distance ===')
        shopping_type, _ = OrderType.objects.get_or_create(name='Shopping', defaults={'base_price': 200, 'price_per_km': 20})
        order3 = Order.objects.create(
            client=user,
            order_type=shopping_type,
            title='Test Order 3',
            description='Test shopping order with items',
            distance=10.0
        )
        ShoppingItem.objects.create(
            order=order3,
            name='Test Item 1',
            price=Decimal('100.00'),
            quantity=2
        )
        ShoppingItem.objects.create(
            order=order3,
            name='Test Item 2',
            price=Decimal('50.00'),
            quantity=1
        )
        price3 = order3.calculate_price()
        expected3 = 100*2 + 50*1 + 200 + (3 * 20)  # items (250) + service fee (260)
        self.stdout.write(f'Expected: {expected3}.00, Actual: {price3}')
        
        # Test Case 4: Banking order
        self.stdout.write('\n=== Test Case 4: Banking order ===')
        banking_type, created = OrderType.objects.get_or_create(
            name='Banking Service',
            defaults={
                'base_price': Decimal('200.00'),
                'price_per_km': Decimal('20.00'),
                'min_price': Decimal('200.00')
            }
        )
        order4 = Order.objects.create(
            client=user,
            order_type=banking_type,
            title='Test Order 4',
            description='Test banking order',
            distance=10.0
        )
        # Create a "shopping item" to simulate banking amount if needed, 
        # or it uses the items_price from shopping items in the model
        ShoppingItem.objects.create(
            order=order4,
            name='Banking Amount',
            price=Decimal('10000.00'),
            quantity=1
        )
        # 10,000 should have 50 fee. Distance 10km has 300 service fee.
        # Fee 50 is less than 300, so 50 should be returned.
        price4 = order4.calculate_price()
        self.stdout.write(f'Expected: 50.00, Actual: {price4}')
        
        # Clean up test data
        Order.objects.filter(title__startswith='Test Order').delete()
        
        self.stdout.write('\n=== Pricing test completed ===')