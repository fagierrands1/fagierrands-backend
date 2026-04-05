# NCBA Daraja API Testing Guide

Complete testing suite for all NCBA API products available in your account.

## Available NCBA Products

✓ **Lipa Na NCBA** (STK Push) - Customer payment initiation  
✓ **C2B v2** - Customer-to-Business payment registration  
✓ **B2C** - Business-to-Customer payouts  
✓ **B2B** - Business-to-Business payments  
✓ **Transaction Status** - Query transaction status  
✓ **Account Balance** - Check account balance  
✓ **Reversal** - Reverse completed transactions  
✓ **Dynamic QR Code** - Generate QR codes for payments  

---

## Quick Start

### 1. Run All NCBA Tests
```bash
cd c:\Users\a\Documents\GitHub\fagierrands\fagierrands\fagierrandsbackup
python manage.py test test_ncba_comprehensive
```

### 2. Run Specific Test Class
```bash
# Test NCBA Service Methods
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase

# Test NCBA API Views
python manage.py test test_ncba_comprehensive.MpesaAPIViewsTestCase

# Test Complete Payment Flow
python manage.py test test_ncba_comprehensive.MpesaIntegrationTestCase
```

### 3. Run Specific Test Method
```bash
# Test STK Push
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_valid_phone

# Test Account Balance
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_account_balance

# Test B2C Payment
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2c_payment

# Test B2B Payment
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_b2b_payment
```

### 4. Run with Verbose Output
```bash
python manage.py test test_ncba_comprehensive -v 2
```

---

## Test Categories & What They Cover

### ✓ Authentication Tests
- **test_get_access_token**: Verify OAuth token generation
- **test_token_caching**: Test token caching mechanism (55 minutes)

### ✓ STK Push Tests (Lipa Na NCBA)
- **test_stk_push_with_valid_phone**: Basic STK Push with valid number
- **test_stk_push_with_invalid_phone**: Error handling for invalid phones
- **test_stk_push_different_amounts**: Test various payment amounts
- **test_stk_query**: Query STK transaction status

### ✓ C2B Tests
- **test_register_c2b_urls**: Register Customer-to-Business URLs

### ✓ B2C Tests (Business to Customer - Payouts)
- **test_b2c_payment**: Single payout test
- **test_b2c_multiple_payouts**: Multiple payout scenarios

### ✓ B2B Tests (Business to Business)
- **test_b2b_payment**: Basic B2B payment
- **test_b2b_with_different_identifiers**: Test shortcode and till number identifiers

### ✓ Transaction Management
- **test_transaction_status**: Query transaction status
- **test_account_balance**: Check NCBA account balance
- **test_reversal**: Reverse a completed transaction

### ✓ Advanced Features
- **test_dynamic_qr_code**: Generate QR codes for payments

### ✓ Data Validation
- **test_phone_number_formatting**: Verify phone number formatting
- **test_phone_number_validation**: Validate Kenyan phone numbers

### ✓ API Endpoint Tests
- **test_payment_initiation**: Test payment creation endpoint
- **test_payment_status_check**: Test payment status endpoint
- **test_ncba_payment_processing**: Test NCBA processing endpoint

### ✓ Integration Tests
- **test_complete_payment_flow**: End-to-end payment flow

---

## Configuration

Your NCBA settings in `.env`:

```env
# NCBA Environment
NCBA_ENVIRONMENT=production

# API Credentials
NCBA_CONSUMER_KEY=your_consumer_key
NCBA_CONSUMER_SECRET=your_consumer_secret

# Shortcode & Passkey
NCBA_SHORTCODE=3573531
NCBA_PASSKEY=041610a7c512aba505a3b91153a923a5a167e74fda639bf4f186d0dc930cf81d

# B2C Configuration (for payouts)
NCBA_B2C_SHORTCODE=600000
NCBA_B2C_INITIATOR_NAME=testapi
NCBA_B2C_SECURITY_CREDENTIAL=your_security_credential
```

---

## Available API Methods

### Core Service Methods in `ncba_service.py`

