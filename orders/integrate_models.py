"""
Script to integrate models_updated.py into models.py
Run this script to ensure all models are properly registered in the Django admin.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

def integrate_models():
    """
    Integrate models from models_updated.py into models.py
    """
    # Read the content of both files
    with open('models.py', 'r') as f:
        models_content = f.read()
    
    with open('models_updated.py', 'r') as f:
        models_updated_content = f.read()
    
    # Check if models_updated.py content is already in models.py
    if "class OrderTracking(models.Model):" in models_content:
        print("Models from models_updated.py are already integrated into models.py")
        return
    
    # Append models_updated.py content to models.py
    with open('models.py', 'a') as f:
        f.write("\n\n# Models from models_updated.py\n")
        
        # Extract only the model classes from models_updated.py
        # Skip imports and other code at the beginning
        lines = models_updated_content.split('\n')
        start_line = 0
        for i, line in enumerate(lines):
            if line.startswith('class '):
                start_line = i
                break
        
        f.write('\n'.join(lines[start_line:]))
    
    print("Successfully integrated models from models_updated.py into models.py")

if __name__ == "__main__":
    integrate_models()