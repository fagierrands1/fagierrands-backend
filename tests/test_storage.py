#!/usr/bin/env python
"""
Test script to verify storage configuration
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from accounts.supabase_client import is_supabase_available, get_supabase_client, VERIFICATION_BUCKET, ensure_bucket_exists

def test_local_storage():
    """Test local storage functionality"""
    print("=== Testing Local Storage ===")
    
    try:
        # Test file content
        test_content = b"This is a test file"
        test_filename = "test_upload.txt"
        
        # Try to save file
        file_path = default_storage.save(f'verification/{test_filename}', ContentFile(test_content))
        print(f"✓ File saved to: {file_path}")
        
        # Try to get URL
        file_url = default_storage.url(file_path)
        print(f"✓ File URL: {file_url}")
        
        # Check if file exists
        if default_storage.exists(file_path):
            print("✓ File exists in storage")
        else:
            print("✗ File does not exist in storage")
        
        # Clean up
        default_storage.delete(file_path)
        print("✓ Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Local storage test failed: {e}")
        return False

def test_supabase_storage():
    """Test Supabase storage functionality"""
    print("\n=== Testing Supabase Storage ===")
    
    if not is_supabase_available():
        print("✗ Supabase is not available")
        return False
    
    print("✓ Supabase is available")
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            print("✗ Could not get Supabase client")
            return False
        
        print("✓ Supabase client obtained")
        
        # Test bucket access
        try:
            bucket_info = supabase.storage.get_bucket(VERIFICATION_BUCKET)
            print(f"✓ Bucket '{VERIFICATION_BUCKET}' exists")
        except Exception as e:
            print(f"✗ Bucket access failed: {e}")
            print("Attempting to create bucket...")
            
            if ensure_bucket_exists(VERIFICATION_BUCKET):
                print(f"✓ Bucket '{VERIFICATION_BUCKET}' created successfully")
            else:
                print(f"✗ Failed to create bucket '{VERIFICATION_BUCKET}'")
                return False
        
        # Test file upload
        test_content = b"This is a test file for Supabase"
        test_filename = "test_supabase_upload.txt"
        
        try:
            result = supabase.storage.from_(VERIFICATION_BUCKET).upload(
                test_filename,
                test_content,
                file_options={'content-type': 'text/plain'}
            )
            
            if result:
                print("✓ File uploaded to Supabase")
                
                # Get public URL
                public_url = supabase.storage.from_(VERIFICATION_BUCKET).get_public_url(test_filename)
                print(f"✓ Public URL: {public_url}")
                
                # Clean up
                supabase.storage.from_(VERIFICATION_BUCKET).remove([test_filename])
                print("✓ Test file cleaned up")
                
                return True
            else:
                print("✗ Upload returned no result")
                return False
                
        except Exception as e:
            print(f"✗ Supabase upload failed: {e}")
            return False
        
    except Exception as e:
        print(f"✗ Supabase test failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("=== Testing Environment ===")
    
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    
    # Check if media directory exists
    if os.path.exists(settings.MEDIA_ROOT):
        print("✓ MEDIA_ROOT directory exists")
    else:
        print("✗ MEDIA_ROOT directory does not exist")
        try:
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            print("✓ Created MEDIA_ROOT directory")
        except Exception as e:
            print(f"✗ Could not create MEDIA_ROOT: {e}")
    
    # Check verification subdirectory
    verification_dir = os.path.join(settings.MEDIA_ROOT, 'verification')
    if os.path.exists(verification_dir):
        print("✓ Verification directory exists")
    else:
        print("✗ Verification directory does not exist")
        try:
            os.makedirs(verification_dir, exist_ok=True)
            print("✓ Created verification directory")
        except Exception as e:
            print(f"✗ Could not create verification directory: {e}")

if __name__ == "__main__":
    print("Storage Configuration Test")
    print("=" * 50)
    
    test_environment()
    local_ok = test_local_storage()
    supabase_ok = test_supabase_storage()
    
    print("\n=== Summary ===")
    print(f"Local Storage: {'✓ Working' if local_ok else '✗ Failed'}")
    print(f"Supabase Storage: {'✓ Working' if supabase_ok else '✗ Failed'}")
    
    if not local_ok and not supabase_ok:
        print("\n⚠️  Both storage methods are failing!")
        print("This explains why you're seeing placeholder URLs.")
    elif not supabase_ok:
        print("\n⚠️  Supabase is failing, but local storage should work.")
    else:
        print("\n✓ Storage configuration looks good!")