"""
MediaFire Storage Service
Handles file uploads, downloads, and management using MediaFire API
"""

import os
import logging
import requests
import hashlib
from typing import Optional, Tuple, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class MediaFireService:
    """
    Service class for interacting with MediaFire API
    
    To get MediaFire API credentials:
    1. Go to https://www.mediafire.com/developers/
    2. Sign up for a developer account
    3. Create a new application
    4. Get your App ID and API Key
    5. Add them to your .env file:
       MEDIAFIRE_APP_ID=your_app_id
       MEDIAFIRE_API_KEY=your_api_key
       MEDIAFIRE_EMAIL=your_mediafire_email
       MEDIAFIRE_PASSWORD=your_mediafire_password
    """
    
    BASE_URL = "https://www.mediafire.com/api/1.5"
    
    def __init__(self):
        """Initialize MediaFire service with credentials from settings"""
        self.app_id = getattr(settings, 'MEDIAFIRE_APP_ID', os.environ.get('MEDIAFIRE_APP_ID', ''))
        self.api_key = getattr(settings, 'MEDIAFIRE_API_KEY', os.environ.get('MEDIAFIRE_API_KEY', ''))
        self.email = getattr(settings, 'MEDIAFIRE_EMAIL', os.environ.get('MEDIAFIRE_EMAIL', ''))
        self.password = getattr(settings, 'MEDIAFIRE_PASSWORD', os.environ.get('MEDIAFIRE_PASSWORD', ''))
        self.folder_key = getattr(settings, 'MEDIAFIRE_FOLDER_KEY', os.environ.get('MEDIAFIRE_FOLDER_KEY', ''))
        
        self._session_token = None
        self._is_available = None
        
        logger.info(f"MediaFire service initialized. App ID present: {bool(self.app_id)}")
    
    def is_available(self) -> bool:
        """Check if MediaFire is properly configured and available"""
        if self._is_available is not None:
            return self._is_available
        
        if not all([self.app_id, self.api_key, self.email, self.password]):
            logger.warning("MediaFire credentials not fully configured")
            self._is_available = False
            return False
        
        try:
            # Try to get a session token
            token = self._get_session_token()
            self._is_available = bool(token)
            return self._is_available
        except Exception as e:
            logger.error(f"MediaFire availability check failed: {e}")
            self._is_available = False
            return False
    
    def _get_session_token(self) -> Optional[str]:
        """
        Get or refresh session token for MediaFire API
        
        Returns:
            Session token string or None if authentication fails
        """
        if self._session_token:
            return self._session_token
        
        try:
            # Generate signature for authentication
            signature = hashlib.sha256(
                f"{self.email}{self.password}{self.app_id}{self.api_key}".encode()
            ).hexdigest()
            
            # Request session token
            response = requests.post(
                f"{self.BASE_URL}/user/get_session_token.php",
                data={
                    'email': self.email,
                    'password': self.password,
                    'application_id': self.app_id,
                    'signature': signature,
                    'response_format': 'json'
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('response', {}).get('result') == 'Success':
                self._session_token = data['response']['session_token']
                logger.info("MediaFire session token obtained successfully")
                return self._session_token
            else:
                error_msg = data.get('response', {}).get('message', 'Unknown error')
                logger.error(f"Failed to get MediaFire session token: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting MediaFire session token: {e}")
            return None
    
    def _ensure_folder_exists(self, folder_name: str = "fagierrands") -> Optional[str]:
        """
        Ensure a folder exists in MediaFire, create if it doesn't
        
        Args:
            folder_name: Name of the folder to create/verify
            
        Returns:
            Folder key or None if operation fails
        """
        if self.folder_key:
            return self.folder_key
        
        try:
            session_token = self._get_session_token()
            if not session_token:
                return None
            
            # Try to create folder (will return existing if already exists)
            response = requests.post(
                f"{self.BASE_URL}/folder/create.php",
                data={
                    'session_token': session_token,
                    'foldername': folder_name,
                    'response_format': 'json'
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('response', {}).get('result') == 'Success':
                folder_key = data['response']['folder_key']
                logger.info(f"MediaFire folder '{folder_name}' ready with key: {folder_key}")
                return folder_key
            else:
                logger.warning(f"Could not create/verify MediaFire folder: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error ensuring MediaFire folder exists: {e}")
            return None
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = 'application/octet-stream',
        folder_name: str = "fagierrands"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to MediaFire
        
        Args:
            file_content: Binary content of the file
            filename: Name for the file
            content_type: MIME type of the file
            folder_name: Folder to upload to
            
        Returns:
            Tuple of (success: bool, file_url: str or None, error_message: str or None)
        """
        try:
            if not self.is_available():
                return False, None, "MediaFire service not available"
            
            session_token = self._get_session_token()
            if not session_token:
                return False, None, "Failed to authenticate with MediaFire"
            
            # Ensure folder exists
            folder_key = self._ensure_folder_exists(folder_name)
            
            # Prepare upload
            logger.info(f"Uploading {filename} to MediaFire (size: {len(file_content)} bytes)")
            
            # Get upload key
            upload_response = requests.post(
                f"{self.BASE_URL}/upload/check.php",
                data={
                    'session_token': session_token,
                    'filename': filename,
                    'size': len(file_content),
                    'hash': hashlib.md5(file_content).hexdigest(),
                    'response_format': 'json'
                },
                timeout=30
            )
            
            upload_response.raise_for_status()
            upload_data = upload_response.json()
            
            if upload_data.get('response', {}).get('result') != 'Success':
                error_msg = upload_data.get('response', {}).get('message', 'Upload check failed')
                return False, None, f"MediaFire upload check failed: {error_msg}"
            
            # Get upload details
            upload_key = upload_data['response'].get('upload_key')
            if not upload_key:
                return False, None, "No upload key received from MediaFire"
            
            # Perform actual upload
            files = {'file': (filename, file_content, content_type)}
            upload_params = {
                'session_token': session_token,
                'upload_key': upload_key,
                'response_format': 'json'
            }
            
            if folder_key:
                upload_params['folder_key'] = folder_key
            
            final_response = requests.post(
                f"{self.BASE_URL}/upload/instant.php",
                data=upload_params,
                files=files,
                timeout=120  # Longer timeout for file upload
            )
            
            final_response.raise_for_status()
            final_data = final_response.json()
            
            if final_data.get('response', {}).get('result') == 'Success':
                # Get the file key
                quickkey = final_data['response'].get('quickkey')
                if not quickkey:
                    return False, None, "No quickkey received from MediaFire"
                
                # Get public link
                link_response = requests.post(
                    f"{self.BASE_URL}/file/get_links.php",
                    data={
                        'session_token': session_token,
                        'quick_key': quickkey,
                        'link_type': 'direct_download',
                        'response_format': 'json'
                    },
                    timeout=30
                )
                
                link_response.raise_for_status()
                link_data = link_response.json()
                
                if link_data.get('response', {}).get('result') == 'Success':
                    links = link_data['response'].get('links', [])
                    if links and len(links) > 0:
                        file_url = links[0].get('direct_download')
                        logger.info(f"Successfully uploaded {filename} to MediaFire: {file_url}")
                        return True, file_url, None
                
                # Fallback to view link if direct download not available
                view_url = f"https://www.mediafire.com/file/{quickkey}/{filename}"
                logger.info(f"Uploaded {filename} to MediaFire (view link): {view_url}")
                return True, view_url, None
            else:
                error_msg = final_data.get('response', {}).get('message', 'Upload failed')
                return False, None, f"MediaFire upload failed: {error_msg}"
                
        except requests.exceptions.Timeout:
            return False, None, "MediaFire upload timeout"
        except requests.exceptions.RequestException as e:
            logger.error(f"MediaFire upload request error: {e}")
            return False, None, f"MediaFire request error: {str(e)}"
        except Exception as e:
            logger.error(f"MediaFire upload error: {e}")
            return False, None, f"MediaFire upload error: {str(e)}"
    
    def delete_file(self, file_url: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from MediaFire
        
        Args:
            file_url: URL of the file to delete
            
        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        try:
            if not self.is_available():
                return False, "MediaFire service not available"
            
            # Extract quickkey from URL
            quickkey = None
            if '/file/' in file_url:
                parts = file_url.split('/file/')
                if len(parts) > 1:
                    quickkey = parts[1].split('/')[0]
            
            if not quickkey:
                return False, "Could not extract file key from URL"
            
            session_token = self._get_session_token()
            if not session_token:
                return False, "Failed to authenticate with MediaFire"
            
            # Delete the file
            response = requests.post(
                f"{self.BASE_URL}/file/delete.php",
                data={
                    'session_token': session_token,
                    'quick_key': quickkey,
                    'response_format': 'json'
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('response', {}).get('result') == 'Success':
                logger.info(f"Successfully deleted file from MediaFire: {quickkey}")
                return True, None
            else:
                error_msg = data.get('response', {}).get('message', 'Delete failed')
                return False, f"MediaFire delete failed: {error_msg}"
                
        except Exception as e:
            logger.error(f"MediaFire delete error: {e}")
            return False, f"MediaFire delete error: {str(e)}"
    
    def get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file from MediaFire
        
        Args:
            file_url: URL of the file
            
        Returns:
            Dictionary with file information or None if operation fails
        """
        try:
            if not self.is_available():
                return None
            
            # Extract quickkey from URL
            quickkey = None
            if '/file/' in file_url:
                parts = file_url.split('/file/')
                if len(parts) > 1:
                    quickkey = parts[1].split('/')[0]
            
            if not quickkey:
                return None
            
            session_token = self._get_session_token()
            if not session_token:
                return None
            
            # Get file info
            response = requests.post(
                f"{self.BASE_URL}/file/get_info.php",
                data={
                    'session_token': session_token,
                    'quick_key': quickkey,
                    'response_format': 'json'
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('response', {}).get('result') == 'Success':
                return data['response'].get('file_info', {})
            
            return None
            
        except Exception as e:
            logger.error(f"MediaFire get file info error: {e}")
            return None


# Global instance
_mediafire_service = None


def get_mediafire_service() -> MediaFireService:
    """Get or create MediaFire service instance"""
    global _mediafire_service
    if _mediafire_service is None:
        _mediafire_service = MediaFireService()
    return _mediafire_service


def is_mediafire_available() -> bool:
    """Check if MediaFire service is available"""
    try:
        service = get_mediafire_service()
        return service.is_available()
    except Exception as e:
        logger.error(f"Error checking MediaFire availability: {e}")
        return False


