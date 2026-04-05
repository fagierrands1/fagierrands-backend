"""
Quick test to verify upload functionality and get valid credentials
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image
import io

User = get_user_model()

def create_test_image():
    """Create a test image in memory"""
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    img_bytes.name = 'test_image.jpg'
    return img_bytes

def main():
    print("=" * 60)
    print("  Quick Upload Test")
    print("=" * 60)
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='testuser@example.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'admin',  # Make admin to bypass permission checks
            'is_active': True,
        }
    )
    
    if created:
        user.set_password('TestPass123!')
        user.save()
        print(f"✅ Created new test user: {user.email}")
    else:
        print(f"✅ Using existing user: {user.email}")
    
    print(f"   User ID: {user.id}")
    print(f"   User Type: {user.user_type}")
    
    # Get an order to upload to
    order = Order.objects.first()
    if not order:
        print("❌ No orders found in database")
        return
    
    print(f"\n✅ Using Order ID: {order.id}")
    print(f"   Client ID: {order.client_id}")
    
    # Create API client
    client = APIClient()
    
    # Get JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    print(f"\n✅ JWT Token generated")
    print(f"   Token: {access_token[:30]}...")
    
    # Set authentication
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Create test image
    test_image = create_test_image()
    
    # Upload
    print(f"\n📤 Uploading image to order {order.id}...")
    url = f'/api/orders/{order.id}/attachments/upload/'
    print(f"   URL: {url}")
    
    response = client.post(
        url,
        {'file': test_image},
        format='multipart'
    )
    
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ Upload successful!")
        print(f"   File ID: {response.data.get('id')}")
        print(f"   File Name: {response.data.get('file_name')}")
        print(f"   File Size: {response.data.get('file_size')} bytes")
        print(f"   Signed URL: {'Generated ✓' if response.data.get('signed_url') else 'Not generated ✗'}")
        
        print("\n" + "=" * 60)
        print("  ✅ TEST PASSED!")
        print("=" * 60)
        print("\n📱 You can now test from mobile app with these credentials:")
        print(f"   Email: {user.email}")
        print(f"   Password: TestPass123!")
        print(f"   Order ID: {order.id}")
        
    else:
        print("❌ Upload failed!")
        print(f"   Response: {response.data}")
        
        print("\n" + "=" * 60)
        print("  ❌ TEST FAILED")
        print("=" * 60)

if __name__ == '__main__':
    main()