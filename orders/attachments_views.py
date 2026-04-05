import os
import uuid
from typing import List

from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .models import Order, OrderAttachment
from accounts.cloudinary_service import get_cloudinary_service

ALLOWED_CONTENT_TYPES: List[str] = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 
    'image/heic', 'image/heif', 'application/pdf', 'application/octet-stream',
    'image'  # Common camera type
]
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def user_can_upload_to_order(user, order: Order) -> bool:
    # Client who owns it or the assigned assistant
    if user.is_anonymous:
        return False
    if getattr(user, 'user_type', 'user') == 'admin':
        return True
    if getattr(user, 'user_type', 'user') == 'handler':
        return True
    if order.client_id == user.id:
        return True
    if order.assistant_id and order.assistant_id == user.id:
        return True
    return False


def user_can_view_order(user, order: Order) -> bool:
    # Client, assigned assistant, handlers, admins
    if user.is_anonymous:
        return False
    if getattr(user, 'user_type', 'user') in ['admin', 'handler']:
        return True
    if order.client_id == user.id:
        return True
    if order.assistant_id and order.assistant_id == user.id:
        return True
    return False


class AttachmentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id: int):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Attachment upload request for order {order_id}")
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request FILES: {request.FILES}")
        logger.info(f"Request POST: {request.POST}")
        logger.info(f"Content-Type: {request.content_type}")
        
        service = get_cloudinary_service()
        if not service:
            logger.error("Cloudinary service not available")
            return Response({
                'error': 'Storage not configured. Set Cloudinary credentials.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order = get_object_or_404(Order, pk=order_id)
        logger.info(f"Order found: {order}")
        
        if not user_can_upload_to_order(request.user, order):
            logger.warning(f"User {request.user} not allowed to upload to order {order_id}")
            return Response({'error': 'Not allowed to upload for this order'}, status=status.HTTP_403_FORBIDDEN)

        upload = request.FILES.get('file')
        if not upload:
            logger.error(f"No file in request. Available files: {list(request.FILES.keys())}")
            return Response({'error': 'No file provided (form field name should be "file")'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = upload.content_type or 'application/octet-stream'
        logger.info(f"Original content type: {content_type}")
        
        # Fix common camera type issues
        if content_type == 'image':
            content_type = 'image/jpeg'
            logger.info(f"Converted 'image' type to 'image/jpeg'")
        
        # Be more flexible with content types from mobile devices
        if content_type not in ALLOWED_CONTENT_TYPES:
            # Check if it's likely an image based on file name
            file_name = upload.name.lower() if upload.name else ''
            logger.info(f"File name: {file_name}")
            
            if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif']):
                # Override content type for image files
                if file_name.endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                elif file_name.endswith('.png'):
                    content_type = 'image/png'
                elif file_name.endswith('.gif'):
                    content_type = 'image/gif'
                elif file_name.endswith('.webp'):
                    content_type = 'image/webp'
                elif file_name.endswith(('.heic', '.heif')):
                    content_type = 'image/heic'
                logger.info(f"Overrode content type to: {content_type} based on file extension")
            else:
                logger.error(f"Content type {content_type} not allowed and no valid image extension found")
                return Response({'error': f'Invalid file type: {content_type}'}, status=status.HTTP_400_BAD_REQUEST)

        size = upload.size
        if size > MAX_FILE_SIZE_BYTES:
            return Response({'error': 'File too large (max 5MB)'}, status=status.HTTP_400_BAD_REQUEST)

        # Build path: orders/{order_id}/{uuid}_{safe_name}
        safe_name = os.path.basename(upload.name).replace('..', '')
        file_id = uuid.uuid4().hex
        path = f"orders/{order_id}/{file_id}_{safe_name}"

        try:
            logger.info(f"Reading file data, size: {size}")
            data = upload.read()
            logger.info(f"File data read successfully, uploading to path: {path}")
            
            # Upload to Cloudinary
            upload_folder = f"orders/{order_id}"
            success, url, error = service.upload_file(
                file_content=data,
                filename=f"{file_id}_{safe_name}",
                folder=upload_folder,
                content_type=content_type,
            )
            if not success:
                logger.error(f"Cloudinary upload failed: {error}")
                return Response({'error': f'Upload failed: {error}'}, status=status.HTTP_502_BAD_GATEWAY)
            logger.info(f"Cloudinary upload succeeded: {url}")
        except Exception as e:
            logger.error(f"Upload to Cloudinary failed: {e}")
            return Response({'error': f'Upload failed: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        # Save metadata
        logger.info(f"Creating attachment record in database")
        # Save metadata. Store the Cloudinary secure URL in file_path.
        att = OrderAttachment.objects.create(
            order=order,
            uploaded_by=request.user,
            file_path=url,
            file_name=safe_name,
            content_type=content_type,
            file_size=size,
        )
        logger.info(f"Attachment created with ID: {att.id}")

        # Return a signed URL for immediate access (1 hour)
        # Cloudinary returns a secure URL which we can return directly
        signed_url = att.file_path

        response_data = {
            'id': att.id,
            'file_name': att.file_name,
            'content_type': att.content_type,
            'file_size': att.file_size,
            'signed_url': signed_url,
        }
        logger.info(f"Returning successful response: {response_data}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class AttachmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id: int):
        service = get_cloudinary_service()
        if not service:
            return Response({
                'error': 'Storage not configured. Set Cloudinary credentials.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order = get_object_or_404(Order, pk=order_id)
        if not user_can_view_order(request.user, order):
            return Response({'error': 'Not allowed to view attachments for this order'}, status=status.HTTP_403_FORBIDDEN)

        items = []
        for att in order.attachments.all().order_by('-uploaded_at'):
            # file_path stores Cloudinary secure URL
            signed_url = att.file_path
            items.append({
                'id': att.id,
                'file_name': att.file_name,
                'content_type': att.content_type,
                'file_size': att.file_size,
                'uploaded_at': att.uploaded_at,
                'signed_url': signed_url,
            })

        return Response({'results': items})


class AttachmentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id: int, pk: int):
        service = get_cloudinary_service()
        if not service:
            return Response({
                'error': 'Storage not configured. Set Cloudinary credentials.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order = get_object_or_404(Order, pk=order_id)
        if not user_can_view_order(request.user, order):
            return Response({'error': 'Not allowed to view this attachment'}, status=status.HTTP_403_FORBIDDEN)

        att = get_object_or_404(OrderAttachment, pk=pk, order=order)

        # Cloudinary stores full URL in file_path
        signed_url = att.file_path

        data = {
            'id': att.id,
            'file_name': att.file_name,
            'content_type': att.content_type,
            'file_size': att.file_size,
            'uploaded_at': att.uploaded_at,
            'uploaded_by': att.uploaded_by.id if att.uploaded_by else None,
            'signed_url': signed_url,
        }

        return Response(data)
