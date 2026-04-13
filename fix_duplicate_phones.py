import os
import django
import re
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def normalize_phone_number(phone):
    """Normalize phone number to +254XXXXXXXXX format"""
    if not phone:
        return None
    
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if phone.startswith('254'):
        return f'+{phone}'
    elif phone.startswith('0'):
        return f'+254{phone[1:]}'
    elif phone.startswith('7') or phone.startswith('1'):
        return f'+254{phone}'
    
    return f'+{phone}'

# Get all users with phone numbers
users = User.objects.exclude(phone_number__isnull=True).exclude(phone_number='').order_by('date_joined')

print(f"Found {users.count()} users with phone numbers")

# Group by normalized phone
phone_groups = {}

for user in users:
    normalized = normalize_phone_number(user.phone_number)
    if normalized not in phone_groups:
        phone_groups[normalized] = []
    phone_groups[normalized].append(user)

# Find duplicates
duplicates_to_fix = []
for phone, user_list in phone_groups.items():
    if len(user_list) > 1:
        # Keep the oldest (first in list since we ordered by date_joined)
        keep = user_list[0]
        remove = user_list[1:]
        duplicates_to_fix.append({
            'phone': phone,
            'keep': keep,
            'remove': remove
        })

if not duplicates_to_fix:
    print("No duplicates found!")
    sys.exit(0)

print(f"\n=== DUPLICATES TO FIX ===")
for dup in duplicates_to_fix:
    print(f"\nPhone: {dup['phone']}")
    print(f"  KEEP: User {dup['keep'].id} ({dup['keep'].username}) - joined {dup['keep'].date_joined}")
    for user in dup['remove']:
        print(f"  DELETE: User {user.id} ({user.username}) - joined {user.date_joined}")

confirm = input("\nDo you want to delete the newer duplicate accounts? (yes/no): ")

if confirm.lower() != 'yes':
    print("Aborted.")
    sys.exit(0)

# Fix duplicates
with transaction.atomic():
    for dup in duplicates_to_fix:
        keep_user = dup['keep']
        # Normalize the phone for the user we're keeping
        keep_user.phone_number = dup['phone']
        keep_user.save(update_fields=['phone_number'])
        
        for user in dup['remove']:
            print(f"Deleting User {user.id} ({user.username})...")
            user.delete()

print("\n✅ Duplicates resolved!")
print("Now you can run: python manage.py migrate accounts")
