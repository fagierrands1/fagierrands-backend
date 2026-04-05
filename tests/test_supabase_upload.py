#!/usr/bin/env python
import os
import sys
import django
from io import BytesIO
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.supabase_client import get_supabase_client, is_supabase_available, VERIFICATION_BUCKET
from accounts.storage_utils import upload_verification_image
from django.core.files.uploadedfile import SimpleUploadedFile

def test_supabase_connection():
    print("=== Testing Supabase Connection ===")
    
    # Test if Supabase is available
    available = is_supabase_available()
    print(f"Supabase available: {available}")
    
    if available:
        client = get_supabase_client()
        print(f"Supabase client: {client is not None}")
        
        if client:
            try:
                # Test bucket access
                print(f"Testing bucket access for: {VERIFICATION_BUCKET}")
                bucket_info = client.storage.get_bucket(VERIFICATION_BUCKET)
                print(f"Bucket info: {bucket_info}")
            except Exception as e:
                print(f"Bucket access error: {e}")
                
                # Try to create bucket
                try:
                    print("Attempting to create bucket...")
                    result = client.storage.create_bucket(VERIFICATION_BUCKET)
                    print(f"Bucket creation result: {result}")
                except Exception as create_error:
                    print(f"Bucket creation error: {create_error}")
    
    return available

def create_test_image():
    """Create a simple test image file"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    
    # Create a Django uploaded file
    test_file = SimpleUploadedFile(
        name='test_image.jpg',
        content=img_io.getvalue(),
        content_type='image/jpeg'
    )
    
    return test_file

def test_file_upload():
    print("\n=== Testing File Upload ===")
    
    # Create a test image
    test_file = create_test_image()
    print(f"Created test file: {test_file.name}, size: {test_file.size} bytes")
    
    # Test upload
    try:
        success, result, error = upload_verification_image(test_file, 999, 'test_upload')
        print(f"Upload success: {success}")
        print(f"Upload result: {result}")
        print(f"Upload error: {error}")
        
        if success and result:
            print(f"✅ Upload successful! URL: {result}")
        else:
            print(f"❌ Upload failed: {error}")
            
    except Exception as e:
        print(f"❌ Upload exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supabase_connection()
    test_file_upload()