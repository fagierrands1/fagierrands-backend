"""
Test script to verify Supabase storage configuration
Run this from the fagierrandsbackup directory:
python test_supabase_upload.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.supabase_client import (
    get_admin_supabase_client, 
    get_supabase_client,
    VERIFICATION_BUCKET,
    is_supabase_available
)

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)
    
    # Check if Supabase is available
    if not is_supabase_available():
        print("❌ Supabase client is not available!")
        print("   Check your .env file for SUPABASE_URL and SUPABASE_KEY")
        return False
    
    print("✅ Supabase client is available")
    
    # Get regular client
    client = get_supabase_client()
    if client:
        print("✅ Regular Supabase client initialized")
    else:
        print("❌ Failed to get regular Supabase client")
        return False
    
    # Get admin client
    admin_client = get_admin_supabase_client()
    if admin_client:
        print("✅ Admin Supabase client initialized")
    else:
        print("❌ Failed to get admin Supabase client")
        print("   Check your .env file for SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    return True

def test_storage_bucket():
    """Test storage bucket access"""
    print("\n" + "=" * 60)
    print("STORAGE BUCKET TEST")
    print("=" * 60)
    
    admin_client = get_admin_supabase_client()
    if not admin_client:
        print("❌ Admin client not available")
        return False
    
    print(f"📦 Target bucket: {VERIFICATION_BUCKET}")
    
    try:
        # List all buckets
        print("\n🔍 Listing all storage buckets...")
        buckets = admin_client.storage.list_buckets()
        
        if not buckets:
            print("❌ No buckets found!")
            print("   You need to create the 'user-uploads' bucket in Supabase")
            print("   Run the SQL script: supabase_user_uploads_policies.sql")
            return False
        
        print(f"✅ Found {len(buckets)} bucket(s):")
        bucket_names = []
        
        for bucket in buckets:
            # Handle both dict and object formats
            if hasattr(bucket, 'id'):
                bucket_id = bucket.id
                is_public = getattr(bucket, 'public', False)
            elif hasattr(bucket, 'name'):
                bucket_id = bucket.name
                is_public = getattr(bucket, 'public', False)
            elif isinstance(bucket, dict):
                bucket_id = bucket.get('id') or bucket.get('name')
                is_public = bucket.get('public', False)
            else:
                # Try to convert to dict
                try:
                    bucket_dict = bucket.__dict__
                    bucket_id = bucket_dict.get('id') or bucket_dict.get('name')
                    is_public = bucket_dict.get('public', False)
                except:
                    bucket_id = str(bucket)
                    is_public = False
            
            print(f"   - {bucket_id} (public: {is_public})")
            bucket_names.append(bucket_id)
        
        # Check if our target bucket exists
        if VERIFICATION_BUCKET in bucket_names:
            print(f"\n✅ Target bucket '{VERIFICATION_BUCKET}' exists!")
            return True
        else:
            print(f"\n❌ Target bucket '{VERIFICATION_BUCKET}' NOT FOUND!")
            print(f"   Available buckets: {', '.join(bucket_names)}")
            print("   You need to create it using the SQL script:")
            print("   supabase_user_uploads_policies.sql")
            return False
            
    except Exception as e:
        import traceback
        print(f"❌ Error accessing storage: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_upload_permission():
    """Test if we can upload to the bucket"""
    print("\n" + "=" * 60)
    print("UPLOAD PERMISSION TEST")
    print("=" * 60)
    
    admin_client = get_admin_supabase_client()
    if not admin_client:
        print("❌ Admin client not available")
        return False
    
    try:
        # Try to upload a small test file
        test_content = b"Test file content"
        test_path = "test/test_file.txt"
        
        print(f"📤 Attempting test upload to: {test_path}")
        
        result = admin_client.storage.from_(VERIFICATION_BUCKET).upload(
            test_path,
            test_content,
            file_options={
                'content-type': 'text/plain',
                'x-upsert': 'true'
            }
        )
        
        print("✅ Test upload successful!")
        print(f"   Result: {result}")
        
        # Try to delete the test file
        print("\n🗑️  Cleaning up test file...")
        admin_client.storage.from_(VERIFICATION_BUCKET).remove([test_path])
        print("✅ Test file deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        print("\n   Possible causes:")
        print("   1. Bucket doesn't exist - run the SQL script")
        print("   2. RLS policies not set up - run the SQL script")
        print("   3. Service role key is incorrect - check .env file")
        return False

def main():
    """Run all tests"""
    print("\n🚀 Starting Supabase Storage Tests...\n")
    
    # Test 1: Connection
    connection_ok = test_supabase_connection()
    
    if not connection_ok:
        print("\n❌ Connection test failed. Fix connection issues first.")
        return
    
    # Test 2: Bucket
    bucket_ok = test_storage_bucket()
    
    if not bucket_ok:
        print("\n❌ Bucket test failed. Create the bucket using SQL script.")
        return
    
    # Test 3: Upload
    upload_ok = test_upload_permission()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Bucket:     {'✅ PASS' if bucket_ok else '❌ FAIL'}")
    print(f"Upload:     {'✅ PASS' if upload_ok else '❌ FAIL'}")
    
    if connection_ok and bucket_ok and upload_ok:
        print("\n🎉 All tests passed! Your Supabase storage is ready.")
        print("   You can now upload images from the mobile app.")
    else:
        print("\n⚠️  Some tests failed. Follow the instructions above to fix.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()