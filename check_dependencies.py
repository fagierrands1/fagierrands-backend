#!/usr/bin/env python
"""
Script to check if all required dependencies are installed correctly.
"""

import sys
import importlib
import pkg_resources

def check_package(package_name):
    """Check if a package is installed and return its version."""
    try:
        package = importlib.import_module(package_name)
        try:
            version = pkg_resources.get_distribution(package_name).version
            return True, version
        except pkg_resources.DistributionNotFound:
            return True, "Unknown version"
    except ImportError:
        return False, None

def main():
    """Check all required packages."""
    packages = [
        # Core Django dependencies
        "django",
        "rest_framework",
        "corsheaders",
        "django_filters",
        "drf_yasg",
        
        # Database
        "psycopg2",
        
        # Supabase
        "supabase",
        "postgrest",
        "realtime",
        "supafunc",
        
        # Celery
        "celery",
        "redis",
        
        # Channels
        "channels",
        "channels_redis",
        
        # Web push
        "pywebpush",
        
        # Payment
        "intasend",
        
        # Other
        "geopy",
        "PIL",
    ]
    
    print("Checking dependencies...")
    print("-" * 50)
    
    all_installed = True
    
    for package in packages:
        installed, version = check_package(package)
        status = f"✅ {version}" if installed else "❌ Not installed"
        print(f"{package.ljust(20)} {status}")
        
        if not installed:
            all_installed = False
    
    print("-" * 50)
    if all_installed:
        print("All dependencies are installed! 🎉")
    else:
        print("Some dependencies are missing. Please install them.")
    
    return 0 if all_installed else 1

if __name__ == "__main__":
    sys.exit(main())