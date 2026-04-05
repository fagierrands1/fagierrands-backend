# MediaFire Storage Troubleshooting Guide

This guide helps you diagnose and fix common issues with MediaFire storage integration.

## 🔍 Quick Diagnostics

Run these commands first to identify the issue:

```bash
# Test MediaFire connection
python test_mediafire_storage.py

# Check logs
tail -f logs/django.log | grep -i mediafire

# Check configuration
python manage.py shell
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> print("App ID:", bool(os.getenv('MEDIAFIRE_APP_ID')))
>>> print("API Key:", bool(os.getenv('MEDIAFIRE_API_KEY')))
>>> print("Email:", bool(os.getenv('MEDIAFIRE_EMAIL')))
>>> print("Password:", bool(os.getenv('MEDIAFIRE_PASSWORD')))
```

---

## ❌ Problem: "MediaFire service not available"

### Symptoms
- Test script shows "MediaFire service is not available"
- Files upload to Supabase instead of MediaFire
- Logs show "MediaFire not available"

### Diagnosis
```bash
python manage.py shell
>>> from accounts.mediafire_service import get_mediafire_service
>>> service = get_mediafire_service()
>>> print("App ID:", bool(service.app_id))
>>> print("API Key:", bool(service.api_key))
>>> print("Email:", bool(service.email))
>>> print("Password:", bool(service.password))
```

### Solutions

#### Solution 1: Missing Credentials
**If any value is False:**

1. Open your `.env` file
2. Verify all four credentials are present:
   ```env
   MEDIAFIRE_APP_ID=your_app_id
   MEDIAFIRE_API_KEY=your_api_key
   MEDIAFIRE_EMAIL=your_email@example.com
   MEDIAFIRE_PASSWORD=your_password
   ```
3. Save the file
4. Restart Django server
5. Run test script again

#### Solution 2: Incorrect Credentials
**If all values are True but still not available:**

1. Try logging into MediaFire website with same credentials
2. If login fails, reset your MediaFire password
3. Update `.env` file with new password
4. Restart Django server

#### Solution 3: Environment Variables Not Loading
**If credentials are in .env but not loading:**

1. Check `.env` file location (should be in project root)
2. Verify `python-dotenv` is installed:
   ```bash
   pip install python-dotenv
   ```
3. Check `settings.py` has:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```
4. Restart Django server

---

## ❌ Problem: "Authentication Failed"

### Symptoms
- Error: "Failed to get MediaFire session token"
- Error: "Authentication failed"
- Test script fails at authentication step

### Diagnosis
```bash
python manage.py shell
>>> from accounts.mediafire_service import get_mediafire_service
>>> service = get_mediafire_service()
>>> token = service._get_session_token()
>>> print("Token:", token)
```

### Solutions

#### Solution 1: Invalid Email/Password
1. Go to https://www.mediafire.com/
2. Try logging in with your credentials
3. If login fails:
   - Click "Forgot Password"
   - Reset your password
   - Update `.env` file
   - Restart Django server

#### Solution 2: Invalid App ID/API Key
1. Go to https://www.mediafire.com/developers/
2. Log in to your developer account
3. Navigate to "My Applications"
4. Verify your App ID and API Key
5. If they don't match your `.env` file:
   - Update `.env` with correct values
   - Restart Django server

#### Solution 3: Special Characters in Password
**If password contains special characters:**

1. In `.env` file, wrap password in quotes:
   ```env
   MEDIAFIRE_PASSWORD="your!pass@word#here"
   ```
2. Or change MediaFire password to one without special characters
3. Restart Django server

#### Solution 4: Account Suspended
1. Check your MediaFire account status
2. Log in to https://www.mediafire.com/myaccount/
3. Verify account is active
4. Check for any suspension notices
5. Contact MediaFire support if suspended

---

## ❌ Problem: "Upload Failed"

### Symptoms
- Files don't upload to MediaFire
- Error: "MediaFire upload failed"
- Files fall back to Supabase or local storage

### Diagnosis
```bash
# Check logs for specific error
tail -f logs/django.log | grep -i "upload"

