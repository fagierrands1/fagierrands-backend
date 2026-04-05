# Email Verification System

This document describes the email verification system implemented for the Fagi Errands Django backend.

## Overview

The email verification system ensures that users verify their email addresses after registration. This helps maintain data quality and enables secure communication with users.

## Features

- ✅ Automatic email verification on user registration
- ✅ Resend verification email functionality
- ✅ Token-based verification with expiration (24 hours)
- ✅ Beautiful HTML email templates
- ✅ Success/error pages for verification results
- ✅ Admin interface for managing verifications
- ✅ Management command for testing

## API Endpoints

### 1. Email Verification (GET)
```
GET /api/accounts/verify-email/{token}/
```
- **Purpose**: Verify user's email using the token from the email
- **Authentication**: None required
- **Response**: HTML page showing success/failure

### 2. Resend Verification Email (POST)
```
POST /api/accounts/resend-verification/
```
- **Purpose**: Resend verification email to user
- **Authentication**: None required
- **Body**:
```json
{
    "email": "user@example.com"
}
```
- **Response**:
```json
{
    "success": true,
    "message": "Verification email sent successfully."
}
```

### 3. Check Email Verification Status (GET)
```
GET /api/accounts/check-email-verification/
```
- **Purpose**: Check if current user's email is verified
- **Authentication**: Required (Bearer token)
- **Response**:
```json
{
    "email_verified": true,
    "email": "user@example.com"
}
```

## Models

### EmailVerification
- `user`: ForeignKey to User model
- `token`: UUID field (unique verification token)
- `created_at`: DateTime when token was created
- `expires_at`: DateTime when token expires (24 hours from creation)
- `is_used`: Boolean indicating if token has been used

## Email Templates

### HTML Template (`email_verification.html`)
- Professional design with Fagi Errands branding
- Clear call-to-action button
- Fallback text link
- Expiration warning
- Mobile-responsive

### Text Template (`email_verification.txt`)
- Plain text version for email clients that don't support HTML
- Contains all essential information

### Success/Error Page (`email_verified_success.html`)
- Shows verification result to user
- Provides link back to the application
- Handles both success and error cases

## Configuration

### Environment Variables
```bash
# Email settings (already configured)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@fagierrands.com

# Frontend URL for redirect links
FRONTEND_URL=https://fagierrands-x9ow.vercel.app
```

### Django Settings
The following settings are automatically configured:
- `EMAIL_BACKEND`: SMTP backend
- `DEFAULT_FROM_EMAIL`: Sender email address
- `FRONTEND_URL`: Frontend application URL

## Usage Examples

### 1. User Registration Flow
```python
# When user registers, verification email is automatically sent
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='password123'
)
# Email verification is sent automatically via RegisterView.perform_create()
```

### 2. Manual Email Sending
```python
from accounts.email_utils import send_verification_email

user = User.objects.get(email='test@example.com')
success = send_verification_email(user, request)
if success:
    print("Email sent successfully")
```

### 3. Verify Email Token
```python
from accounts.email_utils import verify_email_token

success, message, user = verify_email_token(token_uuid)
if success:
    print(f"Email verified for {user.email}")
```

## Testing

### Management Command
Test the email verification system:
```bash
python manage.py test_email_verification --email user@example.com
```

### Manual Testing
1. Register a new user via API
2. Check your email for verification message
3. Click the verification link
4. Verify the success page appears
5. Check that `user.email_verified` is now `True`

## Admin Interface

Access the Django admin to manage email verifications:
- View all verification tokens
- See expiration status
- Filter by used/unused tokens
- Search by user email or username

## Security Features

1. **Token Expiration**: Tokens expire after 24 hours
2. **Single Use**: Tokens can only be used once
3. **UUID Tokens**: Cryptographically secure random tokens
4. **No Sensitive Data**: Tokens don't contain user information

## Error Handling

The system gracefully handles:
- Expired tokens
- Already used tokens
- Invalid tokens
- Email sending failures
- Network issues

## Integration with Frontend

### React/JavaScript Example
```javascript
// Check email verification status
const checkEmailVerification = async () => {
    const response = await fetch('/api/accounts/check-email-verification/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    const data = await response.json();
    return data.email_verified;
};

// Resend verification email
const resendVerification = async (email) => {
    const response = await fetch('/api/accounts/resend-verification/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
    });
    return await response.json();
};
```

## Troubleshooting

### Common Issues

1. **Emails not sending**
   - Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
   - Verify SMTP settings
   - Check spam folder

2. **Verification links not working**
   - Ensure FRONTEND_URL is correctly set
   - Check URL patterns in urls.py
   - Verify token hasn't expired

3. **Template not found errors**
   - Ensure templates are in the correct directory
   - Check TEMPLATES setting in Django settings

### Logs
Check Django logs for email verification issues:
```bash
# Look for these log messages
INFO: Verification email sent to user@example.com
ERROR: Failed to send verification email to user@example.com: [error details]
INFO: Email verified successfully for user user@example.com
```

## Future Enhancements

Potential improvements:
- Email verification reminders
- Custom expiration times
- Email verification required middleware
- Bulk verification management
- Email verification analytics

## Files Created/Modified

### New Files
- `accounts/models.py` - Added EmailVerification model
- `accounts/email_utils.py` - Email utility functions
- `accounts/serializers.py` - Added verification serializers
- `accounts/management/commands/test_email_verification.py` - Test command
- `templates/email_verification.html` - HTML email template
- `templates/email_verification.txt` - Text email template
- `templates/email_verified_success.html` - Success/error page

### Modified Files
- `accounts/views.py` - Added verification views and updated RegisterView
- `accounts/urls.py` - Added verification URL patterns
- `accounts/admin.py` - Added EmailVerification admin
- `fagierrandsbackup/settings.py` - Added FRONTEND_URL setting

## Support

For issues or questions about the email verification system, check:
1. Django logs for error messages
2. Email provider settings
3. Network connectivity
4. Token expiration status in admin panel