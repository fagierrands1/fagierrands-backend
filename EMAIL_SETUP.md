# OTP Email Setup Guide

## Problem
OTP emails are not being sent. This is usually due to:
1. Missing SMTP credentials in environment variables
2. Unverified sender email address in your email service
3. Incorrect email configuration

## Solution

### Step 1: Choose Your Email Service

#### Option A: Brevo (Recommended - Free tier available)
1. Sign up at https://www.brevo.com
2. Go to **SMTP & API** → **SMTP** section
3. Create an SMTP key (copy the password)
4. Verify your sender email address in **Senders** section

#### Option B: Gmail
1. Enable 2-factor authentication on your Gmail account
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Use your Gmail email and the generated app password

#### Option C: AWS SES
1. Set up AWS SES in your preferred region
2. Verify your sender email in SES console
3. Generate SMTP credentials

### Step 2: Set Environment Variables

Add these to your `.env` file:

```bash
# For Brevo
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-brevo-email@example.com
EMAIL_HOST_PASSWORD=your-brevo-smtp-key

# For Gmail
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_USE_SSL=False
# EMAIL_HOST_USER=your-gmail@gmail.com
# EMAIL_HOST_PASSWORD=your-gmail-app-password

# For AWS SES
# EMAIL_HOST=email-smtp.your-region.amazonaws.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_USE_SSL=False
# EMAIL_HOST_USER=your-aws-username
# EMAIL_HOST_PASSWORD=your-aws-password

# Sender email (must be verified in your email service)
DEFAULT_FROM_EMAIL=noreply@fagitone.com
```

### Step 3: Verify Your Sender Email

**Very important:** Your sender email address must be verified in your email service:

- **Brevo**: Go to Senders → Add a new sender and verify the email
- **Gmail**: The email must be verified in your Google account
- **AWS SES**: The email must be verified in the SES console

### Step 4: Test Email Configuration

Run this command to test if emails are working:

```python
# In Django shell
python manage.py shell

# Then run:
from accounts.test_email import test_email_configuration, send_test_email
test_email_configuration()
send_test_email('your-test-email@example.com')
```

### Step 5: Verify OTP Sending

1. Start your Django server
2. Call the OTP endpoint:
   ```
   POST /api/accounts/send-otp/
   {
     "email": "user@example.com"
   }
   ```
3. Check your logs for any errors:
   ```
   tail -f logs/django.log | grep -i "otp\|email"
   ```

## Common Issues & Solutions

### Issue: "Failed to send OTP email"
**Solution**: Check your email credentials in settings or environment variables

### Issue: "Email authentication failed"
**Solution**: Verify your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct

### Issue: "Sender email rejected"
**Solution**: Verify the sender email (DEFAULT_FROM_EMAIL) is verified in your email service

### Issue: "Connection timeout"
**Solution**: 
- Check firewall allows port 587 (SMTP)
- Use EMAIL_USE_TLS=True for secure connection
- Verify EMAIL_HOST is correct

## Email Configuration in Settings

The email configuration is in `fagierrandsbackup/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'support@fagitone.com')
```

## OTP Email Flow

1. User calls `/api/accounts/send-otp/` with their email
2. System creates an OTPVerification record with 6-digit code
3. Email is sent via configured SMTP service
4. User receives email with OTP code
5. User calls `/api/accounts/verify-otp/` with email and code
6. If code matches and hasn't expired, email is marked as verified

## Files Involved

- `accounts/otp_utils.py` - OTP email sending logic
- `accounts/views.py` - SendOTPView, VerifyOTPView endpoints
- `accounts/models.py` - OTPVerification model
- `fagierrandsbackup/settings.py` - Email configuration
- `templates/otp_verification.html` - Email template (HTML)
- `templates/otp_verification.txt` - Email template (Plain text)

## Testing

For development/debugging, you can use Django's console email backend to see emails in console instead of sending them:

```python
# In settings.py for DEBUG=True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This prints emails to console instead of actually sending them via SMTP.
