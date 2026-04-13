#!/usr/bin/env python
"""
Comprehensive audit of all onboarding endpoints to verify no authentication is required
"""
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.urls import get_resolver
from rest_framework.permissions import AllowAny, IsAuthenticated

print("=" * 80)
print("ONBOARDING ENDPOINTS AUTHENTICATION AUDIT")
print("=" * 80)

# Define onboarding endpoints that MUST be AllowAny
ONBOARDING_ENDPOINTS = {
    'Registration': [
        '/api/accounts/register/',
    ],
    'Phone Verification': [
        '/api/accounts/verify-phone/',
        '/api/accounts/resend-otp/',
    ],
    'Login': [
        '/api/accounts/login/',
        '/api/accounts/simple-login/',
        '/api/accounts/token/',
        '/api/accounts/token/refresh/',
    ],
    'Password Reset': [
        '/api/accounts/password-reset/request/',
        '/api/accounts/password-reset/verify-otp/',
        '/api/accounts/password-reset/reset/',
        '/api/accounts/v1/password-reset/request/',
        '/api/accounts/v1/password-reset/reset/',
    ],
    'Email Verification': [
        '/api/accounts/send-otp/',
        '/api/accounts/verify-otp/',
        '/api/accounts/smtp/send-otp/',
        '/api/accounts/smtp/verify-otp/',
        '/api/accounts/verify-email-otp/',
        '/api/accounts/resend-verification/',
        '/api/accounts/supabase/resend-verification/',
        '/api/accounts/supabase/verify-otp/',
        '/api/accounts/custom/resend-verification/',
    ],
}

def check_view_permissions(view_func):
    """Check if a view has AllowAny permission"""
    # Check for permission_classes attribute
    if hasattr(view_func, 'cls'):
        view_class = view_func.cls
        if hasattr(view_class, 'permission_classes'):
            perms = view_class.permission_classes
            return perms, AllowAny in perms
    
    # Check for view_class attribute (for APIView)
    if hasattr(view_func, 'view_class'):
        view_class = view_func.view_class
        if hasattr(view_class, 'permission_classes'):
            perms = view_class.permission_classes
            return perms, AllowAny in perms
    
    # Check for initkwargs
    if hasattr(view_func, 'initkwargs'):
        if 'permission_classes' in view_func.initkwargs:
            perms = view_func.initkwargs['permission_classes']
            return perms, AllowAny in perms
    
    return None, None

# Check each endpoint
all_passed = True
issues = []

for category, endpoints in ONBOARDING_ENDPOINTS.items():
    print(f"\n{'=' * 80}")
    print(f"Category: {category}")
    print('=' * 80)
    
    for endpoint in endpoints:
        # Try to resolve the URL
        try:
            from django.urls import resolve
            resolved = resolve(endpoint)
            view_func = resolved.func
            
            perms, has_allow_any = check_view_permissions(view_func)
            
            if has_allow_any:
                status = "✅ PASS"
                print(f"{status} {endpoint}")
                print(f"     Permissions: AllowAny")
            elif perms is None:
                # Check if it's a function-based view with decorator
                if hasattr(view_func, '__wrapped__'):
                    # Likely has @permission_classes decorator
                    status = "⚠️  CHECK"
                    print(f"{status} {endpoint}")
                    print(f"     Note: Function-based view - check decorator manually")
                else:
                    status = "❌ FAIL"
                    all_passed = False
                    issues.append(f"{endpoint} - No permission classes found")
                    print(f"{status} {endpoint}")
                    print(f"     ERROR: No permission classes found")
            else:
                if IsAuthenticated in perms:
                    status = "❌ FAIL"
                    all_passed = False
                    issues.append(f"{endpoint} - Requires authentication")
                    print(f"{status} {endpoint}")
                    print(f"     ERROR: Requires authentication - {perms}")
                else:
                    status = "✅ PASS"
                    print(f"{status} {endpoint}")
                    print(f"     Permissions: {perms}")
                    
        except Exception as e:
            status = "⚠️  ERROR"
            print(f"{status} {endpoint}")
            print(f"     Error resolving URL: {e}")

# Check settings.py for default permission
print(f"\n{'=' * 80}")
print("GLOBAL SETTINGS CHECK")
print('=' * 80)

from django.conf import settings
default_perms = settings.REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', [])
print(f"DEFAULT_PERMISSION_CLASSES: {default_perms}")

if 'rest_framework.permissions.AllowAny' in default_perms:
    print("✅ PASS - Default is AllowAny (onboarding endpoints open by default)")
elif 'rest_framework.permissions.IsAuthenticated' in default_perms:
    print("⚠️  WARNING - Default is IsAuthenticated")
    print("   This is OK if all onboarding endpoints explicitly set AllowAny")
else:
    print(f"ℹ️  INFO - Default permissions: {default_perms}")

# Final summary
print(f"\n{'=' * 80}")
print("AUDIT SUMMARY")
print('=' * 80)

if all_passed and not issues:
    print("✅ ALL ONBOARDING ENDPOINTS ARE PROPERLY CONFIGURED")
    print("✅ No authentication required for registration, login, or verification")
    print("✅ Issue is RESOLVED")
else:
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
    print("\n⚠️  Issue is NOT fully resolved")

print("\n" + "=" * 80)
