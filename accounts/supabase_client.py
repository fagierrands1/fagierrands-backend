import os
import logging
from dotenv import load_dotenv
from django.conf import settings

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Supabase client with error handling
try:
    from supabase import create_client, Client
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not found in environment variables")
        supabase = None
        admin_supabase = None
    else:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        
        # Initialize admin client with service role key for storage operations
        if supabase_service_role_key:
            admin_supabase: Client = create_client(supabase_url, supabase_service_role_key)
            logger.info("Supabase admin client initialized successfully")
        else:
            logger.warning("Supabase service role key not found, admin operations may fail")
            admin_supabase = supabase  # Fallback to regular client
        
except ImportError as e:
    logger.error(f"Failed to import Supabase: {e}")
    logger.error("This is likely due to a dependency version mismatch between supabase and postgrest packages")
    supabase = None
    admin_supabase = None
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None
    admin_supabase = None

# Define storage bucket name for verification documents
VERIFICATION_BUCKET = 'user-uploads'

# Create a helper function to ensure buckets exist
def ensure_bucket_exists(bucket_name):
    """
    Ensure that a Supabase storage bucket exists.
    Creates the bucket if it doesn't exist.
    """
    if not supabase:
        logger.warning("Supabase client not available, cannot ensure bucket exists")
        return False
        
    try:
        # Try to get bucket details to check if it exists
        supabase.storage.get_bucket(bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists")
        return True
    except Exception as e:
        logger.info(f"Bucket '{bucket_name}' doesn't exist, attempting to create it")
        try:
            # Create the bucket if it doesn't exist (public for verification documents)
            result = supabase.storage.create_bucket(bucket_name)
            logger.info(f"Successfully created bucket '{bucket_name}'")
            return True
        except Exception as create_error:
            logger.error(f"Failed to create bucket '{bucket_name}': {create_error}")
            return False

# Call this when your Django app starts
def initialize_supabase_storage():
    """
    Initialize Supabase storage by ensuring required buckets exist.
    """
    if not supabase:
        logger.warning("Supabase client not available, skipping storage initialization")
        return False
        
    try:
        success = ensure_bucket_exists(VERIFICATION_BUCKET)
        if success:
            logger.info("Supabase storage initialized successfully")
        else:
            logger.warning("Supabase storage initialization completed with warnings")
        return success
    except Exception as e:
        logger.error(f"Failed to initialize Supabase storage: {e}")
        return False

# Helper function to check if Supabase is available
def is_supabase_available():
    """
    Check if Supabase client is available and functional.
    """
    return supabase is not None

# Graceful fallback for when Supabase is not available
def get_supabase_client():
    """
    Get the Supabase client with proper error handling.
    """
    if not supabase:
        logger.warning("Supabase client requested but not available")
        return None
    return supabase

def get_admin_supabase_client():
    """
    Get the Supabase admin client (with service role key) for storage operations.
    This client has elevated permissions for file uploads and management.
    """
    if not admin_supabase:
        logger.warning("Supabase admin client requested but not available")
        return None
    return admin_supabase