# RENDER ENVIRONMENT VARIABLES - CRITICAL CHECKLIST

## ✅ MUST HAVE (or Swagger will fail)

### 1. **SECRET_KEY**
```
Already set in render_env ✓
```

### 2. **DEBUG**
```
Set to: False ✓
```

### 3. **ALLOWED_HOSTS**
```
CURRENT: localhost,127.0.0.1
MUST ADD: fagierrands-backend-xwqi.onrender.com,fagierrands-backend.onrender.com
```
**⚠️ ACTION REQUIRED:** Update in Render Dashboard:
```
ALLOWED_HOSTS=fagierrands-backend-xwqi.onrender.com,fagierrands-backend.onrender.com,localhost,127.0.0.1
```

### 4. **DATABASE_URL**
```
Auto-set by Render when you add PostgreSQL ✓
```

### 5. **BASE_URL**
```
CURRENT: http://localhost:8000
MUST BE: https://fagierrands-backend-xwqi.onrender.com
```
**⚠️ ACTION REQUIRED:** Update in Render Dashboard:
```
BASE_URL=https://fagierrands-backend-xwqi.onrender.com
```

---

## 🔍 VERIFY IN RENDER DASHBOARD

Go to: **Your Service → Environment → Environment Variables**

### Critical Variables to Check:

| Variable | Value | Status |
|----------|-------|--------|
| SECRET_KEY | (long random string) | ✓ Should exist |
| DEBUG | False | ✓ Should be False |
| ALLOWED_HOSTS | fagierrands-backend-xwqi.onrender.com,... | ⚠️ UPDATE |
| DATABASE_URL | postgres://... | ✓ Auto-set |
| BASE_URL | https://fagierrands-backend-xwqi.onrender.com | ⚠️ UPDATE |

---

## 🚨 COMMON ERRORS & FIXES

### Error: "400 Bad Request"
**Cause:** Domain not in ALLOWED_HOSTS
**Fix:** Add your Render domain to ALLOWED_HOSTS

### Error: "500 Internal Server Error" 
**Cause:** Missing DATABASE_URL or serializer issues (now fixed)
**Fix:** Ensure PostgreSQL is attached to your service

### Error: "DisallowedHost at /"
**Cause:** ALLOWED_HOSTS doesn't include request domain
**Fix:** Add the exact domain from error message to ALLOWED_HOSTS

### Error: "CSRF verification failed"
**Cause:** CSRF_TRUSTED_ORIGINS not set
**Fix:** Already configured in settings.py ✓

---

## 📋 DEPLOYMENT STEPS

1. **Push code to GitHub:**
   ```bash
   git push origin main
   ```

2. **In Render Dashboard, update these environment variables:**
   - ALLOWED_HOSTS=fagierrands-backend-xwqi.onrender.com,fagierrands-backend.onrender.com,localhost,127.0.0.1
   - BASE_URL=https://fagierrands-backend-xwqi.onrender.com

3. **Wait for deployment to complete** (check Render logs)

4. **Test Swagger UI:**
   - Visit: https://fagierrands-backend-xwqi.onrender.com/api/docs/
   - Should load without 500 error

5. **If still errors, check Render logs:**
   - Go to: Logs tab in Render Dashboard
   - Look for Python tracebacks
   - Share the error here for help

---

## ✅ OPTIONAL (But Recommended)

- **FRONTEND_URL** - For CORS (already in settings.py)
- **Email settings** - For email verification (already configured)
- **Payment settings** - For M-Pesa (already configured)

---

## 🎯 QUICK TEST AFTER DEPLOYMENT

```bash
# Test if API is responding
curl https://fagierrands-backend-xwqi.onrender.com/

# Test Swagger schema
curl https://fagierrands-backend-xwqi.onrender.com/api/docs/?format=openapi

# Should return JSON schema, not 500 error
```
