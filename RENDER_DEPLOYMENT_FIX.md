# Deployment Fix for Render

## Issue Fixed
- Removed orphaned `orders_reportissue_evidence_photos` table that was causing deletion errors
- Fixed migration 0040 that was trying to remove non-existent columns

## Steps to Deploy on Render

### 1. Push Changes to Git
```bash
git add .
git commit -m "Fix phone uniqueness and remove orphaned reportissue table"
git push origin main
```

### 2. Run Migrations on Render
After deployment, run these commands in Render Shell:

```bash
# Fake the problematic migration if it hasn't run yet
python manage.py migrate orders 0040 --fake

# Run all pending migrations
python manage.py migrate

# Verify migrations
python manage.py showmigrations
```

### 3. Environment Variables to Update on Render
Make sure these are set in Render Environment:

```
# Already set - just verify
DEBUG=False
ALLOWED_HOSTS=fagierrands-backend-xwqi.onrender.com
DATABASE_URL=<your-postgres-url>

# Phone normalization is automatic - no env vars needed
```

### 4. Test After Deployment

Test phone uniqueness:
```bash
curl -X POST https://fagierrands-backend-xwqi.onrender.com/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test1",
    "email": "test1@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "phone_number": "0712345678",
    "user_type": "user"
  }'
```

Try duplicate (should fail):
```bash
curl -X POST https://fagierrands-backend-xwqi.onrender.com/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test2",
    "email": "test2@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "phone_number": "+254712345678",
    "user_type": "user"
  }'
```

Expected response:
```json
{
  "phone_number": ["Phone number already registered"]
}
```

## Files Changed
1. `accounts/models.py` - Added unique constraint for phone_number
2. `accounts/serializers.py` - Added phone normalization and validation
3. `accounts/views.py` - Updated login/verify to normalize phones
4. `fagierrandsbackup/settings.py` - Changed default permission to AllowAny
5. `orders/migrations/0041_remove_orphaned_reportissue_table.py` - New migration

## Migrations Applied
- `accounts/0013_alter_user_phone_number_alter_user_phone_otp_and_more.py`
- `orders/0041_remove_orphaned_reportissue_table.py`
