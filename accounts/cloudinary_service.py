"""Cloudinary storage service integration."""
from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
except ImportError as import_error:
    cloudinary = None  # type: ignore
    logger.error("Cloudinary dependency not installed: %s", import_error)


class CloudinaryService:
    """Wrapper around Cloudinary Python SDK with project defaults."""

    def __init__(self) -> None:
        self.cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
        self.api_key = getattr(settings, 'CLOUDINARY_API_KEY', '')
        self.api_secret = getattr(settings, 'CLOUDINARY_API_SECRET', '')
        self.secure = getattr(settings, 'CLOUDINARY_SECURE', True)
        self.upload_preset = getattr(settings, 'CLOUDINARY_UPLOAD_PRESET', '')

        logger.debug(
            "CloudinaryService init - cloud_name present: %s, secure: %s",
            bool(self.cloud_name),
            self.secure,
        )

        self._is_configured = all([self.cloud_name, self.api_key, self.api_secret])
        self._configured_client = False

    def _configure_client(self) -> bool:
        """Configure Cloudinary client if credentials are available."""
        if not self._is_configured:
            logger.warning("Cloudinary credentials are incomplete")
            return False

        if cloudinary is None:
            logger.error("Cloudinary package not available")
            return False

        if self._configured_client:
            return True

        try:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=self.secure,
            )
            self._configured_client = True
            logger.info("Cloudinary client configured successfully")
            return True
        except Exception as config_error:  # pragma: no cover - defensive logging
            logger.error("Failed to configure Cloudinary client: %s", config_error)
            return False

    def is_available(self) -> bool:
        """Check if Cloudinary is ready for use."""
        return self._configure_client()

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder: str,
        content_type: str = 'application/octet-stream',
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload binary content to Cloudinary."""
        if not self._configure_client():
            return False, None, "Cloudinary not configured"

        upload_options = {
            'resource_type': 'auto',  # Allow any file type (images, PDFs, etc.)
            'public_id': os.path.splitext(filename)[0],
            'folder': folder,
            'overwrite': True,
        }

        if self.upload_preset:
            upload_options['upload_preset'] = self.upload_preset

        try:
            response = cloudinary.uploader.upload(  # type: ignore[attr-defined]
                file_content,
                **upload_options,
            )
            secure_url = response.get('secure_url') or response.get('url')
            if secure_url:
                logger.info("Cloudinary upload succeeded for %s", filename)
                return True, secure_url, None
            return False, None, "No URL returned by Cloudinary"
        except Exception as error:  # pragma: no cover - network call
            logger.error("Cloudinary upload failed for %s: %s", filename, error)
            return False, None, str(error)

    def delete_file(self, file_url: str) -> Tuple[bool, Optional[str]]:
        """Delete resource referenced by provided URL."""
        if not self._configure_client():
            return False, "Cloudinary not configured"

        public_id = self._extract_public_id(file_url)
        if not public_id:
            return False, "Could not determine Cloudinary public ID"

        try:
            response = cloudinary.uploader.destroy(  # type: ignore[attr-defined]
                public_id,
                invalidate=True,
                resource_type='auto',
            )
            result = response.get('result')
            if result in {'ok', 'not_found'}:
                logger.info("Cloudinary delete succeeded for %s", public_id)
                return True, None
            return False, f"Cloudinary delete returned: {result}"
        except Exception as error:  # pragma: no cover - network call
            logger.error("Cloudinary delete failed for %s: %s", public_id, error)
            return False, str(error)

    @staticmethod
    def _extract_public_id(file_url: str) -> Optional[str]:
        """Derive Cloudinary public ID from a full asset URL."""
        if not file_url:
            return None

        try:
            # Cloudinary URLs typically look like https://res.cloudinary.com/<cloud>/.../folder/public_id.ext
            parts = file_url.split('/upload/')
            if len(parts) < 2:
                return None

            path_segment = parts[1]
            public_id_with_ext = path_segment.split('?')[0]
            public_id = os.path.splitext(public_id_with_ext)[0]
            return public_id
        except Exception as error:  # pragma: no cover - defensive
            logger.error("Failed to extract public ID from %s: %s", file_url, error)
            return None


_cloudinary_service: Optional[CloudinaryService] = None


def get_cloudinary_service() -> Optional[CloudinaryService]:
    """Return a singleton CloudinaryService instance."""
    global _cloudinary_service
    if _cloudinary_service is None:
        _cloudinary_service = CloudinaryService()
    return _cloudinary_service if _cloudinary_service.is_available() else None


def is_cloudinary_available() -> bool:
    """Quick availability check for Cloudinary."""
    service = get_cloudinary_service()
    return service is not None