# Test with small file
python manage.py shell
>>> from accounts.mediafire_service import get_mediafire_service
>>> service = get_mediafire_service()
>>> test_content = b"test"
>>> success, url, error = service.upload_file(test_content, "test.txt", "text/plain")
>>> print("Success:", success)
>>> print("Error:", error)
```

### Solutions

#### Solution 1: File Too Large
**If error mentions file size:**

1. Check file size limit in `settings.py`:
   ```python
   FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
   ```
2. Compress large files before upload
3. Or increase limit (not recommended for free tier)

#### Solution 2: Network Issues
**If error mentions timeout or connection:**

1. Check internet connection
2. Try uploading a small test file
3. Check MediaFire status: https://status.mediafire.com
4. Try again in a few minutes

#### Solution 3: API Rate Limit
**If error mentions rate limit:**

1. Check MediaFire dashboard for API usage
2. Free tier: 10,000 calls/day
3. Wait for rate limit to reset (midnight UTC)
4. Or upgrade to MediaFire Pro

#### Solution 4: Storage Full
**If error mentions storage:**

1. Log in to https://www.mediafire.com/myaccount/
2. Check storage usage
3. Free tier: 10GB
4. Delete old files or upgrade account

#### Solution 5: Invalid File Type
**If error mentions file type:**

1. Check file content type
2. Verify file is not corrupted
3. Try uploading a simple text file first

---

## ❌ Problem: "Files Not Accessible"

### Symptoms
- File uploads successfully
- URL is returned
- But clicking URL shows error or 404

### Diagnosis
```bash
# Test URL directly
curl -I "your_mediafire_url_here"

# Or in Python
python manage.py shell
>>> import requests
>>> url = "your_mediafire_url_here"
>>> response = requests.head(url)
>>> print("Status:", response.status_code)
```

### Solutions

#### Solution 1: File Not Public
1. Log in to MediaFire web interface
2. Navigate to your files
3. Right-click the file
4. Select "Share" or "Get Link"
5. Ensure sharing is set to "Public" or "Anyone with link"

#### Solution 2: Folder Permissions
1. Log in to MediaFire
2. Navigate to `fagierrands_verification` folder
3. Check folder permissions
4. Set to "Public" if needed

#### Solution 3: File Deleted
1. Check if file still exists in MediaFire
2. If deleted, re-upload the file
3. Update database with new URL

#### Solution 4: URL Expired
**MediaFire URLs shouldn't expire, but if they do:**

1. Get new URL from MediaFire
2. Update database record
3. Contact MediaFire support if issue persists

---

## ❌ Problem: "Slow Uploads"

### Symptoms
- Uploads take longer than 10 seconds
- Application feels slow
- Users complain about upload speed

### Diagnosis
```bash
# Time an upload
python manage.py shell
>>> import time
>>> from accounts.mediafire_service import get_mediafire_service
>>> service = get_mediafire_service()
>>> test_content = b"x" * (1024 * 1024)  # 1MB
>>> start = time.time()
>>> success, url, error = service.upload_file(test_content, "test.bin", "application/octet-stream")
>>> elapsed = time.time() - start
>>> print(f"Upload took {elapsed:.2f} seconds")
```

### Solutions

#### Solution 1: Compress Files
```python
# Add image compression before upload
from PIL import Image
from io import BytesIO

def compress_image(file, max_size=(1920, 1080), quality=85):
    img = Image.open(file)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return output
```

#### Solution 2: Use Async Uploads
```python
# Use Celery for background uploads
from celery import shared_task

@shared_task
def async_upload(file_path, user_id):
    # Upload in background
    pass
```

#### Solution 3: Check Network
1. Test internet speed
2. Check server bandwidth
3. Try from different network
4. Contact hosting provider

#### Solution 4: Upgrade MediaFire
1. Free tier may have speed limits
2. Consider MediaFire Pro for faster uploads
3. Check MediaFire dashboard for upgrade options

---

## ❌ Problem: "Test Script Fails"

### Symptoms
- `python test_mediafire_storage.py` shows errors
- One or more tests fail

### Solutions by Test Step

#### Step 1: Configuration Check Fails
**Missing credentials:**
- Add all four credentials to `.env` file
- See "MediaFire service not available" section above

#### Step 2: Service Availability Fails
**Can't connect to MediaFire:**
- Check internet connection
- Verify credentials are correct
- Check MediaFire status

#### Step 3: Service Initialization Fails
**Can't create service instance:**
- Check Django setup
- Verify imports work
- Check for Python errors in logs

#### Step 4: Authentication Fails
**Can't get session token:**
- See "Authentication Failed" section above
- Verify email and password
- Check App ID and API Key

#### Step 5: Upload Fails
**Can't upload test file:**
- See "Upload Failed" section above
- Check network connection
- Verify account has storage space

#### Step 6: File Info Fails
**Can't retrieve file info (optional):**
- This is not critical
- File upload still works
- May be API limitation

#### Step 7: Deletion Fails
**Can't delete test file:**
- Not critical for functionality
- File may need manual deletion
- Check folder permissions

---

## ❌ Problem: "Files Going to Supabase Instead of MediaFire"

### Symptoms
- Files upload successfully
- But URLs contain "supabase" not "mediafire"
- MediaFire is configured correctly

### Diagnosis
```bash
# Check which storage is being used
python manage.py shell
>>> from accounts.mediafire_service import is_mediafire_available
>>> from accounts.supabase_client import is_supabase_available
>>> print("MediaFire:", is_mediafire_available())
>>> print("Supabase:", is_supabase_available())
```

### Solutions

#### Solution 1: MediaFire Not Available
**If MediaFire shows False:**
- Follow "MediaFire service not available" section
- Verify credentials
- Restart Django server

#### Solution 2: Code Not Updated
**If using old code:**
1. Verify `storage_utils.py` has MediaFire integration
2. Check for this line:
   ```python
   from .mediafire_service import get_mediafire_service
   ```
3. If missing, re-apply the integration

#### Solution 3: Cache Issue
**If code is correct but not working:**
1. Restart Django server
2. Clear Python cache:
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +
   ```
