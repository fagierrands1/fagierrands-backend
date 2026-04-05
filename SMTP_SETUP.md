# 📧 Free SMTP Setup Guide - Brevo (300 emails/day free)

## 🚀 Quick Setup with Brevo SMTP

### **Step 1: Create Brevo Account**
1. Go to: https://www.brevo.com/
2. Click "Sign up for free"
3. Create account with your email
4. Verify your email address

### **Step 2: Get SMTP Credentials**
1. **Login to Brevo Dashboard**
2. **Go to**: "SMTP & API" → "SMTP" (in left sidebar)
3. **Click**: "Create SMTP Key"
4. **Name**: "Fagi Errands Email Verification"
5. **Copy the SMTP Key** (it looks like: `xsmtpsib-abcd1234...`)

### **Step 3: Configure Django Settings**

#### **Option A: Environment Variables (Recommended)**
Add these to your `.env` file or system environment:

```bash
# SMTP Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-brevo-login-email@example.com
EMAIL_HOST_PASSWORD=xsmtpsib-your-smtp-key-here
DEFAULT_FROM_EMAIL=noreply@fagierrands.com
```

#### **Option B: Direct Settings (For Testing)**
Update `fagierrandsbackup/settings.py`:

```python
# Replace the email settings section with:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-brevo-login-email@example.com'  # Your Brevo account email
EMAIL_HOST_PASSWORD = 'xsmtpsib-your-smtp-key-here'      # Your SMTP key from Step 2
DEFAULT_FROM_EMAIL = 'noreply@fagierrands.com'
```

### **Step 4: Test the Setup**

#### **Start Django Server:**
```bash
cd c:\Users\a\Documents\GitHub\fagierrands\fagierrands\fagierrandsbackup
python manage.py runserver 8006
```

#### **Start React Frontend:**
```bash
cd c:\Users\a\Documents\GitHub\fagierrands\fagierrands\fagi-errands
npm start
```

#### **Test Email Verification:**
1. **Go to**: http://localhost:3000/test-otp
2. **Enter ANY email**: (Gmail, Outlook, Yahoo, etc.)
3. **Click**: "Send Verification Email"
4. **Check your inbox**: Look for "Email Verification - Fagi Errands"
5. **Copy the 6-digit code** from the email
6. **Paste and verify** in the app

---

## 🔧 Alternative Free SMTP Services

### **Option 1: Gmail SMTP (Free)**
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Generate from Google Account settings
```

**Setup:**
1. Enable 2-factor authentication on Gmail
2. Generate App Password: Google Account → Security → App passwords
3. Use the 16-character app password

### **Option 2: Outlook/Hotmail SMTP (Free)**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-outlook@outlook.com'
EMAIL_HOST_PASSWORD = 'your-outlook-password'
```

### **Option 3: SendGrid (100 emails/day free)**
```python
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = 'your-sendgrid-api-key'
```

---

## 🧪 Testing Commands

### **Test SMTP in Django Shell:**
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test basic email
send_mail(
    'Test Email',
    'This is a test email from Django.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-test-email@gmail.com'],
    fail_silently=False,
)
print("Email sent successfully!")
```

### **Test OTP Endpoint Directly:**
```bash
# Send OTP
curl -X POST http://localhost:8006/api/accounts/smtp/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test-email@gmail.com"}'

# Verify OTP (replace 123456 with actual code from email)
curl -X POST http://localhost:8006/api/accounts/smtp/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test-email@gmail.com", "token": "123456"}'
```

---

## 📊 Brevo Free Tier Limits

- **300 emails per day** (Free tier)
- **No credit card required** for free tier
- **All email domains supported** (Gmail, Outlook, Yahoo, etc.)
- **Professional email templates**
- **Delivery tracking and analytics**

---

## 🐛 Troubleshooting

### **Issue: Authentication failed**
**Solution:** 
- Double-check SMTP key is correct
- Make sure EMAIL_HOST_USER is your Brevo login email
- Verify EMAIL_HOST_PASSWORD is the SMTP key (starts with `xsmtpsib-`)

### **Issue: Connection timeout**
**Solution:**
- Check firewall settings
- Try port 25 or 465 instead of 587
- Ensure EMAIL_USE_TLS = True

### **Issue: Email not received**
**Solution:**
- Check spam folder
- Verify recipient email is correct
- Check Brevo dashboard for delivery status

### **Issue: Domain restrictions still apply**
**Solution:**
- Make sure you're using `/smtp/send-otp/` endpoint (not `/supabase/resend-verification/`)
- Check Django logs for actual error messages

---

## ✅ Success Indicators

When working correctly, you should see:

### **Django Console:**
```
INFO: SMTP verification email sent to user@example.com with OTP: 123456
```

### **Frontend Response:**
```
✅ Verification email sent via SMTP! Check your inbox for the 6-digit OTP code. 📧
```

### **Email Received:**
A beautifully formatted email with a large 6-digit code in a bordered box.

---

## 🚀 Ready to Test!

After following this guide:
1. **Any email domain** will work (Gmail, Outlook, Yahoo, etc.)
2. **No Supabase domain restrictions**
3. **Professional email templates**
4. **Free 300 emails per day**

**Test URL:** http://localhost:3000/test-otp

Your email verification system is now free from domain restrictions! 🎉