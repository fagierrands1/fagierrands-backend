# Django Admin Registration Guide

This guide explains how to ensure all models in your project are properly registered in the Django admin interface.

## Overview

All models in the following apps have been registered in the Django admin:

- accounts
- locations
- orders
- admin_dashboard
- notifications

## How to Access the Admin Interface

1. Make sure the Django development server is running:
   ```
   python manage.py runserver
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/admin/
   ```

3. Log in with your superuser credentials.

## Creating a Superuser

If you haven't created a superuser yet, run:
```
python manage.py createsuperuser
```

Follow the prompts to create a username, email, and password.

## Integrating models_updated.py

The `orders` app has an additional file called `models_updated.py` with extra models. To ensure these models are properly registered in the admin:

1. Run the integration script:
   ```
   cd fagierrands/fagierrandsbackup/orders
   python integrate_models.py
   ```

2. Restart the Django development server.

## Manually Registering Models

If you create new models in the future, make sure to register them in the admin. In your app's `admin.py` file:

```python
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ('field1', 'field2', 'field3')  # Fields to display in the list view
    list_filter = ('field1', 'field2')             # Fields to filter by
    search_fields = ('field1', 'field3')           # Fields to search
    date_hierarchy = 'created_at'                  # Date navigation (if applicable)
```

## Customizing the Admin Interface

You can customize how your models appear in the admin interface by modifying the ModelAdmin classes in each app's `admin.py` file.

Common customizations include:
- `list_display`: Fields to show in the list view
- `list_filter`: Fields to filter by
- `search_fields`: Fields to search
- `readonly_fields`: Fields that cannot be edited
- `fieldsets`: Group fields into sections
- `inlines`: Include related models

## Troubleshooting

If you don't see a model in the admin interface:

1. Make sure the model is registered in the app's `admin.py` file.
2. Check that the app is included in `INSTALLED_APPS` in your settings.py.
3. Run `python manage.py makemigrations` and `python manage.py migrate` to ensure the database schema is up to date.
4. Restart the Django development server.