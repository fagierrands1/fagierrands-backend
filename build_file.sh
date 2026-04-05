#!/bin/bash

# Exit the script if any command fails
set -e

# Install dependencies from requirements.txt
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Run any custom build steps if needed
echo "Custom build steps (if any)..."
# Add any other necessary build commands here

echo "Build complete."