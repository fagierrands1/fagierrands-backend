# 🚀 Postman Quick Reference - Email Verification

## 📋 Quick Setup Checklist

- [ ] Start Django server: `python manage.py runserver`
- [ ] Import Postman collection: `Fagi_Errands_Email_Verification.postman_collection.json`
- [ ] Set environment variables in Postman
- [ ] Run setup script: `python setup_postman_testing.py`

## 🔧 Environment Variables

Set these in Postman Environment:

| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:8000` |
| `test_email` | `postman@test.com` |
| `test_username` | `postmantest` |
| `access_token` | *(auto-set after login)* |
| `verification_token` | *(get from setup script)* |

## 📝 Test Sequence

### 1️⃣ Register User
```
POST {{base_url}}/api/accounts/register/
```
**Body:**
```json
{
    "username": "{{test_username}}",
    "email": "{{test_email}}",
    "password": "testpass123",
    "password2": "testpass123",
    "first_name": "Test",
    "last_name": "User"
}
```
**Expected:** `201 Created` + User data

### 2️⃣ Login User
```
POST {{base_url}}/api/accounts/login/
```
**Body:**
```json
{
    "username": "{{test_username}}",
    "password": "testpass123"
}
```
**Expected:** `200 OK` + Access token (auto-saved)

### 3️⃣ Check Email Status (Before Verification)
```
GET {{base_url}}/api/accounts/check-email-verification/
Authorization: Bearer {{access_token}}
```
**Expected:** `200 OK` + `"email_verified": false`

### 4️⃣ Resend Verification Email (Django)
```
POST {{base_url}}/api/accounts/resend-verification/
```
**Body:**
```json
{
    "email": "{{test_email}}"
}
```
**Expected:** `200 OK` + Success message

### 4️⃣b Resend Verification Email (Supabase - Recommended)
```
POST {{base_url}}/api/accounts/supabase/resend-verification/
```
**Body:**
```json
{
    "email": "{{test_email}}"
}
```
**Expected:** `200 OK` + Success message
**Note:** This actually sends real emails via Supabase

### 5️⃣ Verify Email (Browser)
```
GET {{base_url}}/api/accounts/verify-email/{{verification_token}}/
```
**Test in browser** - Should show success page

### 6️⃣ Check Email Status (After Verification)
```
GET {{base_url}}/api/accounts/check-email-verification/
Authorization: Bearer {{access_token}}
```
**Expected:** `200 OK` + `"email_verified": true`

## 🎯 Quick Test Commands

### Get Verification Token
```bash
python manage.py shell -c "
from accounts.models import EmailVerification
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='postmantest')
token = EmailVerification.objects.filter(user=user, is_used=False).first()
print(f'Token: {token.token if token else \"None\"}')
"
```

### Create New Test User
```bash
python setup_postman_testing.py
```

### Check User Status
```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='postmantest')
print(f'Email verified: {user.email_verified}')
"
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check access_token is set correctly |
| User already exists | Delete user or use different username |
| Token not found | Run setup script to create new token |
| Email not sending | Check Django console for email output |

## 📊 Expected Response Codes

| Endpoint | Success Code | Error Codes |
|----------|--------------|-------------|
| Register | 201 | 400 (validation) |
| Login | 200 | 400 (invalid credentials) |
| Check Status | 200 | 401 (not authenticated) |
| Resend Email | 200 | 400 (already verified/not found) |
| Verify Token | 200 (HTML) | 200 (HTML error page) |

## 🎨 Postman Tests

Add these to your requests:

### Registration Test
```javascript
pm.test("User registered", function () {
    pm.response.to.have.status(201);
    pm.expect(pm.response.json()).to.have.property('username');
});
```

### Login Test
```javascript
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.environment.set("access_token", response.access);
});
```

### Status Check Test
```javascript
pm.test("Status retrieved", function () {
    pm.response.to.have.status(200);
    pm.expect(pm.response.json()).to.have.property('email_verified');
});
```

## 🚀 One-Click Testing

1. **Import Collection** → `Fagi_Errands_Email_Verification.postman_collection.json`
2. **Set Environment** → Use variables from setup script
3. **Run Collection** → Click "Run" to test all endpoints
4. **Verify in Browser** → Use the verification URL

## 📞 Support

- Check Django logs for detailed error messages
- Use Django admin at `/admin/` to inspect data
- Run `python demo_email_verification.py` for system test