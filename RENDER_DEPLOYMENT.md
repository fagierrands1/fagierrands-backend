# Render Deployment Guide for Fagi Errands Backend

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your GitHub repository connected to Render
3. PostgreSQL database credentials (Render provides this)
4. All required environment variables ready

## Quick Deploy (Using render.yaml)

### Option 1: Automatic Deployment via Blueprint

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Create New Blueprint on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to create all services

3. **Configure Environment Variables**
   After deployment, go to your web service settings and add:
   - `ALLOWED_HOSTS` - Add your Render URL (e.g., `your-app.onrender.com`)
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_KEY` - Your Supabase anon key
   - `MEDIAFIRE_APP_ID` - MediaFire app ID
   - `MEDIAFIRE_API_KEY` - MediaFire API key
   - `MEDIAFIRE_EMAIL` - MediaFire account email
   - `MEDIAFIRE_PASSWORD` - MediaFire account password
   - `EMAIL_HOST_USER` - Brevo SMTP email
   - `EMAIL_HOST_PASSWORD` - Brevo SMTP password
   - `DEFAULT_FROM_EMAIL` - Your sender email
   - `FRONTEND_URL` - Your frontend URL
   - `MPESA_CONSUMER_KEY` - M-Pesa consumer key
   - `MPESA_CONSUMER_SECRET` - M-Pesa consumer secret
   - `MPESA_SHORTCODE` - M-Pesa shortcode
   - `MPESA_PASSKEY` - M-Pesa passkey
   - `BASE_URL` - Your Render backend URL
   - `REDIS_URL` - (Optional) Redis connection string
   - `VAPID_PRIVATE_KEY` - Web push private key
   - `VAPID_PUBLIC_KEY` - Web push public key
   - `WEBPUSH_EMAIL` - Web push contact email

### Option 2: Manual Deployment

1. **Create PostgreSQL Database**
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Name: `fagierrands-db`
   - Choose a plan (Free tier available)
   - Click "Create Database"
   - Copy the "Internal Database URL"

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `fagierrands-backend`
     - **Runtime**: Python 3
     - **Build Command**: `./build_file.sh`
     - **Start Command**: `gunicorn fagierrandsbackup.wsgi --log-file -`
     - **Plan**: Choose your plan

3. **Add Environment Variables**
   In the "Environment" section, add all variables listed above.

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy

## Post-Deployment Steps

### 1. Update ALLOWED_HOSTS
After deployment, update the `ALLOWED_HOSTS` environment variable:
```
your-app.onrender.com,localhost,127.0.0.1
```

### 2. Update CSRF_TRUSTED_ORIGINS
In your Django settings, ensure your Render URL is in `CSRF_TRUSTED_ORIGINS`:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://your-app.onrender.com',
]
```

### 3. Run Migrations (if needed)
Render runs migrations automatically via `build_file.sh`, but if you need to run them manually:
- Go to your web service
- Click "Shell" tab
- Run: `python manage.py migrate`

### 4. Create Superuser
To create an admin user:
- Go to your web service
- Click "Shell" tab
- Run: `python manage.py createsuperuser`

### 5. Test Your Deployment
Visit your Render URL to verify the deployment:
```
https://your-app.onrender.com/admin/
```

## Important Notes

### Free Tier Limitations
- Free tier services spin down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- Database has 90-day expiration on free tier

### Database Backups
- Render automatically backs up paid databases
- For free tier, manually backup your data regularly

### Static Files
- Static files are served via WhiteNoise (already configured)
- No additional CDN setup needed for basic deployment

### Media Files
- This project uses Supabase and MediaFire for media storage
- Ensure environment variables are correctly set

### Logs
- View logs in real-time from the Render dashboard
- Click on your service → "Logs" tab

## Troubleshooting

### Build Fails
1. Check build logs for specific errors
2. Ensure `build_file.sh` has execute permissions:
   ```bash
   chmod +x build_file.sh
   ```
3. Verify all dependencies in `requirements.txt` are compatible

### Database Connection Issues
1. Verify `DATABASE_URL` is correctly set
2. Check database is running in Render dashboard
3. Ensure database and web service are in the same region

### Static Files Not Loading
1. Run `python manage.py collectstatic` manually
2. Check `STATIC_ROOT` and `STATIC_URL` in settings
3. Verify WhiteNoise is in `MIDDLEWARE`

### Environment Variables Not Working
1. Ensure no typos in variable names
2. Restart the service after adding new variables
3. Check `.env.example` for reference

## Updating Your Deployment

### Automatic Deploys
Render automatically deploys when you push to your main branch:
```bash
git add .
git commit -m "Your update message"
git push origin main
```

### Manual Deploy
- Go to your web service in Render
- Click "Manual Deploy" → "Deploy latest commit"

## Monitoring

### Health Checks
Render automatically monitors your service health. Configure custom health checks:
- Go to service settings
- Add health check path (e.g., `/admin/`)

### Performance
- Monitor response times in Render dashboard
- Consider upgrading to paid tier for better performance

## Scaling

### Vertical Scaling
- Upgrade your plan for more CPU/RAM
- Go to service settings → "Plan"

### Horizontal Scaling
- Available on paid plans
- Configure number of instances in settings

## Security Best Practices

1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Use Render's environment variables

2. **Use Strong SECRET_KEY**
   - Render generates one automatically
   - Or generate: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

3. **Set DEBUG=False in production**
   - Already configured in `render.yaml`

4. **Keep Dependencies Updated**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

5. **Regular Backups**
   - Export database regularly
   - Backup media files from Supabase/MediaFire

## Support

- Render Documentation: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- Project Issues: Create an issue in your GitHub repository

## Additional Services (Optional)

### Redis (for Celery)
1. Create Redis instance on Render
2. Copy connection URL
3. Add to `REDIS_URL` environment variable

### Background Workers
For Celery workers, create a new Background Worker service:
- **Build Command**: `./build_file.sh`
- **Start Command**: `celery -A fagierrandsbackup worker -l info`

### Celery Beat (Scheduled Tasks)
Create another Background Worker:
- **Start Command**: `celery -A fagierrandsbackup beat -l info`

## Cost Optimization

1. **Use Free Tier for Development**
   - Free PostgreSQL (90 days)
   - Free web service (750 hours/month)

2. **Upgrade for Production**
   - Starter plan: $7/month (no spin-down)
   - Database: $7/month (persistent)

3. **Monitor Usage**
   - Check bandwidth usage
   - Optimize database queries
   - Use caching where possible

---

**Deployment Date**: 2026-04-05
**Last Updated**: 2026-04-05
