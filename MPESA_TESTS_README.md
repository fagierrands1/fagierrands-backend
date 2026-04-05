# NCBA Testing Suite - Complete Guide

Comprehensive testing suite for all NCBA Daraja API products in your account.

## 📋 What's Included

This testing suite includes:

### Test Files
1. **test_ncba_comprehensive.py** - Full Django test suite with 20+ test cases
2. **quick_test_ncba.py** - Standalone Python script for quick manual testing
3. **run_ncba_tests.bat** - Interactive batch script (Windows Command Prompt)
4. **run_ncba_tests.ps1** - Interactive PowerShell script
5. **NCBA_TESTING_GUIDE.md** - Detailed testing documentation

### Service Updates
- **ncba_service.py** - Enhanced with Reversal, Dynamic QR Code, and B2B methods

---

## 🚀 Quick Start

### Option 1: Quick Manual Test (Fastest)
```powershell
cd c:\Users\a\Documents\GitHub\fagierrands\fagierrands\fagierrandsbackup
python quick_test_ncba.py
```

This runs 10 quick tests and shows colored results instantly.

### Option 2: Interactive Menu (Recommended)
```powershell
# PowerShell
.\run_ncba_tests.ps1

# Command Prompt
run_ncba_tests.bat
```

### Option 3: Django Test Suite
```powershell
# All tests
python manage.py test test_ncba_comprehensive -v 2

# Specific test class
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase -v 2

# Specific test method
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_valid_phone -v 2
```

---

## 📦 File Structure

```
fagierrandsbackup/
├── test_ncba_comprehensive.py      # Main Django test suite
├── quick_test_ncba.py              # Quick standalone tests
├── run_ncba_tests.bat              # Batch script launcher
├── run_ncba_tests.ps1              # PowerShell script launcher
├── NCBA_TESTS_README.md            # This file
├── NCBA_TESTING_GUIDE.md           # Detailed guide
└── orders/
    ├── ncba_service.py             # Enhanced service (Reversal, QR, B2B added)
    └── views_payment_ncba.py       # Payment views
```

---

## 🧪 Test Categories

### Service Tests (20 tests)

#### Authentication (2 tests)
- ✓ OAuth token generation
- ✓ Token caching mechanism

#### STK Push - Lipa Na NCBA (4 tests)
- ✓ Valid phone number
- ✓ Invalid phone number handling
- ✓ Various payment amounts
- ✓ Transaction status query

#### C2B - Customer to Business (1 test)
- ✓ URL registration

#### B2C - Business to Customer (2 tests)
- ✓ Single payout
- ✓ Multiple payouts

#### B2B - Business to Business (2 tests)
- ✓ Basic B2B payment
- ✓ Different identifier types (shortcode, till)

#### Transaction Management (3 tests)
- ✓ Transaction status query
- ✓ Account balance query
- ✓ Transaction reversal

#### Advanced Features (1 test)
- ✓ Dynamic QR code generation

#### Data Validation (2 tests)
- ✓ Phone number formatting
- ✓ Phone number validation

### API Tests (3 tests)

#### Payment Endpoints (3 tests)
- ✓ Payment initiation
- ✓ Payment status check
- ✓ NCBA payment processing

### Integration Tests (1 test)

#### Complete Flow (1 test)
- ✓ End-to-end payment workflow

---

## 🎯 Available NCBA Products Tested

✅ **Lipa Na NCBA** (STK Push)  
   - Initiate customer payment prompts
   - Query transaction status

✅ **C2B v2** (Customer to Business)  
   - Register validation URLs
   - Handle incoming payments

✅ **B2C** (Business to Customer)  
   - Send payouts to customers
   - Multiple payout scenarios

✅ **B2B** (Business to Business)  
   - Send payments between businesses
   - Support for shortcodes and till numbers

✅ **Transaction Status**  
   - Query transaction status
   - Verify payment completion

✅ **Account Balance**  
   - Check current account balance
   - Monitor account status

✅ **Reversal**  
   - Reverse completed transactions
   - Handle payment reversals

✅ **Dynamic QR Code**  
   - Generate QR codes for payments
   - Support for various transaction types

---

## 📊 New Methods Added to ncba_service.py

### 1. Reversal
```python
result = ncba_service.reversal(
    transaction_id='MLU0200009902',
    amount=1000,
    remarks='Transaction reversal'
)
```

### 2. Dynamic QR Code
```python
result = ncba_service.generate_dynamic_qr(
    amount=500,
    ref_no='QR-001',
    merchant_name='Test Merchant'
)
```

### 3. B2B Payment
```python
result = ncba_service.b2b_payment(
    receiver_shortcode='600000',
    amount=5000,
    account_reference='B2B-001',
    remarks='Inter-business payment',
    identifier_type='4'  # 4=shortcode, 2=till, 1=MSISDN
)
```

---

## 🔧 Running Tests

### Method 1: Quick Test (Recommended for first run)
```powershell
python quick_test_ncba.py
```
**Time:** ~2-3 minutes  
**Output:** Colored console output with pass/fail for each test

### Method 2: Interactive Menu
```powershell
.\run_ncba_tests.ps1
```
**Features:** 
- Select specific tests
- View testing guide
- Run full or partial suite

