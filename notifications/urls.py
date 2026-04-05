from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, 
    PushTokenViewSet,
    UserPushSubscriptionViewSet,
    get_vapid_public_key,
    send_test_notification,
    get_unread_count,
    subscribe_to_push,
    send_push_notification,
    debug_notifications,
    debug_all_notifications,
    health_check,
    send_broadcast_notification
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'push-tokens', PushTokenViewSet, basename='push-token')
router.register(r'push-subscriptions', UserPushSubscriptionViewSet, basename='push-subscription')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('vapid-public-key/', get_vapid_public_key, name='vapid-public-key'),
    path('send-test-notification/', send_test_notification, name='send-test-notification'),
    path('unread-count/', get_unread_count, name='unread-count'),
    path('subscribe-push/', subscribe_to_push, name='subscribe-push'),
    path('send-push/', send_push_notification, name='send-push'),
    path('broadcast/', send_broadcast_notification, name='send-broadcast'),
    path('debug/', debug_notifications, name='debug-notifications'),
    path('debug-all/', debug_all_notifications, name='debug-all-notifications'),
    path('health/', health_check, name='health-check'),
]