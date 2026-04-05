import os
import logging
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .supabase_client import get_supabase_client, VERIFICATION_BUCKET, is_supabase_available, ensure_bucket_exists
from .mediafire_service import get_mediafire_service, is_mediafire_available

logger = logging.getLogger(__name__)

def upload_verification_image(file, user_id, file_type='verification'):
    """
    Upload verification image to MediaFire storage with Supabase and local storage as fallbacks.
    
    Storage priority:
    1. MediaFire (primary)
    2. Supabase (fallback)
    3. Local storage (last resort)
    
    Args:
        file: File object to upload
        user_id: ID of the user uploading the file
        file_type: Type of verification file (default: 'verification')
    
    Returns:
        tuple: (success: bool, file_path: str or None, error_message: str or None)
    """
    
    logger.info(f"Starting upload for user {user_id}, file_type: {file_type}")
    
    if not file:
        logger.error("No file provided for upload")
        return False, None, "No file provided"
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.name)[1]
    filename = f"{user_id}_{file_type}_{file.name}"
    
    logger.info(f"Generated filename: {filename}")
    logger.info(f"File size: {file.size} bytes")
    logger.info(f"File content type: {getattr(file, 'content_type', 'unknown')}")
    
    # Try MediaFire first if available
    mediafire_available = is_mediafire_available()
    logger.info(f"MediaFire available: {mediafire_available}")
    
    if mediafire_available:
        try:
            mediafire = get_mediafire_service()
            logger.info(f"MediaFire service obtained: {mediafire is not None}")
            
            if mediafire:
                # Read file content
                file_content = file.read()
                logger.info(f"File content read for MediaFire, size: {len(file_content)} bytes")
                
                # Upload to MediaFire
                logger.info(f"Attempting upload to MediaFire")
                success, file_url, error = mediafire.upload_file(
                    file_content=file_content,
                    filename=filename,
                    content_type=file.content_type or 'application/octet-stream',
                    folder_name='fagierrands_verification'
                )
                
                if success and file_url:
                    logger.info(f"Successfully uploaded {filename} to MediaFire: {file_url}")
                    return True, file_url, None
                else:
                    logger.warning(f"MediaFire upload failed: {error}, trying Supabase fallback")
                    # Reset file pointer for fallback
                    try:
                        file.seek(0)
                    except Exception as seek_error:
                        logger.warning(f"Could not reset file pointer after MediaFire failure: {seek_error}")
                    
        except Exception as e:
            logger.warning(f"MediaFire upload exception for {filename}: {e}, falling back to Supabase")
            # Reset file pointer for fallback
            try:
                file.seek(0)
            except Exception as seek_error:
                logger.warning(f"Could not reset file pointer after MediaFire exception: {seek_error}")
    else:
        logger.info("MediaFire not available, trying Supabase")
    
    # Try Supabase as fallback
    supabase_available = is_supabase_available()
    logger.info(f"Supabase available: {supabase_available}")
    
    if supabase_available:
        try:
            supabase = get_supabase_client()
            logger.info(f"Supabase client obtained: {supabase is not None}")
            
            if supabase:
                # Note: Bucket should be created manually in Supabase dashboard
                # Auto-creation disabled due to permission restrictions
                
                # Read file content
                file_content = file.read()
                logger.info(f"File content read, size: {len(file_content)} bytes")
                
                # Upload to Supabase storage
                logger.info(f"Attempting upload to bucket: {VERIFICATION_BUCKET}")
                
                # Try to upload the file
                try:
                    result = supabase.storage.from_(VERIFICATION_BUCKET).upload(
                        filename, 
                        file_content,
                        file_options={
                            'content-type': file.content_type or 'application/octet-stream'
                        }
                    )
                    logger.info(f"Upload result: {result}")
                    
                    # Check if upload was successful
                    # Supabase upload returns a response object, check for errors
                    if hasattr(result, 'get') and result.get('error'):
                        logger.error(f"Supabase upload error: {result.get('error')}")
                        raise Exception(f"Upload failed: {result.get('error')}")
                    
                    # Get the public URL
                    public_url = supabase.storage.from_(VERIFICATION_BUCKET).get_public_url(filename)
                    logger.info(f"Successfully uploaded {filename} to Supabase: {public_url}")
                    return True, public_url, None
                    
                except Exception as upload_error:
                    logger.error(f"Supabase upload exception for {filename}: {upload_error}")
                    raise upload_error
                    
        except Exception as e:
            logger.warning(f"Supabase upload failed for {filename}: {e}, falling back to local storage")
            # Reset file pointer for fallback
            try:
                file.seek(0)
            except Exception as seek_error:
                logger.warning(f"Could not reset file pointer after Supabase failure: {seek_error}")
    else:
        logger.info("Supabase not available, using local storage")
    
    # Fallback to Django's default storage (local/media files)
    logger.info("Attempting fallback to local storage")
    try:
        # Reset file pointer if it was read before
        try:
            file.seek(0)
        except Exception as seek_error:
            logger.warning(f"Could not reset file pointer: {seek_error}")
        
        # Ensure the verification directory exists
        from django.conf import settings
        verification_dir = os.path.join(settings.MEDIA_ROOT, 'verification')
        os.makedirs(verification_dir, exist_ok=True)
        logger.info(f"Ensured verification directory exists: {verification_dir}")
        
        # Save using Django's default storage
        logger.info(f"Saving to local storage with path: verification/{filename}")
        file_content = file.read()
        logger.info(f"Read file content, size: {len(file_content)} bytes")
        
        file_path = default_storage.save(f'verification/{filename}', ContentFile(file_content))
        full_path = default_storage.url(file_path)
        
        logger.info(f"Successfully uploaded {filename} to local storage: {file_path}")
        logger.info(f"Full URL: {full_path}")
        return True, full_path, None
        
    except Exception as e:
        error_msg = f"Failed to upload {filename} to local storage: {e}"
        logger.error(error_msg)
        
        # Last resort fallback - return a placeholder URL with error info
        placeholder_url = f"https://via.placeholder.com/300?text=Upload+Failed+-+Check+Logs"
        logger.error(f"All upload methods failed for {filename}. Using placeholder URL.")
        return False, placeholder_url, f"All upload methods failed for {filename}"

