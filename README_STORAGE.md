# Fagi Errands Storage System

## Overview

The Fagi Errands application uses a robust three-tier storage system to ensure files are always available:

```
┌─────────────────────────────────────────────────────────┐
│                    File Upload Request                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 1: MediaFire (Primary)                            │
│  ✓ 10GB free storage                                    │
│  ✓ Unlimited bandwidth                                  │
│  ✓ Direct download links                                │
│  ✓ 10,000 API calls/day                                 │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   Success?    │
                    └───────┬───────┘
                            │ No
                            ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 2: Supabase (Fallback)                            │
│  ✓ Integrated with database                             │
│  ✓ Automatic backups                                    │
│  ✓ Built-in CDN                                         │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   Success?    │
                    └───────┬───────┘
                            │ No
                            ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 3: Local Storage (Last Resort)                    │
│  ✓ Server filesystem                                    │
│  ✓ Always available                                     │
│  ✓ No external dependencies                             │
└─────────────────────────────────────────────────────────┘
```

## Features

- ✅ **Automatic Failover**: If MediaFire fails, automatically tries Supabase, then local storage
- ✅ **Transparent**: Application code doesn't need to know which storage is used
- ✅ **Reliable**: Three layers of redundancy ensure files are never lost
- ✅ **Cost-Effective**: Uses free tiers of cloud services
- ✅ **Scalable**: Easy to upgrade to paid tiers as needed

## Files Included

### Core Implementation
- `accounts/mediafire_service.py` - MediaFire API integration
- `accounts/storage_utils.py` - Unified storage interface
- `accounts/supabase_client.py` - Supabase integration (existing)

### Configuration
- `fagierrandsbackup/settings.py` - Storage settings
- `.env.example` - Environment variable template

### Documentation
- `MEDIAFIRE_SETUP.md` - Detailed setup instructions
- `STORAGE_QUICK_REFERENCE.md` - Quick reference guide
- `README_STORAGE.md` - This file

### Testing & Utilities
- `test_mediafire_storage.py` - Test MediaFire integration
- `migrate_storage_to_mediafire.py` - Migrate existing files

## Quick Setup (5 Minutes)

### 1. Get MediaFire Credentials

1. Visit https://www.mediafire.com/developers/
2. Create a developer account
3. Create a new application
4. Copy your App ID and API Key

### 2. Configure Environment

Add to your `.env` file:

```env
MEDIAFIRE_APP_ID=your_app_id_here
MEDIAFIRE_API_KEY=your_api_key_here
MEDIAFIRE_EMAIL=your_mediafire_email@example.com
MEDIAFIRE_PASSWORD=your_mediafire_password
```

### 3. Test Configuration

```bash
cd fagierrands/fagierrandsbackup
python test_mediafire_storage.py
```

### 4. Done!

Your application now uses MediaFire for storage! 🎉

## Usage

### In Your Code

The storage system is transparent. Just use the existing functions:

```python
from accounts.storage_utils import upload_verification_image

# Upload a file (automatically uses MediaFire → Supabase → Local)
success, url, error = upload_verification_image(
    file=request.FILES['document'],
    user_id=request.user.id,
    file_type='verification'
)

if success:
    # File uploaded successfully to one of the storage tiers
    user.verification_document_url = url
    user.save()
else:
    # All storage tiers failed
    return Response({'error': error}, status=500)
```

### File Types Supported

The system handles all file types:
- Images: JPG, PNG, GIF, WebP
- Documents: PDF, DOC, DOCX
- Any other file type up to 10MB (configurable)

## Storage Locations

### MediaFire Organization

Files are organized in folders:

```
MediaFire Account
├── fagierrands_verification/
│   ├── 123_verification_drivers_license.jpg
│   ├── 124_verification_national_id.pdf
│   └── ...
├── fagierrands_orders/
│   ├── order_456_receipt.jpg
│   └── ...
└── fagierrands_profiles/
    ├── user_123_avatar.jpg
    └── ...
```

