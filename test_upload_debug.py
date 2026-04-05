"""
Debug script to test image upload with detailed error logging
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
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    img_bytes.name = 'test_image.jpg'
    return img_bytes

def main():
    print("🚀 Starting Debug Upload Test...\n")
    
    # Get user
    try:
        user = User.objects.filter(email='ogollawayne387@gmail.com').first()
        if not user:
            print("❌ User not found")
            return
        print(f"✅ User: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"   User Type: {getattr(user, 'user_type', 'user')}")
        
        # Temporarily make user an admin for testing
        original_user_type = getattr(user, 'user_type', 'user')
        user.user_type = 'admin'
        user.save()
        print(f"   ⚠️  Temporarily set user_type to 'admin' for testing")
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return
    
    # Get order for this user
    try:
        # Try to find an order where the user is the client
        order = Order.objects.filter(client_id=user.id).first()
        if not order:
            # If no order found, create a test order
            print("⚠️  No existing order found for user, using any order for testing")
            order = Order.objects.all().first()
            if not order:
                print("❌ No orders found in database")
                return
        print(f"✅ Order: #{order.id}")
        print(f"   Client ID: {order.client_id}, User ID: {user.id}")
        print(f"   Assistant ID: {order.assistant_id}")
    except Exception as e:
        print(f"❌ Error getting order: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return
    
    # Create API client
    client = APIClient()
    
    # Get JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    print(f"✅ JWT Token set\n")
    
    # Create test image
    test_image = create_test_image()
    print(f"✅ Test image created\n")
    
    # Make upload request
    url = f'/api/orders/{order.id}/attachments/upload/'
    print(f"📤 Uploading to: {url}")
    
    try:
        response = client.post(
            url,
            {'file': test_image},
            format='multipart'
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"   Response Data: {response.data if hasattr(response, 'data') else response.content}")
        
        if response.status_code in [200, 201]:
            print("\n✅ Upload successful!")
        else:
            print("\n❌ Upload failed!")
            
    except Exception as e:
        print(f"\n❌ Exception during upload: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
    finally:
        # Restore original user type
        try:
            user.user_type = original_user_type
            user.save()
            print(f"\n🔄 Restored user_type to '{original_user_type}'")
        except:
            pass

if __name__ == '__main__':
    main()