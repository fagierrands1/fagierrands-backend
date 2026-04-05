import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from orders.models import OrderType
from decimal import Decimal

# Get or create an OrderType for testing
ot, created = OrderType.objects.get_or_create(
    name='Test Order Type',
    defaults={
        'description': 'Test order type for pricing',
        'base_price': Decimal('200.00'),
        'price_per_km': Decimal('20.00'),
        'min_price': Decimal('200.00')
    }
)

# Test cases for the new pricing logic
test_cases = [
    (None, Decimal('200.00')),  # No distance - should return base price
    (0, Decimal('200.00')),     # 0 km - should return base price
    (3, Decimal('200.00')),     # 3 km <= 7km - should return base price
    (5, Decimal('200.00')),     # 5 km <= 7km - should return base price
    (7, Decimal('200.00')),     # 7 km - should return base price
    (10, Decimal('260.00')),    # 10 km: 200 + 20*(10-7) = 260
    (15, Decimal('360.00')),    # 15 km: 200 + 20*(15-7) = 360
]

print("Testing OrderType.calculate_price method with new pricing logic:")
print("=" * 60)
all_passed = True
for distance, expected in test_cases:
    result = ot.calculate_price(distance)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"Distance: {distance} km -> Expected: {expected}, Got: {result} [{status}]")

print("=" * 60)
if all_passed:
    print("All tests PASSED! The pricing logic is working correctly.")
else:
    print("Some tests FAILED! Please review the implementation.")