def delete_verification_image(file_path, user_id):
    """
    Delete verification image from storage (MediaFire, Supabase, or local).
    
    Args:
        file_path: Path to the file to delete
        user_id: ID of the user (for logging purposes)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    
    if not file_path:
        return False, "No file path provided"
    
    # Try MediaFire first if it's a MediaFire URL
    if is_mediafire_available() and 'mediafire' in file_path.lower():
        try:
            mediafire = get_mediafire_service()
            if mediafire:
                success, error = mediafire.delete_file(file_path)
                if success:
                    logger.info(f"Successfully deleted {file_path} from MediaFire")
                    return True, None
                else:
                    logger.error(f"Failed to delete {file_path} from MediaFire: {error}")
        except Exception as e:
            logger.error(f"MediaFire deletion exception for {file_path}: {e}")
    
    # Try Supabase if available and if it's a Supabase URL
    if is_supabase_available() and 'supabase' in file_path:
        try:
            supabase = get_supabase_client()
            if supabase:
                # Extract filename from URL
                filename = file_path.split('/')[-1]
                
                # Delete from Supabase storage
                result = supabase.storage.from_(VERIFICATION_BUCKET).remove([filename])
                
                if result:
                    logger.info(f"Successfully deleted {filename} from Supabase")
                    return True, None
                else:
                    logger.error(f"Failed to delete {filename} from Supabase")
                    
        except Exception as e:
            logger.error(f"Supabase deletion failed for {file_path}: {e}")
    
    # Fallback to Django's default storage
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info(f"Successfully deleted {file_path} from local storage")
            return True, None
        else:
            logger.warning(f"File {file_path} doesn't exist in local storage")
            return True, None  # Consider it successful if file doesn't exist
            
    except Exception as e:
        error_msg = f"Failed to delete {file_path} from local storage: {e}"
        logger.error(error_msg)
        return False, error_msg

def get_verification_image_url(file_path):
    """
    Get the full URL for a verification image.
    
    Args:
        file_path: Path to the file
    
    Returns:
        str: Full URL to the file or None if not found
    """
    
    if not file_path:
        return None
    
    # If it's already a full URL (Supabase), return as-is
    if file_path.startswith(('http://', 'https://')):
        return file_path
    
    # For local storage, use Django's default storage URL
    try:
        return default_storage.url(file_path)
    except Exception as e:
        logger.error(f"Failed to get URL for {file_path}: {e}")
        return None