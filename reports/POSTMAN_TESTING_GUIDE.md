# 📮 Postman Testing Guide - Email Verification System

## 🚀 Setup Instructions

### 1. Start the Django Server
```bash
cd C:\Users\a\Documents\GitHub\fagierrands\fagierrands\fagierrandsbackup
python manage.py runserver
```

### 2. Base URL
Use this base URL for all requests:
```
http://localhost:8000
```

## 📋 Test Scenarios

### **Scenario 1: User Registration (Triggers Email Verification)**

**Method:** `POST`  
**URL:** `http://localhost:8000/api/accounts/register/`  
**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "username": "testuser123",
    "email": "your-email@example.com",
    "password": "testpass123",
    "password2": "testpass123",
    "first_name": "Test",
    "last_name": "User"
}
```

**Expected Response:**
```json
{
    "id": 1,
    "username": "testuser123",
    "email": "your-email@example.com",
    "first_name": "Test",
    "last_name": "User"
}
```

**What Happens:**
- User is created
- Verification email is automatically sent (check logs)
- User's `email_verified` field is `false`

---

### **Scenario 2: Check Email Verification Status**

**Method:** `GET`  
**URL:** `http://localhost:8000/api/accounts/check-email-verification/`  
**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**How to get ACCESS_TOKEN:**
First, login to get the token:

**Method:** `POST`  
**URL:** `http://localhost:8000/api/accounts/login/`  
**Body (JSON):**
```json
{
    "username": "testuser123",
    "password": "testpass123"
}
```

**Response will contain:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser123",
        "email": "your-email@example.com",
        "email_verified": false
    }
}
```

Copy the `access` token and use it in the Authorization header.

**Expected Response:**
```json
{
    "email_verified": false,
    "email": "your-email@example.com"
}
```

---

### **Scenario 3: Resend Verification Email**

**Method:** `POST`  
**URL:** `http://localhost:8000/api/accounts/resend-verification/`  
**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "email": "your-email@example.com"
}
```

**Expected Response (Success):**
```json
{
    "success": true,
    "message": "Verification email sent successfully."
}
```

**Expected Response (Already Verified):**
```json
{
    "success": false,
    "message": "Email is already verified."
}
```

**Expected Response (User Not Found):**
```json
{
    "success": false,
    "message": "No user found with this email address."
}
```

---

### **Scenario 4: Verify Email via Token (Browser Test)**

Since this endpoint returns HTML, you'll need to test it in a browser:

**Method:** `GET`  
**URL:** `http://localhost:8000/api/accounts/verify-email/{TOKEN}/`

**How to get the TOKEN:**
1. Check Django logs after registration/resend
2. Or check the database directly
3. Or use the Django shell (see below)

**Expected Response:**
- HTML page showing "Email Verified Successfully!" or error message
- User's `email_verified` field becomes `true`

---

## 🔍 Getting Verification Tokens for Testing

### Method 1: Django Shell
```bash
python manage.py shell
```

```python
from accounts.models import EmailVerification
from django.contrib.auth import get_user_model

User = get_user_model()

# Get user
user = User.objects.get(email='your-email@example.com')

# Get verification token
verification = EmailVerification.objects.filter(user=user, is_used=False).first()
if verification:
    print(f"Token: {verification.token}")
    print(f"Full URL: http://localhost:8000/api/accounts/verify-email/{verification.token}/")
else:
    print("No unused verification token found")
```

### Method 2: Django Admin
1. Go to `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Go to "Email verifications"
4. Find your user's verification token

### Method 3: Check Django Logs
Look for log messages like:
```
INFO: Verification email sent to your-email@example.com
```

---

## 📊 Postman Collection Setup

### Create a Postman Collection

1. **Create New Collection:** "Fagi Errands Email Verification"

2. **Add Environment Variables:**
   - `base_url`: `http://localhost:8000`
   - `access_token`: (will be set after login)
   - `test_email`: `your-email@example.com`
   - `test_username`: `testuser123`

3. **Add Requests:**

#### Request 1: Register User
- **Name:** "1. Register User"
- **Method:** POST
- **URL:** `{{base_url}}/api/accounts/register/`
- **Body:** Raw JSON
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

#### Request 2: Login User
- **Name:** "2. Login User"
- **Method:** POST
- **URL:** `{{base_url}}/api/accounts/login/`
- **Body:** Raw JSON
```json
{
    "username": "{{test_username}}",
    "password": "testpass123"
}
```
- **Tests Script:**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access);
}
```

#### Request 3: Check Email Verification
- **Name:** "3. Check Email Verification Status"
- **Method:** GET
- **URL:** `{{base_url}}/api/accounts/check-email-verification/`
- **Headers:** `Authorization: Bearer {{access_token}}`

#### Request 4: Resend Verification
- **Name:** "4. Resend Verification Email"
- **Method:** POST
- **URL:** `{{base_url}}/api/accounts/resend-verification/`
- **Body:** Raw JSON
```json
{
    "email": "{{test_email}}"
}
```

---

## 🧪 Complete Test Flow

### Step-by-Step Testing:

1. **Register User** → Should return 201 Created
2. **Login User** → Should return access token
3. **Check Email Status** → Should show `email_verified: false`
4. **Resend Verification** → Should return success message
5. **Get Token from Django Shell** → Copy the verification token
6. **Verify Email in Browser** → Go to verification URL
7. **Check Email Status Again** → Should show `email_verified: true`
8. **Try Resend Again** → Should return "already verified" message

---

## 🔧 Testing Without Real Email

If you don't want to configure real email settings, you can:

### 1. Use Console Email Backend
Add to `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

### 2. Use File Email Backend
Add to `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = 'C:/temp/emails'  # Create this directory
```

This will save emails as files.

---

## 📝 Sample Postman Tests

Add these to your Postman request tests:

### For Registration:
```javascript
pm.test("User registered successfully", function () {
    pm.response.to.have.status(201);
    const response = pm.response.json();
    pm.expect(response).to.have.property('username');
    pm.expect(response).to.have.property('email');
});
```

### For Login:
```javascript
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response).to.have.property('access');
    pm.environment.set("access_token", response.access);
});
```

### For Email Verification Check:
```javascript
pm.test("Email verification status retrieved", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response).to.have.property('email_verified');
    pm.expect(response).to.have.property('email');
});
```

### For Resend Verification:
```javascript
pm.test("Resend verification response", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response).to.have.property('success');
    pm.expect(response).to.have.property('message');
});
```

---

## 🚨 Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution:** Make sure you're using the correct access token in the Authorization header.

### Issue: 400 Bad Request on Registration
**Solution:** Check that all required fields are provided and passwords match.

### Issue: Email not sending
**Solution:** Check Django console for email output or configure real email settings.

### Issue: Token not found
**Solution:** Make sure the user was created and verification token exists in the database.

---

## 🎯 Quick Test Commands

### Create Test User via Django Shell:
```python
from django.contrib.auth import get_user_model
from accounts.models import EmailVerification

User = get_user_model()
user = User.objects.create_user(
    username='postmantest',
    email='test@example.com',
    password='testpass123'
)

# Create verification token
verification = EmailVerification.objects.create(user=user)
print(f"Verification URL: http://localhost:8000/api/accounts/verify-email/{verification.token}/")
```

This gives you a complete testing setup for the email verification system in Postman! 🚀