#!/usr/bin/env python
"""
Script to clean up duplicate users in the database before applying unique constraints.
This script will:
1. Find all duplicate email addresses
2. Keep the most recent user for each email
3. Delete older duplicate users
4. Report what was cleaned up
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from collections import Counter

User = get_user_model()

def find_duplicate_emails():
    """Find all email addresses that have multiple users"""
    print("🔍 Searching for duplicate email addresses...")
    
    # Get all users with their emails and creation dates
    users = User.objects.all().values('email', 'id', 'date_joined', 'username')
    
    # Count occurrences of each email
    email_counts = Counter(user['email'] for user in users if user['email'])
    
    # Find emails with more than one user
    duplicates = {email: count for email, count in email_counts.items() if count > 1}
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} email addresses with duplicates:")
        for email, count in duplicates.items():
            print(f"   📧 {email}: {count} users")
        return duplicates
    else:
        print("✅ No duplicate email addresses found!")
        return {}

def cleanup_duplicates(dry_run=True):
    """Clean up duplicate users, keeping only the most recent one for each email"""
    duplicates = find_duplicate_emails()
    
    if not duplicates:
        return
    
    print(f"\n{'🧪 DRY RUN MODE' if dry_run else '🔧 CLEANUP MODE'}")
    print("-" * 50)
    
    total_to_delete = 0
    cleanup_plan = []
    
    for email in duplicates.keys():
        # Get all users with this email, ordered by creation date (newest first)
        users_with_email = User.objects.filter(email=email).order_by('-date_joined')
        users_list = list(users_with_email)
        
        if len(users_list) <= 1:
            continue
            
        # Keep the most recent user
        keep_user = users_list[0]
        delete_users = users_list[1:]
        
        print(f"\n📧 Email: {email}")
        print(f"   ✅ KEEP: User ID {keep_user.id} ({keep_user.username}) - Created: {keep_user.date_joined}")
        
        for user in delete_users:
            print(f"   ❌ DELETE: User ID {user.id} ({user.username}) - Created: {user.date_joined}")
            total_to_delete += 1
            cleanup_plan.append(user.id)
    
    print(f"\n📊 Summary:")
    print(f"   Total users to delete: {total_to_delete}")
    print(f"   Emails to be deduplicated: {len(duplicates)}")
    
    if not dry_run and total_to_delete > 0:
        confirm = input(f"\n⚠️  Are you sure you want to delete {total_to_delete} users? (type 'yes' to confirm): ")
        
        if confirm.lower() == 'yes':
            print("\n🗑️  Deleting duplicate users...")
            with transaction.atomic():
                deleted_count = 0
                for user_id in cleanup_plan:
                    try:
                        user = User.objects.get(id=user_id)
                        username = user.username
                        user.delete()
                        deleted_count += 1
                        print(f"   ✅ Deleted user ID {user_id} ({username})")
                    except User.DoesNotExist:
                        print(f"   ⚠️  User ID {user_id} not found (already deleted?)")
                    except Exception as e:
                        print(f"   ❌ Error deleting user ID {user_id}: {e}")
                
                print(f"\n🎉 Successfully deleted {deleted_count} duplicate users!")
        else:
            print("❌ Cleanup cancelled.")
    
    elif dry_run:
        print(f"\n💡 To actually perform the cleanup, run:")
        print(f"   python cleanup_duplicate_users.py --execute")

def main():
    print("🧹 Duplicate User Cleanup Script")
    print("=" * 40)
    
    # Check if --execute flag is provided
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("Running in DRY RUN mode (no changes will be made)")
    else:
        print("⚠️  EXECUTE mode - changes will be permanent!")
    
    try:
        cleanup_duplicates(dry_run=dry_run)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()