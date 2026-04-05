# Payment Integration with IntaSend

This document outlines the payment integration with IntaSend for the Fagierrands application.

## Overview

The application uses IntaSend as the payment gateway to process M-Pesa and card payments. IntaSend provides a simple API for integrating payments into your application.

## Configuration

The following settings are required in the `settings.py` file:

```python
# IntaSend settings
INTASEND_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY', 'ISPubKey_test_your-publishable-key')
INTASEND_SECRET_KEY = os.environ.get('INTASEND_SECRET_KEY', 'ISSecretKey_test_your-secret-key')
INTASEND_TEST_MODE = os.environ.get('INTASEND_TEST_MODE', 'True') == 'True'
```

## Payment Flow

1. **Initiate Payment**: The client initiates a payment for a completed order.
2. **Process Payment**: The payment is processed through IntaSend based on the selected payment method (M-Pesa or card).
3. **Payment Callback**: IntaSend redirects the user back to the application after the payment is completed.
4. **Payment Webhook**: IntaSend sends a webhook notification to the application when the payment status changes.

## API Endpoints

- `POST /api/orders/payments/initiate/`: Initiate a payment for a completed order.
- `GET /api/orders/payments/<int:pk>/`: Get the status of a payment.
- `POST /api/orders/payments/<int:payment_id>/process/`: Process a payment through IntaSend.
- `GET /api/orders/payments/callback/`: Handle payment callbacks from IntaSend.
- `POST /api/orders/payments/webhook/`: Handle payment webhooks from IntaSend.

## Payment Methods

### M-Pesa

M-Pesa payments are processed using the IntaSend M-Pesa STK Push API. The user receives a prompt on their phone to enter their M-Pesa PIN to complete the payment.

### Card

Card payments are processed using the IntaSend Checkout API. The user is redirected to the IntaSend checkout page to enter their card details.

## Dependencies

- `intasend-python`: The official Python SDK for IntaSend Payment Gateway.

## Installation

```bash
pip install intasend-python
```

## Usage

```python
from intasend import APIService

# Initialize IntaSend API service
api_service = APIService(
    token=INTASEND_SECRET_KEY,
    publishable_key=INTASEND_PUBLISHABLE_KEY,
    test=INTASEND_TEST_MODE
)

# Trigger M-Pesa STK Push
response = api_service.collect.mpesa_stk_push(
    phone_number='254712345678',
    email='customer@example.com',
    amount=1000,
    narrative='Payment for Order #123'
)

# Create a checkout link for card payment
response = api_service.collect.checkout({
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'customer@example.com',
    'amount': 1000,
    'currency': 'KES',
    'phone_number': '254712345678',
    'reference': 'ORDER-123',
    'comment': 'Payment for Order #123',
    'redirect_url': 'https://example.com/payment/callback'
})
```

## Testing

To test the payment integration, you can use the IntaSend test credentials and test mode. In test mode, no actual payments are processed.

## Production

For production, you need to set the following environment variables:

```
INTASEND_PUBLISHABLE_KEY=your-production-publishable-key
INTASEND_SECRET_KEY=your-production-secret-key
INTASEND_TEST_MODE=False
```

## Troubleshooting

If you encounter any issues with the payment integration, check the following:

1. Ensure that the IntaSend credentials are correct.
2. Check that the phone number format is correct for M-Pesa payments (should start with 254).
3. Verify that the webhook URL is accessible from the internet.
4. Check the IntaSend dashboard for payment status and logs.