```python
# Authentication
ncba_service.get_access_token()

# STK Push (Lipa Na NCBA)
ncba_service.stk_push(
    phone_number='254712345678',
    amount=100,
    account_reference='ORD-001',
    transaction_desc='Payment for order'
)

# STK Query
ncba_service.stk_query(checkout_request_id='WSF61BV61ZSSD')

# Customer to Business
ncba_service.register_c2b_urls()

# Business to Customer (Payouts)
ncba_service.b2c_payment(
    phone_number='254712345678',
    amount=1000,
    occasion='Salary',
    remarks='Monthly salary'
)

# Business to Business
ncba_service.b2b_payment(
    receiver_shortcode='600000',
    amount=5000,
    account_reference='B2B-001',
    remarks='Inter-business payment'
)

# Transaction Status
ncba_service.transaction_status(transaction_id='MLU0200009902')

# Account Balance
ncba_service.account_balance()

# Reversal
ncba_service.reversal(
    transaction_id='MLU0200009902',
    amount=1000,
    remarks='Transaction reversal'
)

# Dynamic QR Code
ncba_service.generate_dynamic_qr(
    amount=500,
    ref_no='QR-001',
    merchant_name='Test Merchant'
)

# Phone Utilities
ncba_service.format_phone_number('0712345678')      # Returns: 254712345678
ncba_service.validate_phone_number('254712345678')  # Returns: True/False
```

---

## Test Results Interpretation

### Response Codes
- **0**: Success - transaction initiated successfully
- **1**: Insufficient Funds - account balance insufficient
- **2**: Less Than Minimum Transaction Value - amount too small
- **Other**: Specific error from NCBA API

### Common Responses

**Success Response (STK Push):**
```json
{
    "MerchantRequestID": "123456",
    "CheckoutRequestID": "ws_CO_123456",
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CustomerMessage": "Please enter NCBA PIN"
}
```

**Error Response:**
```json
{
    "ResponseCode": "1",
    "ResponseDescription": "Insufficient funds",
    "error": "Insufficient funds"
}
```

---

## Debugging & Troubleshooting

### Enable Debug Logging
```python
# In your settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'orders': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Common Issues

**Issue: "No access token in response"**
- Check your consumer key and secret
- Verify the environment is set to 'production' or 'sandbox'

**Issue: "Invalid phone number format"**
- Phone must be in format 254XXXXXXXXX
- Can't have leading 0 or +254

**Issue: "NCBA authentication failed"**
- Verify API credentials in .env
- Check API consumer credentials are still valid

**Issue: "Security credential error"**
- B2C_SECURITY_CREDENTIAL needs to be encrypted properly
- Generate new credentials from NCBA portal if needed

---

## Production Testing Best Practices

1. **Test with Small Amounts**
   - Use amounts like 1, 5, 10 KES for initial tests
   - Test with various amounts: 1, 50, 100, 500, 1000

2. **Phone Number Testing**
   - Use test phone numbers from Safaricom
   - Verify both MSISDN (2547) and Airtel (2541) formats

3. **Error Scenarios**
   - Test with expired tokens
   - Test with insufficient funds
   - Test with invalid phone numbers
   - Test with invalid shortcodes

4. **Logging & Monitoring**
   - Always check logs for transaction details
   - Monitor callback responses
   - Track transaction IDs for reconciliation

5. **Rate Limiting**
   - NCBA API has rate limits
   - Don't send too many requests in quick succession
   - Implement exponential backoff for retries

---

## Integration with Django Models

### Payment Model Integration
```python
from orders.models import Payment

# Create payment from STK result
payment = Payment.objects.create(
    order=order,
    client=user,
    amount=100,
    phone_number='254712345678',
    payment_method='ncba',
    status='processing'
)

# Store NCBA references
payment.ncba_checkout_request_id = response['CheckoutRequestID']
payment.ncba_merchant_request_id = response['MerchantRequestID']
payment.save()
```

### Webhook Handling
```python
# Callback URL receives STK result
# Process callback to update payment status
# Update order status based on payment completion
```

---

## Additional Resources

- **NCBA Daraja API**: https://developer.safaricom.co.ke/
- **API Documentation**: https://developer.safaricom.co.ke/docs
- **Test Credentials**: Available from NCBA portal
- **Support**: Contact Safaricom developer support

---

## Quick Reference Commands

```bash
# Run tests
python manage.py test test_ncba_comprehensive

# Run specific test
python manage.py test test_ncba_comprehensive.MpesaServiceTestCase.test_stk_push_with_valid_phone

# Run with verbose output
python manage.py test test_ncba_comprehensive -v 2

# Generate test coverage report
coverage run --source='orders' manage.py test test_ncba_comprehensive
coverage report

# Generate HTML coverage report
coverage html
```

---

## Support & Debugging

For issues or questions:

1. Check the logs in `debug.log`
2. Verify `.env` configuration
3. Test with curl commands to isolate API issues
4. Check NCBA portal for account status
5. Verify callback URLs are accessible from public internet

---

Last Updated: 2025-01-22  
Test Suite Version: 1.0  
Tested With: Django 4.x, Python 3.8+