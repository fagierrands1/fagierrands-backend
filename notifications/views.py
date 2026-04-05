from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import json
import logging
from .models import Notification, PushToken, UserPushSubscription
from .serializers import NotificationSerializer, PushTokenSerializer, UserPushSubscriptionSerializer
from .utils import get_vapid_key, send_web_push_notification

logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return notifications for the currently authenticated user.
        """
        try:
            # Check if user is authenticated
            if not self.request.user.is_authenticated:
                return Notification.objects.none()
            
            return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_queryset: {e}")
            # Return empty queryset if there's an error
            return Notification.objects.none()
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to handle errors gracefully
        """
        try:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return Response({
                    'results': [],
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Try to get notifications with additional error handling
            try:
                queryset = self.get_queryset()
                
                # Check if queryset is valid
                if queryset is None:
                    raise ValueError("Queryset is None")
                
                page = self.paginate_queryset(queryset)
                
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                
                serializer = self.get_serializer(queryset, many=True)
                return Response({
                    'results': serializer.data,
                    'count': len(serializer.data)
                })
                
            except Exception as db_error:
                # Database-specific error handling
                logger.error(f"Database error in notifications list: {db_error}")
                return Response({
                    'results': [],
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'error': 'Database temporarily unavailable'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"General error in notifications list: {e}")
            
            # Return empty result set if there's an error
            return Response({
                'results': [],
                'count': 0,
                'next': None,
                'previous': None,
                'error': 'Service temporarily unavailable'
            }, status=status.HTTP_200_OK)  # Return 200 with empty data instead of 500

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications as read for the current user.
        """
        self.get_queryset().update(read=True)
        return Response({'status': 'All notifications marked as read'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a specific notification as read.
        """
        notification = get_object_or_404(self.get_queryset(), pk=pk)
        notification.read = True
        notification.save()
        return Response({'status': 'Notification marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread notifications for the current user.
        """
        count = self.get_queryset().filter(read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)


class PushTokenViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing push notification tokens.
    """
    serializer_class = PushTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return push tokens for the currently authenticated user.
        """
        return PushToken.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a specific push token.
        """
        token = self.get_object()
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def delete_token(self, request):
        """
        Delete a push token by providing the token value.
        """
        token_value = request.data.get('token')
        if not token_value:
            return Response({'error': 'Token value is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = PushToken.objects.get(user=request.user, token=token_value)
            token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PushToken.DoesNotExist:
            return Response({'error': 'Token not found'}, status=status.HTTP_404_NOT_FOUND)


class UserPushSubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Web Push subscriptions with VAPID support.
    """
    serializer_class = UserPushSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return push subscriptions for the currently authenticated user.
        """
        return UserPushSubscription.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create or update a push subscription for the current user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Push subscription saved successfully',
            'subscription_id': subscription.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def send_test_push(self, request):
        """
        Send a test push notification to the user's subscription.
        """
        try:
            subscription = UserPushSubscription.objects.get(
                user=request.user, 
                is_active=True
            )
            
            title = request.data.get('title', 'Test Notification')
            message = request.data.get('message', 'This is a test push notification!')
            
            success = send_web_push_notification(
                subscription_info=subscription.subscription_data,
                title=title,
                message=message,
                data={
                    'action_link': '/',
                    'tag': 'test-notification'
                }
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Test push notification sent successfully'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send push notification'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except UserPushSubscription.DoesNotExist:
            return Response({
                'error': 'No active push subscription found'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_vapid_public_key(request):
    """
    Get the VAPID public key for Web Push notifications
    """
    try:
        # Get or generate VAPID keys
        vapid_keys = get_vapid_key()
        
        if not vapid_keys['public_key']:
            return Response({
                'error': 'VAPID keys not configured',
                'public_key': '',
                'message': 'Push notifications not available'
            }, status=status.HTTP_200_OK)  # Return 200 instead of 500
        
        return Response({
            'public_key': vapid_keys['public_key'],
            'message': 'VAPID key retrieved successfully'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting VAPID public key: {e}")
        
        return Response({
            'error': str(e),
            'public_key': '',
            'message': 'Error retrieving VAPID key'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_test_notification(request):
    """
    Send a test notification to the current user
    """
    # Use synchronous version to avoid Redis dependency
    from .services_sync import NotificationServiceSync as NotificationService
    
    # Create a test notification
    notification = NotificationService.create_notification(
        recipient=request.user,
        notification_type='message',
        title='Test Notification',
        message='This is a test notification from the Fagi Errands system.'
    )
    
    return Response({'status': 'Test notification sent', 'notification_id': notification.id})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_count(request):
    """
    Get unread notification count - simple endpoint for frontend compatibility
    """
    try:
        count = Notification.objects.filter(recipient=request.user, read=False).count()
        return Response({'count': count, 'unread_count': count})
    except Exception as e:
        # Return 0 if there's any error
        return Response({'count': 0, 'unread_count': 0, 'error': str(e)})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def subscribe_to_push(request):
    """
    Subscribe user to push notifications - endpoint for frontend compatibility
    """
    try:
        subscription_data = request.data.get('subscription')
        user_agent = request.data.get('user_agent', '')
        
        if not subscription_data:
            return Response({
                'error': 'Subscription data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update subscription
        subscription, created = UserPushSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'subscription_data': subscription_data,
                'user_agent': user_agent,
                'is_active': True
            }
        )
        
        return Response({
            'success': True,
            'message': 'Subscription saved successfully',
            'created': created
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_push_notification(request):
    """
    Send push notification to user - endpoint for testing and manual sends
    """
    try:
        user_id = request.data.get('user_id', request.user.id)
        title = request.data.get('title', 'Fagi Errands')
        message = request.data.get('message', 'You have a new notification')
        action_link = request.data.get('action_link', '/')
        
        # Get user's push subscription
        subscription = UserPushSubscription.objects.get(
            user_id=user_id,
            is_active=True
        )
        
        # Send push notification
        success = send_web_push_notification(
            subscription_info=subscription.subscription_data,
            title=title,
            message=message,
            data={
                'action_link': action_link,
                'tag': request.data.get('tag', 'fagi-notification')
            }
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Push notification sent successfully'
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to send push notification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except UserPushSubscription.DoesNotExist:
        return Response({
            'error': 'No push subscription found for user'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def debug_notifications(request):
    """
    Debug endpoint to check notification system status
    """
    try:
        user = request.user
        
        # Get detailed notification information
        try:
            # Count notifications for current user
            user_notifications = Notification.objects.filter(recipient=user).count()
            user_unread = Notification.objects.filter(recipient=user, read=False).count()
            
            # Count ALL notifications in database
            total_notifications = Notification.objects.all().count()
            
            # Get sample notifications for current user
            user_sample = list(Notification.objects.filter(recipient=user)[:3].values(
                'id', 'title', 'message', 'notification_type', 'read', 'created_at'
            ))
            
            # Get sample of ALL notifications (to see what users they belong to)
            all_sample = list(Notification.objects.all()[:5].values(
                'id', 'title', 'recipient_id', 'recipient__username', 'created_at'
            ))
            
            db_status = 'connected'
        except Exception as db_error:
            user_notifications = 0
            user_unread = 0
            total_notifications = 0
            user_sample = []
            all_sample = []
            db_status = f'error: {str(db_error)}'
        
        # Check VAPID configuration
        vapid_keys = get_vapid_key()
        vapid_configured = bool(vapid_keys['public_key'])
        
        return Response({
            'success': True,
            'current_user': {
                'id': user.id,
                'username': user.username,
                'email': getattr(user, 'email', 'No email'),
                'is_authenticated': user.is_authenticated
            },
            'notifications': {
                'user_notifications': user_notifications,
                'user_unread': user_unread,
                'total_in_database': total_notifications,
                'user_sample': user_sample,
                'all_notifications_sample': all_sample
            },
            'system': {
                'vapid_configured': vapid_configured,
                'database_status': db_status
            },
            'message': 'Detailed notification debug info'
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in debug_notifications: {e}")
        
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Error in notification system',
            'user_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False
        }, status=status.HTTP_200_OK)  # Return 200 instead of 500


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def debug_all_notifications(request):
    """
    Debug endpoint to show ALL notifications (temporary for debugging)
    """
    try:
        # Get ALL notifications with user info
        all_notifications = Notification.objects.select_related('recipient').all()[:10]
        
        notifications_data = []
        for notif in all_notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message[:100],
                'recipient_id': notif.recipient.id,
                'recipient_username': notif.recipient.username,
                'notification_type': notif.notification_type,
                'read': notif.read,
                'created_at': notif.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'current_user_id': request.user.id,
            'current_username': request.user.username,
            'total_notifications': Notification.objects.count(),
            'notifications': notifications_data,
            'message': 'All notifications debug info'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Error getting all notifications'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([])  # No authentication required for health check
def health_check(request):
    """
    Simple health check endpoint that doesn't require database access
    """
    try:
        return Response({
            'status': 'healthy',
            'service': 'notifications',
            'message': 'Notification service is running',
            'timestamp': str(timezone.now()),
            'cors_origin': request.META.get('HTTP_ORIGIN', 'No origin header'),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'No user agent')[:100]
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'service': 'notifications',
            'error': str(e),
            'message': 'Health check failed'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def send_broadcast_notification(request):
    """
    Send a broadcast notification to users
    Admin only endpoint
    """
    from .broadcast_service import BroadcastService
    
    try:
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'announcement')
        target_audience = request.data.get('target_audience', 'all')
        action_url = request.data.get('action_url')
        image_url = request.data.get('image_url')
        send_immediately = request.data.get('send_immediately', True)
        
        if not title or not message:
            return Response({
                'success': False,
                'error': 'Title and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = BroadcastService.create_and_send_broadcast(
            title=title,
            message=message,
            notification_type=notification_type,
            target_audience=target_audience,
            created_by=request.user,
            action_url=action_url,
            image_url=image_url,
            send_immediately=send_immediately
        )
        
        if result['success']:
            return Response({
                'success': True,
                'broadcast_id': result['broadcast_id'],
                'message': 'Broadcast notification sent successfully',
                'details': result.get('send_result', {})
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error sending broadcast notification: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)