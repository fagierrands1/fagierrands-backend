import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from accounts.models import User

username = input("Username: ")
email = input("Email: ")
password = input("Password: ")

if User.objects.filter(username=username).exists():
    print(f"User {username} already exists!")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser {username} created successfully!")
