import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model

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
users = User.objects.exclude(phone_number__isnull=True).exclude(phone_number='')

print(f"Found {users.count()} users with phone numbers")

# Track normalized phones and duplicates
phone_map = {}
duplicates = []

for user in users:
    original = user.phone_number
    normalized = normalize_phone_number(original)
    
    if normalized in phone_map:
        duplicates.append({
            'phone': normalized,
            'original': original,
            'user_id': user.id,
            'username': user.username,
            'date_joined': user.date_joined,
            'existing_user_id': phone_map[normalized]['user_id']
        })
        print(f"DUPLICATE: {original} -> {normalized} (User {user.id}, existing: {phone_map[normalized]['user_id']})")
    else:
        phone_map[normalized] = {
            'user_id': user.id,
            'original': original,
            'username': user.username
        }
        
        # Update to normalized format if different
        if original != normalized:
            print(f"Normalizing: {original} -> {normalized} (User {user.id})")
            user.phone_number = normalized
            user.save(update_fields=['phone_number'])

print(f"\n=== SUMMARY ===")
print(f"Total users: {users.count()}")
print(f"Normalized: {len([p for p in phone_map.values() if p['original'] != normalize_phone_number(p['original'])])}")
print(f"Duplicates found: {len(duplicates)}")

if duplicates:
    print(f"\n=== DUPLICATES TO RESOLVE ===")
    for dup in duplicates:
        print(f"Phone: {dup['phone']}")
        print(f"  - User {dup['user_id']} ({dup['username']}) joined {dup['date_joined']}")
        print(f"  - Conflicts with User {dup['existing_user_id']}")
        print()
    
    print("\nTo resolve duplicates, you need to:")
    print("1. Keep the oldest account (earliest date_joined)")
    print("2. Delete or merge the duplicate accounts")
    print("\nRun this script with --fix flag to auto-delete newer duplicates")