3. Restart again

---

## ❌ Problem: "Import Error"

### Symptoms
- Error: "No module named 'accounts.mediafire_service'"
- Error: "cannot import name 'get_mediafire_service'"

### Solutions

#### Solution 1: File Not Created
1. Verify `accounts/mediafire_service.py` exists
2. If missing, re-create the file
3. Check file permissions

#### Solution 2: Python Path Issue
```bash
python manage.py shell
>>> import sys
>>> print(sys.path)
>>> # Verify project directory is in path
```

#### Solution 3: Syntax Error in File
```bash
python -m py_compile accounts/mediafire_service.py
# Check for syntax errors
```

---

## 🔧 Advanced Diagnostics

### Check Full System Status

```python
python manage.py shell

from accounts.mediafire_service import get_mediafire_service, is_mediafire_available
from accounts.supabase_client import is_supabase_available
from django.core.files.storage import default_storage

print("=== Storage System Status ===")
print(f"MediaFire Available: {is_mediafire_available()}")
print(f"Supabase Available: {is_supabase_available()}")
print(f"Local Storage Available: {default_storage is not None}")

if is_mediafire_available():
    service = get_mediafire_service()
    print(f"\nMediaFire Details:")
    print(f"  App ID: {service.app_id[:10]}..." if service.app_id else "  App ID: Not set")
    print(f"  Email: {service.email}")
    
    # Test authentication
    token = service._get_session_token()
    print(f"  Session Token: {'✅ Valid' if token else '❌ Invalid'}")
```

### Test Full Upload Flow

```python
python manage.py shell

from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.storage_utils import upload_verification_image

# Create test file
test_file = SimpleUploadedFile(
    "test_document.txt",
    b"This is a test file",
    content_type="text/plain"
)

# Test upload
success, url, error = upload_verification_image(
    file=test_file,
    user_id=1,
    file_type='test'
)

print(f"Success: {success}")
print(f"URL: {url}")
print(f"Error: {error}")

if url:
    if 'mediafire' in url.lower():
        print("✅ Using MediaFire (correct)")
    elif 'supabase' in url.lower():
        print("⚠️  Using Supabase (fallback)")
    else:
        print("⚠️  Using Local Storage (last resort)")
```

---

## 📞 Getting Help

### Before Contacting Support

Gather this information:

1. **Error Message**: Exact error from logs
2. **Test Results**: Output from `test_mediafire_storage.py`
3. **Configuration**: Confirm credentials are set (don't share actual values)
4. **Django Version**: `python manage.py --version`
5. **Python Version**: `python --version`
6. **Recent Changes**: Any recent code or config changes

### MediaFire Support

- **Developer Portal**: https://www.mediafire.com/developers/
- **API Documentation**: https://www.mediafire.com/developers/core_api/
- **Email**: developers@mediafire.com
- **Status Page**: https://status.mediafire.com

### Application Support

- Check logs: `tail -f logs/django.log`
- Review documentation in this directory
- Check GitHub issues (if applicable)
- Contact development team

---

## ✅ Prevention Tips

### Regular Maintenance

1. **Monthly**: Check MediaFire storage usage
2. **Quarterly**: Rotate API keys
3. **Yearly**: Review and update credentials
4. **Always**: Monitor logs for errors

### Best Practices

1. ✅ Keep credentials secure
2. ✅ Monitor API usage
3. ✅ Test after any changes
4. ✅ Keep documentation updated
5. ✅ Have backup plan (Supabase)

### Monitoring Setup

```python
# Add to your monitoring system
from accounts.mediafire_service import is_mediafire_available

def check_storage_health():
    if not is_mediafire_available():
        # Send alert
        send_alert("MediaFire storage is unavailable!")
```

---

## 📊 Common Error Codes

| Error Code | Meaning | Solution |
|------------|---------|----------|
| 401 | Authentication failed | Check credentials |
| 403 | Permission denied | Check folder permissions |
| 404 | File not found | Verify file exists |
| 413 | File too large | Reduce file size |
| 429 | Rate limit exceeded | Wait or upgrade |
| 500 | Server error | Check MediaFire status |
| 503 | Service unavailable | Try again later |

---

**Last Updated**: January 2025  
**Version**: 1.0