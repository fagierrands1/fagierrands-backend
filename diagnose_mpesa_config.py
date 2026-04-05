#!/usr/bin/env python
"""
Diagnose M-Pesa Configuration Issues
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fagierrandsbackup.settings')
django.setup()

from django.conf import settings

print('\n' + '='*70)
print('🔍 M-PESA CONFIGURATION DIAGNOSIS')
print('='*70 + '\n')

print('📋 Current Configuration:')
print('-'*70)
print(f'Environment:        {settings.MPESA_ENVIRONMENT}')
print(f'Consumer Key:       {settings.MPESA_CONSUMER_KEY[:20]}...' if settings.MPESA_CONSUMER_KEY else 'Not set')
print(f'Consumer Secret:    {settings.MPESA_CONSUMER_SECRET[:20]}...' if settings.MPESA_CONSUMER_SECRET else 'Not set')
print(f'Shortcode:          {settings.MPESA_SHORTCODE}')
print(f'Pass Key:           {settings.MPESA_PASSKEY[:20]}...' if settings.MPESA_PASSKEY else 'Not set')
print('-'*70 + '\n')

print('⚠️  COMMON ISSUES:')
print('-'*70)

# Check environment
if settings.MPESA_ENVIRONMENT == 'sandbox':
    print('✓ Environment: SANDBOX')
    print('  → Using Sandbox API (https://sandbox.safaricom.co.ke)')
    print('  → Test with any phone number format')
    print()
elif settings.MPESA_ENVIRONMENT == 'production':
    print('✓ Environment: PRODUCTION')
    print('  → Using Production API (https://api.safaricom.co.ke)')
    print('  ⚠️  Only real transactions will work!')
    print()
else:
    print(f'❌ Unknown environment: {settings.MPESA_ENVIRONMENT}')
    print()

# Check credentials completeness
missing = []
if not settings.MPESA_CONSUMER_KEY:
    missing.append('MPESA_CONSUMER_KEY')
if not settings.MPESA_CONSUMER_SECRET:
    missing.append('MPESA_CONSUMER_SECRET')
if not settings.MPESA_SHORTCODE:
    missing.append('MPESA_SHORTCODE')
if not settings.MPESA_PASSKEY:
    missing.append('MPESA_PASSKEY')

if missing:
    print(f'❌ Missing credentials: {", ".join(missing)}')
else:
    print('✓ All required credentials are set')
print()

print('🔗 API ENDPOINTS:')
print('-'*70)
if settings.MPESA_ENVIRONMENT == 'sandbox':
    base_url = 'https://sandbox.safaricom.co.ke'
else:
    base_url = 'https://api.safaricom.co.ke'

print(f'Base URL:           {base_url}')
print(f'STK Push:           {base_url}/mpesa/stkpush/v1/processrequest')
print(f'Token:              {base_url}/oauth/v1/generate?grant_type=client_credentials')
print()

print('💡 NEXT STEPS:')
print('-'*70)
print('1. If you\'re in PRODUCTION, verify with Safaricom that:')
print('   - Your API keys are active')
print('   - Your Shortcode (3573531) is properly configured')
print('   - Your callback URLs are whitelisted')
print()
print('2. Try this diagnostic test:')
print('   python -c "from orders.mpesa_service import MpesaDarajaService; m = MpesaDarajaService(); print(m.get_access_token())"')
print()
print('3. If that fails, you likely need to:')
print('   - Update your API credentials in .env')
print('   - Or switch to sandbox mode for testing')
print()

print('='*70 + '\n')