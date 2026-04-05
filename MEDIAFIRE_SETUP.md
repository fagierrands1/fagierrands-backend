# MediaFire Storage Integration Guide

This guide will help you set up MediaFire as your primary storage solution for Fagi Errands.

## Why MediaFire?

- **Free Storage**: MediaFire offers generous free storage (10GB+)
- **Reliable**: Established file hosting service with good uptime
- **API Access**: Full API for programmatic file management
- **Direct Links**: Get direct download links for files
- **No Bandwidth Limits**: Unlike some services, MediaFire doesn't restrict bandwidth on free accounts

## Storage Priority

The application uses a three-tier storage system:

1. **MediaFire** (Primary) - Fast, reliable cloud storage
2. **Supabase** (Fallback) - If MediaFire is unavailable
3. **Local Storage** (Last Resort) - If both cloud services fail

## Setup Instructions

### Step 1: Create MediaFire Developer Account

1. Go to [MediaFire Developers Portal](https://www.mediafire.com/developers/)
2. Click "Sign Up" or "Register" to create a developer account
3. If you already have a MediaFire account, you can use those credentials

### Step 2: Create an Application

1. Log in to the [MediaFire Developers Portal](https://www.mediafire.com/developers/)
2. Navigate to "My Applications" or "Create Application"
3. Fill in the application details:
   - **Application Name**: Fagi Errands Storage
   - **Description**: File storage for Fagi Errands delivery platform
   - **Application Type**: Web Application
4. Submit the application

### Step 3: Get Your API Credentials

After creating your application, you'll receive:
- **App ID**: A unique identifier for your application
- **API Key**: Your secret key for API authentication

**Important**: Keep these credentials secure and never commit them to version control!

### Step 4: Configure Environment Variables

Add the following to your `.env` file:

```env
# MediaFire Storage Configuration
MEDIAFIRE_APP_ID=your_app_id_here
MEDIAFIRE_API_KEY=your_api_key_here
MEDIAFIRE_EMAIL=your_mediafire_email@example.com
MEDIAFIRE_PASSWORD=your_mediafire_password
MEDIAFIRE_FOLDER_KEY=  # Optional: leave empty to auto-create folders
```

**Security Notes**:
- Use a strong, unique password for your MediaFire account
- Consider creating a dedicated MediaFire account just for the application
- Never share these credentials or commit them to Git

### Step 5: Test the Integration

Run the test script to verify your MediaFire setup:

```bash
python test_mediafire_storage.py
```

This will:
1. Check if MediaFire credentials are configured
2. Authenticate with MediaFire API
3. Upload a test file
4. Retrieve the file URL
5. Delete the test file

## Usage in Your Application

The MediaFire integration is automatic. When you upload files through the application:

```python
from accounts.storage_utils import upload_verification_image

# Upload a file
success, file_url, error = upload_verification_image(
    file=uploaded_file,
    user_id=user.id,
    file_type='verification'
)

if success:
    print(f"File uploaded successfully: {file_url}")
else:
    print(f"Upload failed: {error}")
```

## File Organization

Files are organized in MediaFire folders:
- `fagierrands_verification/` - User verification documents (ID cards, licenses)
- `fagierrands_orders/` - Order-related files
- `fagierrands_profiles/` - User profile images

## API Rate Limits

MediaFire API has the following limits:
- **Free Accounts**: 
  - 10,000 API calls per day
  - 10GB storage
  - Unlimited bandwidth
- **Premium Accounts**: Higher limits available

For most applications, the free tier is sufficient.

## Troubleshooting

### "Authentication Failed" Error

**Cause**: Invalid credentials or incorrect email/password

**Solution**:
1. Verify your MediaFire email and password are correct
2. Try logging in to MediaFire website with the same credentials
3. Check if your App ID and API Key are correct
4. Ensure there are no extra spaces in your .env file

### "Upload Failed" Error

**Cause**: Network issues, file size limits, or API errors

**Solution**:
1. Check your internet connection
2. Verify file size is under 10MB (configurable in settings)
3. Check MediaFire API status at [status.mediafire.com](https://status.mediafire.com)
4. Review application logs for detailed error messages

### "Session Token Expired" Error

**Cause**: Session tokens expire after a period of inactivity

**Solution**:
- The application automatically refreshes tokens
- If the issue persists, restart your Django server

### Files Not Accessible

**Cause**: Folder permissions or file visibility settings

**Solution**:
1. Log in to MediaFire web interface
2. Check folder permissions for the `fagierrands_*` folders
3. Ensure files are set to "Public" or "Anyone with link"

## Monitoring and Maintenance

### Check Storage Usage

Log in to your MediaFire account to monitor:
- Storage space used
- Number of files
- API call usage
- Bandwidth consumption

### Backup Strategy

While MediaFire is reliable, consider:
1. Keeping Supabase as a fallback (already configured)
2. Periodic backups of critical files
3. Monitoring upload success rates

## Security Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Rotate Credentials**: Change API keys periodically
3. **Monitor Access**: Review API usage logs regularly
4. **Limit Permissions**: Use dedicated accounts with minimal permissions
5. **HTTPS Only**: Ensure all API calls use HTTPS (default)

## Cost Considerations

### Free Tier (Current Setup)
- **Storage**: 10GB free
- **Bandwidth**: Unlimited
- **API Calls**: 10,000/day
- **Cost**: $0/month

### If You Need More
- **Pro Account**: 1TB storage, priority support
- **Business Account**: Unlimited storage, advanced features
- Check [MediaFire Pricing](https://www.mediafire.com/upgrade/) for details

## Migration from Supabase

If you're migrating existing files from Supabase to MediaFire:

1. The system will automatically use MediaFire for new uploads
2. Existing Supabase URLs will continue to work
3. To migrate old files, run the migration script:

```bash
python migrate_storage_to_mediafire.py
```

## Support

For MediaFire API issues:
- [MediaFire API Documentation](https://www.mediafire.com/developers/core_api/)
- [MediaFire Developer Forum](https://forum.mediafire.com/)
- Email: developers@mediafire.com

For application-specific issues:
- Check application logs in `logs/` directory
- Review Django error messages
- Contact your development team

## Additional Resources

- [MediaFire API Reference](https://www.mediafire.com/developers/core_api/1.5/getting_started/)
- [MediaFire Python SDK](https://github.com/MediaFire/mediafire-python-open-sdk) (alternative to our custom implementation)
- [File Upload Best Practices](https://www.mediafire.com/developers/core_api/1.5/upload/)

---

**Last Updated**: January 2025
**Version**: 1.0