#!/bin/bash
# Render Environment Variables Checklist for Swagger/API Documentation

echo "=== CRITICAL ENVIRONMENT VARIABLES FOR SWAGGER UI ==="
echo ""

# Required Django Settings
echo "✓ SECRET_KEY - Set to a secure random string"
echo "✓ DEBUG - Should be 'False' in production"
echo "✓ ALLOWED_HOSTS - Must include your Render domain"
echo ""

# Database
echo "✓ DATABASE_URL - PostgreSQL connection string (auto-set by Render)"
echo ""

# CORS (Important for API access)
echo "✓ CORS settings in settings.py should allow your frontend domains"
echo ""

echo "=== OPTIONAL BUT RECOMMENDED ==="
echo "✓ FRONTEND_URL - Your frontend domain for CORS"
echo ""

echo "=== CHECK THESE IN RENDER DASHBOARD ==="
echo "1. Environment > Environment Variables"
echo "2. Ensure DATABASE_URL is set (auto-configured)"
echo "3. Ensure SECRET_KEY is set and secure"
echo "4. Set DEBUG=False"
echo "5. Set ALLOWED_HOSTS to include: fagierrands-backend-xwqi.onrender.com"
echo ""

echo "=== COMMON ISSUES ==="
echo "❌ Missing DATABASE_URL → 500 error on all endpoints"
echo "❌ Wrong ALLOWED_HOSTS → 400 Bad Request"
echo "❌ DEBUG=True in production → Security risk"
echo "❌ Missing SECRET_KEY → Django won't start"
echo ""

echo "=== VERIFY AFTER DEPLOYMENT ==="
echo "1. Visit: https://fagierrands-backend-xwqi.onrender.com/api/docs/"
echo "2. Should see Swagger UI interface"
echo "3. Check Render logs for any errors"
echo "4. Test a simple GET endpoint"
