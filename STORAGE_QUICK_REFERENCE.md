# Storage System Quick Reference

## Overview

Fagi Errands uses a three-tier storage system for reliability:

1. **MediaFire** (Primary) - Cloud storage with API
2. **Supabase** (Fallback) - Cloud storage backup
3. **Local Storage** (Last Resort) - Server filesystem

## Quick Start

### 1. Configure MediaFire (5 minutes)

```bash
# Add to .env file
MEDIAFIRE_APP_ID=your_app_id
MEDIAFIRE_API_KEY=your_api_key
MEDIAFIRE_EMAIL=your_email@example.com
MEDIAFIRE_PASSWORD=your_password
```

Get credentials at: https://www.mediafire.com/developers/

### 2. Test Configuration

```bash
python test_mediafire_storage.py
```

### 3. Start Using

Files will automatically upload to MediaFire!

## Common Tasks

### Upload a File

```python
from accounts.storage_utils import upload_verification_image

success, url, error = upload_verification_image(
    file=request.FILES['document'],
    user_id=request.user.id,
    file_type='verification'
)

if success:
    # Save URL to database
    user.verification_document_url = url
    user.save()
```

### Delete a File

```python
from accounts.storage_utils import delete_verification_image

success, error = delete_verification_image(
    file_path=user.verification_document_url,
    user_id=user.id
)
```

### Get File URL

```python
from accounts.storage_utils import get_verification_image_url

url = get_verification_image_url(user.verification_document_url)
```

## Storage Locations

### MediaFire Folders
- `fagierrands_verification/` - ID cards, licenses, etc.
- `fagierrands_orders/` - Order receipts, photos
- `fagierrands_profiles/` - User avatars

### File Naming Convention
```
{user_id}_{file_type}_{original_filename}
```

Example: `123_verification_drivers_license.jpg`

## Troubleshooting

### Files Not Uploading

1. Check MediaFire credentials:
   ```bash
   python test_mediafire_storage.py
   ```

2. Check logs:
   ```bash
   tail -f logs/django.log
   ```

3. Verify file size (max 10MB by default)

### Files Not Accessible

1. Check if URL is valid:
   ```python
   import requests
   response = requests.head(file_url)
   print(response.status_code)  # Should be 200
   ```

2. Check MediaFire account status

3. Verify file wasn't deleted

### Slow Uploads

- MediaFire free tier may have rate limits
- Check network connection
- Consider upgrading MediaFire account

## API Limits

### MediaFire Free Tier
- **Storage**: 10GB
- **API Calls**: 10,000/day
- **Bandwidth**: Unlimited
- **File Size**: Up to 4GB per file

### Monitoring Usage

Check MediaFire dashboard:
https://www.mediafire.com/myaccount/

## Migration

### Move Existing Files to MediaFire

```bash
python migrate_storage_to_mediafire.py
```

This will:
1. Download files from Supabase
2. Upload to MediaFire
3. Update database URLs
4. Optionally delete from Supabase

## Code Examples

### Custom Upload Function

```python
from accounts.mediafire_service import get_mediafire_service

def upload_custom_file(file_content, filename):
    mediafire = get_mediafire_service()
    
    success, url, error = mediafire.upload_file(
        file_content=file_content,
        filename=filename,
        content_type='image/jpeg',
        folder_name='custom_folder'
    )
    
    return url if success else None
```

### Check Storage Availability

```python
from accounts.mediafire_service import is_mediafire_available
from accounts.supabase_client import is_supabase_available

if is_mediafire_available():
    print("MediaFire is ready")
elif is_supabase_available():
    print("Using Supabase fallback")
else:
    print("Using local storage")
```

### Batch Upload

```python
from accounts.mediafire_service import get_mediafire_service

mediafire = get_mediafire_service()
uploaded_urls = []

for file in files:
    success, url, error = mediafire.upload_file(
        file_content=file.read(),
        filename=file.name,
        content_type=file.content_type
    )
    
    if success:
        uploaded_urls.append(url)
    else:
        print(f"Failed: {error}")

print(f"Uploaded {len(uploaded_urls)} files")
```

## Environment Variables

### Required for MediaFire
```env
MEDIAFIRE_APP_ID=required
MEDIAFIRE_API_KEY=required
MEDIAFIRE_EMAIL=required
MEDIAFIRE_PASSWORD=required
```

### Optional
```env
MEDIAFIRE_FOLDER_KEY=optional  # Pre-created folder
```

### Supabase (Fallback)
```env
SUPABASE_URL=optional
SUPABASE_KEY=optional
```

## File Size Limits

### Current Settings (settings.py)
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
```

### To Increase Limits
```python
# In settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
```

## Security

### Best Practices
1. ✅ Use environment variables for credentials
2. ✅ Never commit .env file to Git
3. ✅ Rotate API keys periodically
4. ✅ Use HTTPS for all uploads
5. ✅ Validate file types before upload

### File Type Validation

```python
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']

def validate_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {ext} not allowed")
```

## Performance Tips

1. **Async Uploads**: Use Celery for large files
2. **Compression**: Compress images before upload
3. **Caching**: Cache file URLs in database
4. **CDN**: MediaFire provides CDN automatically

## Support

### Documentation
- [MediaFire Setup Guide](MEDIAFIRE_SETUP.md)
- [MediaFire API Docs](https://www.mediafire.com/developers/core_api/)

### Logs
```bash
# Django logs
tail -f logs/django.log

# Storage-specific logs
grep "MediaFire" logs/django.log
grep "storage" logs/django.log
```

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Authentication failed | Check credentials |
| 403 | Permission denied | Check folder permissions |
| 413 | File too large | Reduce file size |
| 429 | Rate limit exceeded | Wait or upgrade account |
| 500 | Server error | Check MediaFire status |

## Testing

### Unit Tests

```python
# Run storage tests
python manage.py test accounts.tests.test_storage
```

### Manual Testing

```bash
# Test MediaFire
python test_mediafire_storage.py

# Test full upload flow
python manage.py shell
>>> from accounts.storage_utils import upload_verification_image
>>> # Test upload here
```

## Monitoring

### Check Upload Success Rate

```python
from django.contrib.auth import get_user_model

User = get_user_model()

total = User.objects.count()
with_files = User.objects.exclude(verification_document_url='').count()
mediafire_files = User.objects.filter(verification_document_url__icontains='mediafire').count()

print(f"Total users: {total}")
print(f"Users with files: {with_files}")
print(f"Files on MediaFire: {mediafire_files}")
print(f"Success rate: {(mediafire_files/with_files*100):.1f}%")
```

## Backup Strategy

1. **Primary**: MediaFire (automatic)
2. **Fallback**: Supabase (automatic)
3. **Manual**: Periodic database backups
4. **Critical**: Download important files locally

---

**Last Updated**: January 2025
**Version**: 1.0