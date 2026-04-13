# Phone Number Uniqueness Implementation

## Changes Made

### 1. Phone Number Normalization
- Created `normalize_phone_number()` function in `accounts/serializers.py`
- Normalizes all phone formats to `+254XXXXXXXXX` standard:
  - `0712345678` → `+254712345678`
  - `712345678` → `+254712345678`
  - `254712345678` → `+254712345678`
  - `+254712345678` → `+254712345678`

### 2. Database Constraints
- Updated `User.phone_number` field to allow `null=True`
- Added unique constraint at database level:
  ```python
  models.UniqueConstraint(
      fields=['phone_number'], 
      condition=models.Q(phone_number__isnull=False) & ~models.Q(phone_number=''),
      name='unique_phone_number'
  )
  ```

### 3. Registration Validation
- Added `validate_phone_number()` method in `RegisterSerializer`
- Checks for existing phone numbers in normalized format
- Returns error: "Phone number already registered"

### 4. Login & Verification Updates
- Updated `LoginView` to normalize phone numbers before lookup
- Updated `verify_phone()` to normalize phone numbers
- Updated `resend_otp()` to normalize phone numbers

### 5. Data Cleanup
- Created scripts to:
  - Normalize existing phone numbers
  - Identify and remove duplicate accounts
  - Keep oldest account when duplicates exist

## Migration Applied
- `accounts/migrations/0013_alter_user_phone_number_alter_user_phone_otp_and_more.py`

## Testing
Run the test script:
```bash
python test_phone_uniqueness.py
```

Expected results:
- ✅ First registration succeeds
- ❌ Second registration fails (same phone, different format)
- ❌ Third registration fails (same phone, another format)
- ✅ Fourth registration succeeds (different phone)

## API Response
When duplicate phone is detected:
```json
{
  "phone_number": ["Phone number already registered"]
}
```

## Benefits
1. **One phone per account** - Prevents multiple accounts with same phone
2. **Format agnostic** - Works with any phone format
3. **Database enforced** - Constraint at DB level prevents duplicates
4. **User friendly** - Clear error messages
5. **Backward compatible** - Existing accounts normalized automatically
