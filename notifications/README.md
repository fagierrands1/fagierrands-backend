# Fagi Errands Notification System

This module provides a comprehensive notification system for the Fagi Errands application, including:

- In-app notifications
- Web push notifications
- Mobile push notifications (via Firebase Cloud Messaging)

## Setup Instructions

### 1. Install Required Packages

```bash
pip install pywebpush py-vapid firebase-admin
```

### 2. Generate VAPID Keys

VAPID keys are required for Web Push notifications. Generate them using the provided management command:

```bash
python manage.py generate_vapid_keys
```

Add the generated keys to your `.env` file:

```
VAPID_PUBLIC_KEY=your_generated_public_key
VAPID_PRIVATE_KEY=your_generated_private_key
WEBPUSH_EMAIL=admin@fagierrands.com
```

### 3. Firebase Cloud Messaging (Optional)

For mobile push notifications, set up Firebase Cloud Messaging:

1. Create a Firebase project at https://console.firebase.google.com/
2. Add Android and/or iOS apps to your project
3. Get your FCM Server Key from Project Settings > Cloud Messaging
4. Add the FCM Server Key to your `.env` file:

```
FCM_SERVER_KEY=your_fcm_server_key
```

### 4. Celery Setup

Make sure Celery is properly configured to handle asynchronous notification sending:

1. Install Redis (used as the message broker)
2. Start the Celery worker:

```bash
celery -A fagierrandsbackup worker -l info
```

3. Start the Celery beat scheduler for periodic tasks:

```bash
celery -A fagierrandsbackup beat -l info
```

## Usage

### Creating Notifications

Use the `NotificationService` to create notifications:

```python
from notifications.services import NotificationService

# Create a notification
NotificationService.create_notification(
    recipient=user,
    notification_type='message',
    title='New Message',
    message='You have received a new message',
    content_object=message_object  # Optional related object
)
```

### Testing Notifications

You can test the notification system using the provided API endpoint:

```
POST /api/notifications/send-test-notification/
```

This will send a test notification to the authenticated user.

### Frontend Integration

1. Register for push notifications in your frontend app
2. Get the VAPID public key from the API endpoint:

```
GET /api/notifications/vapid-public-key/
```

3. Subscribe to push notifications and send the subscription to the server:

```
POST /api/notifications/push-tokens/
{
    "token": "subscription_json_string",
    "device_type": "web"
}
```

## Notification Types

The system supports the following notification types:

- `order_created`: When a new order is created
- `order_assigned`: When an order is assigned to an assistant
- `order_started`: When an order is marked as in progress
- `order_completed`: When an order is completed
- `order_cancelled`: When an order is cancelled
- `verification_approved`: When an assistant's verification is approved
- `verification_rejected`: When an assistant's verification is rejected
- `message`: General messages
- `review`: When a review is submitted

## Automatic Notifications

The system automatically creates notifications for the following events:

1. Order status changes
2. New orders
3. Reviews
4. Verification status changes

These are handled by Django signals in `notifications/signals.py`.