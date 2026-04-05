#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.supabase_client import get_supabase_client, VERIFICATION_BUCKET

def create_bucket():
    print("=== Creating Supabase Bucket ===")
    
    client = get_supabase_client()
    if not client:
        print("❌ Supabase client not available")
        return False
    
    try:
        # Check if bucket already exists
        try:
            bucket_info = client.storage.get_bucket(VERIFICATION_BUCKET)
            print(f"✅ Bucket '{VERIFICATION_BUCKET}' already exists")
            print(f"Bucket info: {bucket_info}")
            return True
        except Exception as e:
            print(f"Bucket doesn't exist: {e}")
        
        # Try to create the bucket
        print(f"Creating bucket '{VERIFICATION_BUCKET}'...")
        
        # Create bucket with public access
        result = client.storage.create_bucket(
            VERIFICATION_BUCKET,
            options={
                "public": True,
                "allowedMimeTypes": ["image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"],
                "fileSizeLimit": 10485760  # 10MB
            }
        )
        
        print(f"Bucket creation result: {result}")
        
        if result:
            print(f"✅ Successfully created bucket '{VERIFICATION_BUCKET}'")
            return True
        else:
            print(f"❌ Failed to create bucket '{VERIFICATION_BUCKET}'")
            return False
            
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        
        # Try alternative approach - create with minimal options
        try:
            print("Trying alternative bucket creation...")
            result = client.storage.create_bucket(VERIFICATION_BUCKET)
            print(f"Alternative creation result: {result}")
            
            if result:
                print(f"✅ Successfully created bucket '{VERIFICATION_BUCKET}' with minimal options")
                return True
                
        except Exception as alt_error:
            print(f"❌ Alternative creation also failed: {alt_error}")
        
        return False

def test_bucket_upload():
    print("\n=== Testing Bucket Upload ===")
    
    client = get_supabase_client()
    if not client:
        print("❌ Supabase client not available")
        return False
    
    try:
        # Test upload with a simple text file
        test_content = b"This is a test file for bucket verification"
        test_filename = "test_upload.txt"
        
        result = client.storage.from_(VERIFICATION_BUCKET).upload(
            test_filename,
            test_content,
            file_options={"content-type": "text/plain"}
        )
        
        print(f"Test upload result: {result}")
        
        if result:
            # Get public URL
            public_url = client.storage.from_(VERIFICATION_BUCKET).get_public_url(test_filename)
            print(f"✅ Test upload successful! URL: {public_url}")
            
            # Clean up test file
            try:
                client.storage.from_(VERIFICATION_BUCKET).remove([test_filename])
                print("🧹 Test file cleaned up")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup warning: {cleanup_error}")
            
            return True
        else:
            print("❌ Test upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Test upload error: {e}")
        return False

if __name__ == "__main__":
    bucket_created = create_bucket()
    if bucket_created:
        test_bucket_upload()
    else:
        print("\n❌ Cannot test upload without bucket")