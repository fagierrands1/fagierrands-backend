import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.models import User

user = User.objects.get(username='admin')
user.set_password('admin123')
user.save()
print("Password reset successfully!")
print("\nCredentials:")
print("Username: admin")
print("Password: admin123")
print("URL: http://localhost:8000/admin/")