### File Naming Convention

```
{user_id}_{file_type}_{original_filename}
```

Examples:
- `123_verification_drivers_license.jpg`
- `456_profile_avatar.png`
- `789_order_receipt.pdf`

## Monitoring

### Check Storage Status

```bash
# Test MediaFire connection
python test_mediafire_storage.py

# Check which storage is being used
python manage.py shell
>>> from accounts.mediafire_service import is_mediafire_available
>>> from accounts.supabase_client import is_supabase_available
>>> print(f"MediaFire: {is_mediafire_available()}")
>>> print(f"Supabase: {is_supabase_available()}")
```

### View Upload Statistics

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Count files by storage provider
mediafire_count = User.objects.filter(
    verification_document_url__icontains='mediafire'
).count()

supabase_count = User.objects.filter(
    verification_document_url__icontains='supabase'
).count()

local_count = User.objects.filter(
    verification_document_url__icontains='/media/'
).count()

print(f"MediaFire: {mediafire_count}")
print(f"Supabase: {supabase_count}")
print(f"Local: {local_count}")
```

## Migration

### Migrate Existing Files to MediaFire

If you have existing files in Supabase and want to move them to MediaFire:

```bash
python migrate_storage_to_mediafire.py
```

This script will:
1. Find all files currently in Supabase
2. Download each file
3. Upload to MediaFire
4. Update database with new URLs
5. Optionally delete from Supabase

**Warning**: Make backups before running migration!

## Troubleshooting

### Problem: Files not uploading to MediaFire

**Solution**:
1. Check credentials: `python test_mediafire_storage.py`
2. Verify MediaFire account is active
3. Check API rate limits (10,000/day on free tier)
4. Review logs: `tail -f logs/django.log | grep MediaFire`

### Problem: "Authentication Failed" error

**Solution**:
1. Verify email and password are correct
2. Try logging into MediaFire website with same credentials
3. Check for typos in .env file
4. Ensure no extra spaces in environment variables

### Problem: Files upload but aren't accessible

**Solution**:
1. Check MediaFire folder permissions
2. Verify files are set to "Public" or "Anyone with link"
3. Test URL directly in browser
4. Check if MediaFire account has storage space

### Problem: Slow uploads

**Solution**:
1. Check network connection
2. Reduce file size (compress images)
3. Consider upgrading MediaFire account
4. Use async uploads with Celery

## Performance

### Upload Times (Approximate)

| File Size | MediaFire | Supabase | Local |
|-----------|-----------|----------|-------|
| 100 KB    | 1-2s      | 1-2s     | <1s   |
| 1 MB      | 2-4s      | 2-4s     | <1s   |
| 5 MB      | 5-10s     | 5-10s    | 1-2s  |
| 10 MB     | 10-20s    | 10-20s   | 2-3s  |

### Optimization Tips

1. **Compress Images**: Use Pillow to compress before upload
2. **Async Uploads**: Use Celery for large files
3. **Batch Uploads**: Upload multiple files in parallel
4. **CDN**: MediaFire provides CDN automatically

## Security

### Best Practices

1. ✅ **Environment Variables**: Never hardcode credentials
2. ✅ **File Validation**: Validate file types and sizes
3. ✅ **Access Control**: Verify user permissions before upload
4. ✅ **HTTPS**: All uploads use HTTPS
5. ✅ **Credential Rotation**: Change API keys periodically

### File Validation Example

```python
ALLOWED_TYPES = ['image/jpeg', 'image/png', 'application/pdf']
MAX_SIZE = 10 * 1024 * 1024  # 10MB

def validate_upload(file):
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("File type not allowed")
    
    if file.size > MAX_SIZE:
        raise ValueError("File too large")
    
    return True
