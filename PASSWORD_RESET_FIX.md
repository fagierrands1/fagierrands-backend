# Password Reset Phone Normalization Fix

## Issue
Password reset was failing with "User not found" error when using phone numbers in different formats (e.g., `0719224951` vs `+254719224951`).

## Root Cause
Password reset endpoints were not normalizing phone numbers before database lookup, while registration was storing them in normalized format (`+254XXXXXXXXX`).

## Solution
Added `normalize_phone_number()` to all password reset endpoints:

### Files Updated

1. **accounts/password_reset_views.py** (Old API)
   - `RequestPasswordResetView` - Normalizes phone before lookup
   - `VerifyPasswordResetOTPView` - Normalizes phone before verification
   - `ResetPasswordView` - Normalizes phone before password reset

2. **accounts/password_reset_v1.py** (New API)
   - `RequestPasswordResetV1` - Normalizes phone before lookup
   - `ResetPasswordV1` - Normalizes phone before password reset

## Affected Endpoints

### Old API (Still Working)
- `POST /api/accounts/password-reset/request/` ✅
- `POST /api/accounts/password-reset/verify-otp/` ✅
- `POST /api/accounts/password-reset/reset/` ✅

### New API (Recommended)
- `POST /api/accounts/v1/password-reset/request/` ✅
- `POST /api/accounts/v1/password-reset/reset/` ✅

## Testing

### Test Password Reset Request
```bash
curl -X POST https://fagierrands-backend-xwqi.onrender.com/api/accounts/password-reset/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "0719224951"
  }'
```

**Expected:** 200 OK with "OTP sent to your phone" (if user exists)

### Test with Different Formats
All these formats now work:
- `0719224951` → `+254719224951`
- `719224951` → `+254719224951`
- `254719224951` → `+254719224951`
- `+254719224951` → `+254719224951`

## Status
✅ Fixed locally  
⏳ Ready for production deployment

## Deployment
Just push to Git - no migrations needed. The fix is in the view logic only.

```bash
git push origin main
```

After Render deploys, test the password reset flow with any phone format.