### Method 3: Django Test Suite (Full)
```powershell
python manage.py test test_ncba_comprehensive -v 2
```
**Time:** ~5-10 minutes  
**Output:** Detailed Django test framework output

### Method 4: Specific Test
```powershell
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_valid_phone -v 2
```

---

## 📈 Test Results Interpretation

### Success Indicators
- **Response Code 0**: Success ✓
- **Customer message received**: Payment prompt sent ✓
- **Callback URL called**: Webhook fired ✓

### Common Response Codes
| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Transaction initiated |
| 1 | Insufficient Funds | Check account balance |
| 2 | Less Than Minimum | Use higher amount |
| Other | API Error | Check logs for details |

---

## 🛠 Dependencies

### Required
- Django 4.x+
- Python 3.8+
- requests
- djangorestframework

### Optional (for colored output)
```powershell
pip install colorama
```

If colorama is not installed, quick_test_ncba.py will still work but without colored output.

---

## 🔐 Configuration

Make sure your `.env` file has:

```env
# NCBA Environment
NCBA_ENVIRONMENT=production

# API Credentials
NCBA_CONSUMER_KEY=your_key
NCBA_CONSUMER_SECRET=your_secret

# Shortcode & Passkey
NCBA_SHORTCODE=3573531
NCBA_PASSKEY=your_passkey

# B2C Configuration
NCBA_B2C_SHORTCODE=600000
NCBA_B2C_INITIATOR_NAME=testapi
NCBA_B2C_SECURITY_CREDENTIAL=your_credential

# Callback URLs
NCBA_STK_CALLBACK_URL=https://your-domain.com/api/ncba/stk/callback/
NCBA_C2B_VALIDATION_URL=https://your-domain.com/api/ncba/c2b/validation/
NCBA_C2B_CONFIRMATION_URL=https://your-domain.com/api/ncba/c2b/confirmation/
NCBA_B2C_RESULT_URL=https://your-domain.com/api/ncba/b2c/result/
NCBA_B2C_TIMEOUT_URL=https://your-domain.com/api/ncba/b2c/timeout/
```

---

## 📋 Test Checklist

Use this checklist to ensure all features are tested:

- [ ] Authentication works (token generation)
- [ ] STK Push initiates successfully
- [ ] Phone number validation works
- [ ] STK Query returns status
- [ ] C2B URLs register
- [ ] B2C payouts work
- [ ] B2B payments work
- [ ] Account balance queries
- [ ] Transaction reversals work
- [ ] Dynamic QR codes generate
- [ ] Payment flow end-to-end
- [ ] Error handling works
- [ ] Logging is captured

---

## 🐛 Troubleshooting

### Issue: "No module named colorama"
**Solution:**
```powershell
pip install colorama
```
Or the script will work without colors.

### Issue: "Invalid credentials"
**Solution:**
- Verify NCBA_CONSUMER_KEY and NCBA_CONSUMER_SECRET
- Check NCBA portal for active credentials
- Ensure environment is set correctly (production/sandbox)

### Issue: "Test takes too long"
**Use quick_test_ncba.py instead of Django test suite**

### Issue: "Phone validation fails"
**Check format:**
- Must be 254XXXXXXXXX
- Must start with 2547 or 2541
- Must be 12 digits total

### Issue: "Transaction status returns error"
**This is expected** - You need an actual transaction ID from the system

---

## 📚 Documentation Files

1. **NCBA_TESTS_README.md** (this file) - Overview and quick start
2. **NCBA_TESTING_GUIDE.md** - Detailed testing documentation
3. **test_ncba_comprehensive.py** - Full test code with comments
4. **quick_test_ncba.py** - Quick test code with examples

---

## 🚀 Next Steps

1. **Run quick test first:**
   ```powershell
   python quick_test_ncba.py
   ```

2. **Review NCBA_TESTING_GUIDE.md** for detailed information

3. **Run specific tests** based on what you need to verify

4. **Monitor logs** in `debug.log` for detailed output

5. **Check NCBA portal** for transaction confirmations

---

## 📞 Support

For issues:

1. Check the log files (debug.log)
2. Review NCBA_TESTING_GUIDE.md
3. Verify .env configuration
4. Check NCBA portal for account status
5. Review response codes in documentation

---

## 📝 Version Info

- **Test Suite Version:** 1.0
- **Last Updated:** 2025-01-22
- **Compatible With:** Django 4.x+, Python 3.8+
- **NCBA API:** Daraja v1

---

## 🎓 Learning Path

1. **Day 1:** Run quick_test_ncba.py
2. **Day 2:** Read NCBA_TESTING_GUIDE.md
3. **Day 3:** Run specific test classes
4. **Day 4:** Run full test suite
5. **Day 5:** Integrate into your application

---

## ✅ Validation Checklist

Before deployment, verify:

- [ ] All tests pass
- [ ] Phone numbers validate correctly
- [ ] STK Push works with real phones
- [ ] Callbacks are received
- [ ] Payment status updates work
- [ ] B2C payouts succeed
- [ ] B2B transfers work
- [ ] Account balance updates
- [ ] Error handling works
- [ ] Logging captures all details

---

**Happy Testing! 🎉**

For detailed technical information, see NCBA_TESTING_GUIDE.md