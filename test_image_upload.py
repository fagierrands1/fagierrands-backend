"""
Test script to simulate image upload to an order
This tests the complete upload flow including authentication

Usage:
python test_image_upload.py <order_id> <image_path>

Example:
python test_image_upload.py 1 test_image.jpg
"""

import os
import sys
import django
import requests
from io import BytesIO
from PIL import Image

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()

def create_test_image(filename='test_image.jpg'):
    """Create a simple test image"""
    print(f"📸 Creating test image: {filename}")
    
    # Create a simple 800x600 red image
    img = Image.new('RGB', (800, 600), color='red')
    
    # Add some text to make it identifiable
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes
    draw.rectangle([100, 100, 700, 500], outline='white', width=5)
    draw.ellipse([200, 200, 600, 400], fill='blue', outline='white', width=3)
    
    # Save the image
    img.save(filename, 'JPEG', quality=85)
    file_size = os.path.getsize(filename)
    print(f"✅ Test image created: {filename} ({file_size} bytes)")
    
    return filename

def get_or_create_test_user():
    """Get or create a test user for authentication"""
    print("\n👤 Setting up test user...")
    
    # Try to get an existing user
    try:
        user = User.objects.filter(user_type='user').first()
        if user:
            print(f"✅ Using existing user: {user.email or user.phone_number}")
            return user
    except Exception as e:
        print(f"⚠️  Error finding user: {e}")
    
    # Create a test user if none exists
    try:
        user = User.objects.create_user(
            phone_number='+254700000001',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            user_type='user'
        )
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
        return user
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

def get_or_create_test_order(user):
    """Get or create a test order"""
    print("\n📦 Setting up test order...")
    
    # Try to get any existing order (from any user)
    try:
        order = Order.objects.first()
        if order:
            print(f"✅ Using existing order: #{order.id} - {order.title}")
            print(f"   Client: {order.client.email or order.client.phone_number}")
            return order
    except Exception as e:
        print(f"⚠️  Error finding order: {e}")
    
    print("❌ No orders found in database")
    print("   Please create an order from the mobile app first")
    return None

def get_auth_token(user):
    """Get or create JWT authentication token"""
    print("\n🔑 Getting JWT authentication token...")
    
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Generate JWT token for the user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"✅ JWT Access Token: {access_token[:30]}...")
        return access_token
    except Exception as e:
        print(f"❌ Error generating JWT token: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None

def test_upload(order_id, image_path, token):
    """Test the upload endpoint"""
    print("\n" + "=" * 60)
    print("TESTING IMAGE UPLOAD")
    print("=" * 60)
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    file_size = os.path.getsize(image_path)
    print(f"📤 Uploading: {image_path}")
    print(f"   File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
    print(f"   Order ID: {order_id}")
    
    # Prepare the upload
    url = f'http://127.0.0.1:8000/api/orders/{order_id}/attachments/upload/'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        with open(image_path, 'rb') as f:
            files = {
                'file': (os.path.basename(image_path), f, 'image/jpeg')
            }
            
            print(f"\n🌐 Making request to: {url}")
            print(f"   Headers: Authorization: Bearer {token[:30]}...")
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200 or response.status_code == 201:
                print("✅ Upload successful!")
                try:
                    data = response.json()
                    print(f"   Response data: {data}")
                    return True
                except:
                    print(f"   Response text: {response.text}")
                    return True
            else:
                print(f"❌ Upload failed!")
                print(f"   Response: {response.text}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Is Django server running?")
        print("   Start it with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    print("\n🚀 Starting Image Upload Test...\n")
    
    # Step 1: Create test image
    image_path = create_test_image('test_upload_image.jpg')
    
    # Step 2: Get or create test user
    user = get_or_create_test_user()
    if not user:
        print("\n❌ Failed to set up test user")
        return
    
    # Step 3: Get or create test order
    order = get_or_create_test_order(user)
    if not order:
        print("\n❌ Failed to set up test order")
        return
    
    # Step 4: Get authentication token
    token = get_auth_token(user)
    if not token:
        print("\n❌ Failed to get authentication token")
        return
    
    # Step 5: Test upload
    success = test_upload(order.id, image_path, token)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"User: {user.email or user.phone_number}")
    print(f"Order: #{order.id} - {order.title}")
    print(f"Image: {image_path}")
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 60)
    
    if success:
        print("\n🎉 Image upload test passed!")
        print(f"   Check Supabase dashboard for the uploaded file")
        print(f"   Path: orders/{order.id}/...")
    else:
        print("\n⚠️  Image upload test failed")
        print("   Check Django console logs for details")
    
    # Cleanup
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"\n🗑️  Cleaned up test image: {image_path}")
    except:
        pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()