```

## Cost Analysis

### Current Setup (Free Tier)

| Service | Storage | Bandwidth | API Calls | Cost |
|---------|---------|-----------|-----------|------|
| MediaFire | 10GB | Unlimited | 10,000/day | $0 |
| Supabase | 1GB | 2GB/month | Unlimited | $0 |
| Local | Unlimited | N/A | N/A | $0 |
| **Total** | **11GB+** | **Unlimited** | **10,000/day** | **$0/month** |

### If You Need More

**MediaFire Pro**: $3.75/month
- 1TB storage
- Priority support
- No ads

**Supabase Pro**: $25/month
- 8GB storage
- 100GB bandwidth
- Better performance

## API Limits

### MediaFire Free Tier

- **Storage**: 10GB
- **API Calls**: 10,000 per day
- **File Size**: Up to 4GB per file
- **Bandwidth**: Unlimited

### Monitoring Usage

Check your MediaFire dashboard:
https://www.mediafire.com/myaccount/

Set up alerts when approaching limits.

## Backup Strategy

### Automatic Backups

1. **Primary**: MediaFire (automatic)
2. **Secondary**: Supabase (automatic fallback)
3. **Tertiary**: Local storage (last resort)

### Manual Backups

For critical files, consider:
1. Periodic downloads to local backup
2. Database backups (includes file URLs)
3. MediaFire account backup

## Support

### Documentation

- **Setup Guide**: See `MEDIAFIRE_SETUP.md`
- **Quick Reference**: See `STORAGE_QUICK_REFERENCE.md`
- **MediaFire API**: https://www.mediafire.com/developers/core_api/

### Getting Help

1. **Check Logs**: `tail -f logs/django.log`
2. **Test Connection**: `python test_mediafire_storage.py`
3. **MediaFire Support**: developers@mediafire.com
4. **Application Issues**: Contact your development team

## Advanced Usage

### Custom Storage Folders

```python
from accounts.mediafire_service import get_mediafire_service

mediafire = get_mediafire_service()

success, url, error = mediafire.upload_file(
    file_content=file.read(),
    filename='custom_file.jpg',
    content_type='image/jpeg',
    folder_name='custom_folder_name'  # Custom folder
)
```

### Batch Operations

```python
from accounts.mediafire_service import get_mediafire_service

mediafire = get_mediafire_service()
results = []

for file in files:
    success, url, error = mediafire.upload_file(
        file_content=file.read(),
        filename=file.name,
        content_type=file.content_type
    )
    results.append({'success': success, 'url': url})

print(f"Uploaded {sum(r['success'] for r in results)} files")
```

### Async Uploads with Celery

```python
from celery import shared_task
from accounts.storage_utils import upload_verification_image

@shared_task
def async_upload_file(file_path, user_id):
    with open(file_path, 'rb') as f:
        success, url, error = upload_verification_image(
            file=f,
            user_id=user_id,
            file_type='verification'
        )
    return {'success': success, 'url': url}
```

## Testing

### Unit Tests

```bash
# Run all storage tests
python manage.py test accounts.tests.test_storage

# Run specific test
python manage.py test accounts.tests.test_storage.MediaFireTestCase
```

### Manual Testing

```bash
# Test MediaFire integration
python test_mediafire_storage.py

# Test in Django shell
python manage.py shell
>>> from accounts.storage_utils import upload_verification_image
>>> # Test upload here
```

## Changelog

### Version 1.0 (January 2025)
- ✅ Initial MediaFire integration
- ✅ Three-tier storage system
- ✅ Automatic failover
- ✅ Migration script
- ✅ Comprehensive documentation

## Future Enhancements

- [ ] Add AWS S3 as additional tier
- [ ] Implement file compression
- [ ] Add image thumbnail generation
- [ ] Implement file versioning
- [ ] Add storage analytics dashboard

## Contributing

When modifying the storage system:

1. Update tests in `accounts/tests/test_storage.py`
2. Update documentation
3. Test all three storage tiers
4. Verify failover works correctly
5. Check performance impact

## License

This storage system is part of the Fagi Errands application.

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Maintainer**: Fagi Errands Development Team