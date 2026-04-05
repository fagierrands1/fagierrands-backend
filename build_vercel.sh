#!/bin/bash
set -e

echo "Starting build process..."

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Install IntaSend package
echo "Installing IntaSend package..."
pip install intasend-python

# Check dependencies
echo "Checking dependencies..."
python check_dependencies.py || true

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"