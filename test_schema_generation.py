#!/usr/bin/env python
"""
Test script to verify schema generation works without errors
Run this before deploying to catch any serializer issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg import openapi
from rest_framework import permissions

def test_schema_generation():
    """Test that schema generation doesn't crash"""
    print("Testing schema generation...")
    
    try:
        generator = OpenAPISchemaGenerator(
            info=openapi.Info(
                title="Fagi Errands API",
                default_version='v1',
                description="API for Fagi Errands application",
            ),
            url='http://localhost:8000',
        )
        
        schema = generator.get_schema(request=None, public=True)
        
        print("✅ Schema generation successful!")
        print(f"✅ Found {len(schema.paths)} API endpoints")
        print("\nSample endpoints:")
        for path in list(schema.paths.keys())[:10]:
            print(f"  - {path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_schema_generation()
    sys.exit(0 if success else 1)
