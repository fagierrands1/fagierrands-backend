#!/usr/bin/env python
"""
Script to identify and provide options to fix duplicate email addresses
"""
import os
import sys
import django
from django.conf import settings

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

User = get_user_model()

def find_duplicate_emails():
    """Find all duplicate email addresses"""
    print("=" * 60)
    print("DUPLICATE EMAIL ANALYSIS")
    print("=" * 60)
    
    # Find all email addresses that appear more than once
    duplicates = User.objects.values('email').annotate(count=Count('email')).filter(count__gt=1)
    
    if not duplicates:
        print("✅ No duplicate email addresses found!")
        return []
    
    print(f"Found {len(duplicates)} email addresses with duplicates:")
    print()
    
    duplicate_details = []
    
    for dup in duplicates:
        email = dup['email']
        count = dup['count']
        print(f"📧 Email: {email} ({count} users)")
        
        # Get all users with this email
        users = User.objects.filter(email=email).order_by('-date_joined')
        user_details = []
        
        for i, user in enumerate(users):
            print(f"   {i+1}. User ID: {user.id}")
            print(f"      Username: {user.username}")
            print(f"      User Type: {user.user_type}")
            print(f"      Active: {user.is_active}")
            print(f"      Last Login: {user.last_login or 'Never'}")
            print(f"      Date Joined: {user.date_joined}")
            print(f"      Email Verified: {user.email_verified}")
            
            # Check if user has any related data
            order_count = 0  # You'd need to import Order model to check this
            try:
                from orders.models import Order
                order_count = Order.objects.filter(user=user).count()
            except:
                pass
            
            print(f"      Orders: {order_count}")
            print()
            
            user_details.append({
                'user': user,
                'order_count': order_count,
                'last_login': user.last_login,
                'date_joined': user.date_joined
            })
        
        duplicate_details.append({
            'email': email,
            'users': user_details
        })
        print("-" * 40)
    
    return duplicate_details

def recommend_cleanup(duplicate_details):
    """Recommend which users to keep/remove"""
    print("\n" + "=" * 60)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 60)
    
    for dup in duplicate_details:
        email = dup['email']
        users = dup['users']
        
        print(f"\n📧 Email: {email}")
        
        # Sort users by priority (most recent login, most orders, most recent registration)
        def user_priority(user_info):
            user = user_info['user']
            score = 0
            
            # Recent login gets points
            if user.last_login:
                days_since_login = (timezone.now() - user.last_login).days
                score += max(0, 100 - days_since_login)
            
            # Orders get points
            score += user_info['order_count'] * 10
            
            # Recent registration gets points
            days_since_joined = (timezone.now() - user.date_joined).days
            score += max(0, 50 - days_since_joined)
            
            # Active users get points
            if user.is_active:
                score += 20
            
            # Email verified gets points
            if user.email_verified:
                score += 30
            
            return score
        
        sorted_users = sorted(users, key=user_priority, reverse=True)
        
        print("🎯 RECOMMENDED ACTION:")
        keep_user = sorted_users[0]['user']
        print(f"   ✅ KEEP: User ID {keep_user.id} ({keep_user.username})")
        print(f"      Reason: Best combination of activity, orders, and recency")
        
        if len(sorted_users) > 1:
            print("   🗑️  CONSIDER REMOVING:")
            for user_info in sorted_users[1:]:
                user = user_info['user']
                print(f"      - User ID {user.id} ({user.username})")
                if user_info['order_count'] > 0:
                    print(f"        ⚠️  WARNING: This user has {user_info['order_count']} orders!")
                if user.last_login:
                    print(f"        Last active: {user.last_login}")
                else:
                    print(f"        Never logged in")
        
        print()

def generate_cleanup_script(duplicate_details):
    """Generate a Django management command to clean up duplicates"""
    print("\n" + "=" * 60)
    print("CLEANUP SCRIPT GENERATION")
    print("=" * 60)
    
    script_content = '''#!/usr/bin/env python
"""
Auto-generated script to clean up duplicate email addresses
PLEASE REVIEW CAREFULLY BEFORE RUNNING!
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def cleanup_duplicates():
    """Clean up duplicate email addresses"""
    print("Starting duplicate email cleanup...")
    
'''
    
    for dup in duplicate_details:
        email = dup['email']
        users = dup['users']
        
        if len(users) <= 1:
            continue
        
        # Sort by priority and recommend keeping the first one
        def user_priority(user_info):
            user = user_info['user']
            score = 0
            if user.last_login:
                days_since_login = (timezone.now() - user.last_login).days
                score += max(0, 100 - days_since_login)
            score += user_info['order_count'] * 10
            days_since_joined = (timezone.now() - user.date_joined).days
            score += max(0, 50 - days_since_joined)
            if user.is_active:
                score += 20
            if user.email_verified:
                score += 30
            return score
        
        sorted_users = sorted(users, key=user_priority, reverse=True)
        keep_user = sorted_users[0]['user']
        remove_users = [u['user'] for u in sorted_users[1:]]
        
        script_content += f'''
    # Cleanup for email: {email}
    print("Processing email: {email}")
    
    # Keep user: {keep_user.username} (ID: {keep_user.id})
    # Remove users: {[u.username for u in remove_users]}
    
    users_to_remove = User.objects.filter(id__in={[u.id for u in remove_users]})
    for user in users_to_remove:
        print(f"  Removing user: {{user.username}} (ID: {{user.id}})")
        # UNCOMMENT THE NEXT LINE TO ACTUALLY DELETE:
        # user.delete()
    
'''
    
    script_content += '''
    print("Cleanup completed!")
    print("Note: Users were not actually deleted - uncomment delete lines to execute")

if __name__ == '__main__':
    cleanup_duplicates()
'''
    
    with open('cleanup_duplicate_emails.py', 'w') as f:
        f.write(script_content)
    
    print("✅ Generated cleanup script: cleanup_duplicate_emails.py")
    print("⚠️  IMPORTANT: Review the script carefully before running!")
    print("   The script is generated with delete lines commented out for safety.")

if __name__ == '__main__':
    duplicate_details = find_duplicate_emails()
    
    if duplicate_details:
        recommend_cleanup(duplicate_details)
        
        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("1. ✅ The login endpoint has been fixed to handle duplicates")
        print("2. 🔍 Review the recommendations above")
        print("3. 🧹 Consider cleaning up duplicate accounts to prevent future issues")
        print("4. 📧 Optionally, add email uniqueness constraint to prevent future duplicates")
        print()
        print("The system will continue to work with the current fix, but cleanup is recommended.")
    else:
        print("\n✨ No action needed - no duplicates found!")