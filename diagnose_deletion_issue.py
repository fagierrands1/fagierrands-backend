import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

print("=== Checking for orphaned tables ===\n")

# Get all tables in database
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename;
    """)
    all_tables = [row[0] for row in cursor.fetchall()]

print(f"Total tables in database: {len(all_tables)}\n")

# Check for reportissue tables
reportissue_tables = [t for t in all_tables if 'reportissue' in t.lower()]
if reportissue_tables:
    print("⚠️  Found reportissue tables:")
    for table in reportissue_tables:
        print(f"  - {table}")
    print()

# Check for evidence tables
evidence_tables = [t for t in all_tables if 'evidence' in t.lower()]
if evidence_tables:
    print("⚠️  Found evidence tables:")
    for table in evidence_tables:
        print(f"  - {table}")
    print()

# Try to delete a test user
print("=== Testing user deletion ===\n")
test_user = User.objects.filter(username__startswith='test').first()
if test_user:
    print(f"Found test user: {test_user.id} - {test_user.username}")
    try:
        test_user.delete()
        print("✅ User deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No test user found to delete")

# Check for foreign key constraints on accounts_user
print("\n=== Foreign key constraints on accounts_user ===\n")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT 
            tc.table_name, 
            tc.constraint_name,
            kcu.column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND ccu.table_name = 'accounts_user'
        ORDER BY tc.table_name;
    """)
    constraints = cursor.fetchall()
    
    if constraints:
        for table, constraint, column in constraints:
            print(f"  {table}.{column} -> {constraint}")
    else:
        print("  No foreign key constraints found")
