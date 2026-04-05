# NCBA Testing - Quick Reference Card

Copy and paste these commands into PowerShell or Command Prompt.

## 🚀 Most Common Commands

```powershell
# Quick test (fastest - 2-3 min)
python quick_test_ncba.py

# Interactive menu (easy to use)
.\run_ncba_tests.ps1

# All tests (comprehensive - 5-10 min)
python manage.py test test_ncba_comprehensive -v 2
```

---

## 🔬 Specific Test Commands

### Authentication Tests
```powershell
# Get access token
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_get_access_token -v 2

# Token caching
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_token_caching -v 2
```

### STK Push Tests (Lipa Na NCBA)
```powershell
# Valid phone
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_valid_phone -v 2

# Invalid phone (error handling)
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_invalid_phone -v 2

# Various amounts
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_different_amounts -v 2

# Query transaction status
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_query -v 2
```

### B2C Tests (Payouts)
```powershell
# Single payout
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2c_payment -v 2

# Multiple payouts
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2c_multiple_payouts -v 2
```

### B2B Tests (Business Payments)
```powershell
# B2B payment
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2b_payment -v 2

# Different identifier types
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2b_with_different_identifiers -v 2
```

### Account & Balance Tests
```powershell
# Account balance
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_account_balance -v 2

# Transaction status
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_transaction_status -v 2
```

### Advanced Features
```powershell
# Reversal
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_reversal -v 2

# Dynamic QR code
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_dynamic_qr_code -v 2

# C2B registration
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_register_c2b_urls -v 2
```

### Data Validation Tests
```powershell
# Phone formatting
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_phone_number_formatting -v 2

# Phone validation
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_phone_number_validation -v 2
```

### API Endpoint Tests
```powershell
# Payment initiation
python manage.py test test_ncba_comprehensive.MpesaAPIViewsTestCase.test_payment_initiation -v 2

# Payment status check
python manage.py test test_ncba_comprehensive.MpesaAPIViewsTestCase.test_payment_status_check -v 2

# NCBA payment processing
python manage.py test test_ncba_comprehensive.MpesaAPIViewsTestCase.test_ncba_payment_processing -v 2
```

### Integration Tests
```powershell
# Complete payment flow
python manage.py test test_ncba_comprehensive.MpesaIntegrationTestCase.test_complete_payment_flow -v 2
```

---

## 📊 Test Classes

Run entire test classes:

```powershell
# Service tests (20 tests)
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase -v 2

# API view tests (3 tests)
python manage.py test test_ncba_comprehensive.MpesaAPIViewsTestCase -v 2

# Integration tests (1 test)
python manage.py test test_ncba_comprehensive.MpesaIntegrationTestCase -v 2
```

---

## 🔧 Usage Examples in Code

### Get Access Token
```python
from orders.ncba_service import ncba_service

token = ncba_service.get_access_token()
print(f"Token: {token}")
```

### Initiate STK Push
```python
result = ncba_service.stk_push(
    phone_number='254712345678',
    amount=100,
    account_reference='ORD-001',
    transaction_desc='Payment for order'
)
print(f"Status: {result['ResponseCode']}")
print(f"Checkout ID: {result['CheckoutRequestID']}")
```

### Send B2C Payout
```python
result = ncba_service.b2c_payment(
    phone_number='254712345678',
    amount=1000,
    occasion='Salary',
    remarks='Monthly payment'
)
print(f"Status: {result['ResponseCode']}")
```

### Send B2B Payment
```python
result = ncba_service.b2b_payment(
    receiver_shortcode='600000',
    amount=5000,
    account_reference='B2B-001',
    remarks='Payment to supplier'
)
print(f"Status: {result['ResponseCode']}")
```

### Generate QR Code
```python
result = ncba_service.generate_dynamic_qr(
    amount=500,
    ref_no='QR-001',
    merchant_name='My Business'
)
print(f"QR Code: {result['QRCode']}")
```

### Reverse Transaction
```python
result = ncba_service.reversal(
    transaction_id='MLU0200009902',
    amount=1000,
    remarks='Customer refund'
)
print(f"Status: {result['ResponseCode']}")
```

### Format Phone Number
```python
phone = ncba_service.format_phone_number('0712345678')
print(f"Formatted: {phone}")  # Output: 254712345678
```

### Validate Phone Number
```python
is_valid = ncba_service.validate_phone_number('254712345678')
print(f"Valid: {is_valid}")  # Output: True
```

---

## 📋 Response Code Meanings

| Code | Meaning |
|------|---------|
| 0 | ✓ Success |
| 1 | ✗ Insufficient Funds |
| 2 | ✗ Less Than Minimum |
| 1001 | ✗ Unable to lock subscriber |
| 1002 | ✗ Subscriber not found |
| 1026 | ✗ Invalid pin |
| 1027 | ✗ PIN tries exceeded |
| 1031 | ✗ Transacting subscriber not found |

---

## 🛠 Environment Setup

### Install colorama (optional, for colored output)
```powershell
pip install colorama
```

### Verify your .env file has these keys:
```env
NCBA_ENVIRONMENT=production
NCBA_CONSUMER_KEY=your_key
NCBA_CONSUMER_SECRET=your_secret
NCBA_SHORTCODE=3573531
NCBA_PASSKEY=your_passkey
NCBA_B2C_SHORTCODE=600000
NCBA_B2C_INITIATOR_NAME=testapi
NCBA_B2C_SECURITY_CREDENTIAL=your_credential
```

---

## 📁 File Locations

```
c:\Users\a\Documents\GitHub\fagierrands\fagierrands\fagierrandsbackup\
├── test_ncba_comprehensive.py       # Full test suite
├── quick_test_ncba.py               # Quick tests
├── run_ncba_tests.ps1               # PowerShell launcher
├── run_ncba_tests.bat               # Batch launcher
├── NCBA_TESTS_README.md             # Overview
├── NCBA_TESTING_GUIDE.md            # Detailed guide
├── NCBA_QUICK_REFERENCE.md          # This file
└── orders/
    ├── ncba_service.py              # Service class
    └── views_payment_ncba.py        # API views
```

---

## 🎯 Quick Test Plan

### Day 1: Verify Setup
```powershell
# Run quick test
python quick_test_ncba.py

# Check if all 10 tests pass
```

### Day 2: Test Each Feature
```powershell
# STK Push
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_valid_phone -v 2

# B2C
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2c_payment -v 2

# Account Balance
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_account_balance -v 2
```

### Day 3: Run Full Suite
```powershell
# Complete test
python manage.py test test_ncba_comprehensive -v 2
```

---

## 🐛 If Something Goes Wrong

### Check logs
```powershell
# View debug log (if exists)
Get-Content debug.log -Tail 50
```

### Verify credentials
```powershell
# Check .env file exists
Test-Path .env

# View NCBA settings
python -c "from django.conf import settings; import os; os.environ['DJANGO_SETTINGS_MODULE']='fagierrandsbackup.settings'; from django.setup import setup; setup(); from django.conf import settings; print(settings.NCBA_SHORTCODE)"
```

### Test API connectivity
```python
import os
os.environ['DJANGO_SETTINGS_MODULE']='fagierrandsbackup.settings'
import django
django.setup()

from orders.ncba_service import ncba_service
try:
    token = ncba_service.get_access_token()
    print(f"✓ Connected: {token[:20]}...")
except Exception as e:
    print(f"✗ Error: {e}")
```

---

## 📞 Help

1. **Read:** NCBA_TESTS_README.md
2. **Reference:** NCBA_TESTING_GUIDE.md
3. **Run:** quick_test_ncba.py
4. **Check:** .env file configuration
5. **Monitor:** debug.log file

---

## ⏱ Estimated Times

| Test | Time |
|------|------|
| Quick Test | 2-3 min |
| Service Tests | 3-5 min |
| API Tests | 1-2 min |
| Full Suite | 5-10 min |

---

## ✅ Pre-Deployment Checklist

- [ ] All tests pass
- [ ] .env configured correctly
- [ ] Phone validation works
- [ ] STK Push works
- [ ] B2C payouts work
- [ ] Account balance updates
- [ ] Logs capture details
- [ ] Error handling works

---

**Last Updated:** 2025-01-22  
**Version:** 1.0  
**Ready to test!** 🚀