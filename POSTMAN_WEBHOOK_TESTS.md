# 🧪 Postman Webhook Testing Guide

## 📋 Postman Collection Setup

### Base Configuration
- **Method**: POST
- **URL**: `https://fagierrands-server.vercel.app/api/orders/payments/webhook/`
- **Headers**: 
  - `Content-Type: application/json`
  - `User-Agent: IntaSend-Webhook-Test`

## 🧪 Test Cases

### Test 1: Payment Completed ✅
**Purpose**: Test successful payment webhook

**Request Body**:
```json
{
  "event": "payment.completed",
  "data": {
    "invoice": {
      "id": "test-invoice-completed-123"
    },
    "mpesa_receipt": "TEST123456789",
    "amount": 100.00,
    "currency": "KES",
    "phone_number": "254700000000",
    "account": "Test Account"
  }
}
```

**Expected Response**:
- **Status Code**: `200 OK`
- **Response Body**: `{"status": "success"}`

**What This Tests**:
- ✅ Webhook endpoint accessibility
- ✅ Payment completion processing
- ✅ JSON payload parsing
- ✅ Response format

---

### Test 2: Payment Failed ❌
**Purpose**: Test failed payment webhook

**Request Body**:
```json
{
  "event": "payment.failed",
  "data": {
    "invoice": {
      "id": "test-invoice-failed-456"
    },
    "reason": "Insufficient funds",
    "amount": 50.00,
    "currency": "KES",
    "phone_number": "254700000000"
  }
}
```

**Expected Response**:
- **Status Code**: `200 OK`
- **Response Body**: `{"status": "success"}`

---

### Test 3: Payment Cancelled 🚫
**Purpose**: Test cancelled payment webhook

**Request Body**:
```json
{
  "event": "payment.cancelled",
  "data": {
    "invoice": {
      "id": "test-invoice-cancelled-789"
    },
    "reason": "User cancelled payment",
    "amount": 75.00,
    "currency": "KES",
    "phone_number": "254700000000"
  }
}
```

**Expected Response**:
- **Status Code**: `200 OK`
- **Response Body**: `{"status": "success"}`

---

### Test 4: Unknown Event Type 🤔
**Purpose**: Test handling of unknown webhook events

**Request Body**:
```json
{
  "event": "payment.unknown",
  "data": {
    "invoice": {
      "id": "test-invoice-unknown-999"
    },
    "some_field": "some_value"
  }
}
```

**Expected Response**:
- **Status Code**: `200 OK`
- **Response Body**: `{"status": "success"}`

---

### Test 5: Invalid JSON 💥
**Purpose**: Test error handling for malformed requests

**Request Body**:
```json
{
  "event": "payment.completed",
  "data": {
    "invoice": {
      // Missing closing bracket
    "amount": 100.00
  }
```

**Expected Response**:
- **Status Code**: `400 Bad Request` or `500 Internal Server Error`
- **Response Body**: Error message

---

### Test 6: Missing Required Fields 📝
**Purpose**: Test handling of incomplete webhook data

**Request Body**:
```json
{
  "event": "payment.completed",
  "data": {
    // Missing invoice field
    "amount": 100.00
  }
}
```

**Expected Response**:
- **Status Code**: `200 OK` (should handle gracefully)
- **Response Body**: `{"status": "success"}`

---

### Test 7: Real Payment Simulation 🎯
**Purpose**: Test with realistic IntaSend webhook payload

**Request Body**:
```json
{
  "event": "payment.completed",
  "data": {
    "invoice": {
      "id": "INV-2024-001234",
      "state": "COMPLETE",
      "provider": "M-PESA",
      "charges": 100.00,
      "net_amount": 97.00,
      "currency": "KES",
      "value": 100.00,
      "account": "254700000000",
      "api_ref": "12345678",
      "host": "https://payment.intasend.com",
      "failed_reason": null,
      "failed_code": null
    },
    "mpesa_receipt": "QGH7X8Y9Z0",
    "checkout_id": "checkout_123456",
    "tracking_id": "track_789012"
  }
}
```

**Expected Response**:
- **Status Code**: `200 OK`
- **Response Body**: `{"status": "success"}`

## 📊 Postman Collection JSON

Copy this into Postman as a collection:

```json
{
  "info": {
    "name": "IntaSend Webhook Tests",
    "description": "Test collection for IntaSend webhook endpoint",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Payment Completed",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "User-Agent",
            "value": "IntaSend-Webhook-Test"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"event\": \"payment.completed\",\n  \"data\": {\n    \"invoice\": {\n      \"id\": \"test-invoice-completed-123\"\n    },\n    \"mpesa_receipt\": \"TEST123456789\",\n    \"amount\": 100.00,\n    \"currency\": \"KES\",\n    \"phone_number\": \"254700000000\"\n  }\n}"
        },
        "url": {
          "raw": "https://fagierrands-server.vercel.app/api/orders/payments/webhook/",
          "protocol": "https",
          "host": ["fagierrands-server", "vercel", "app"],
          "path": ["api", "orders", "payments", "webhook", ""]
        }
      }
    },
    {
      "name": "Payment Failed",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "User-Agent",
            "value": "IntaSend-Webhook-Test"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"event\": \"payment.failed\",\n  \"data\": {\n    \"invoice\": {\n      \"id\": \"test-invoice-failed-456\"\n    },\n    \"reason\": \"Insufficient funds\",\n    \"amount\": 50.00,\n    \"currency\": \"KES\"\n  }\n}"
        },
        "url": {
          "raw": "https://fagierrands-server.vercel.app/api/orders/payments/webhook/",
          "protocol": "https",
          "host": ["fagierrands-server", "vercel", "app"],
          "path": ["api", "orders", "payments", "webhook", ""]
        }
      }
    },
    {
      "name": "Payment Cancelled",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "User-Agent",
            "value": "IntaSend-Webhook-Test"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"event\": \"payment.cancelled\",\n  \"data\": {\n    \"invoice\": {\n      \"id\": \"test-invoice-cancelled-789\"\n    },\n    \"reason\": \"User cancelled payment\",\n    \"amount\": 75.00,\n    \"currency\": \"KES\"\n  }\n}"
        },
        "url": {
          "raw": "https://fagierrands-server.vercel.app/api/orders/payments/webhook/",
          "protocol": "https",
          "host": ["fagierrands-server", "vercel", "app"],
          "path": ["api", "orders", "payments", "webhook", ""]
        }
      }
    }
  ]
}
```

## 🎯 Testing Steps

### Step 1: Import Collection
1. Open Postman
2. Click **Import**
3. Paste the JSON collection above
4. Click **Import**

### Step 2: Run Tests
1. Select **"Payment Completed"** request
2. Click **Send**
3. Verify response: `200 OK` with `{"status": "success"}`
4. Repeat for other test cases

### Step 3: Monitor Server Logs
While running tests, check for these log messages:
- ✅ `"Received IntaSend webhook: event=payment.completed"`
- ✅ `"Webhook processed successfully"`

## 🔍 What Each Test Validates

### ✅ Successful Tests Confirm:
- **Endpoint accessibility**: Server responds to requests
- **JSON parsing**: Handles webhook payloads correctly
- **Event processing**: Processes different event types
- **Error handling**: Gracefully handles invalid data
- **Response format**: Returns expected JSON response

### ❌ Failed Tests Indicate:
- **Server issues**: 500 errors suggest code problems
- **Network issues**: Timeout or connection errors
- **Configuration issues**: 404 errors suggest routing problems

## 📊 Expected Results Summary

| Test Case | Expected Status | Expected Response |
|-----------|----------------|-------------------|
| Payment Completed | 200 OK | `{"status": "success"}` |
| Payment Failed | 200 OK | `{"status": "success"}` |
| Payment Cancelled | 200 OK | `{"status": "success"}` |
| Unknown Event | 200 OK | `{"status": "success"}` |
| Invalid JSON | 400/500 | Error message |
| Missing Fields | 200 OK | `{"status": "success"}` |
| Real Simulation | 200 OK | `{"status": "success"}` |

## 🚨 Troubleshooting

### If Tests Fail:

**404 Not Found**:
- ❌ Wrong URL format
- ✅ Use: `https://fagierrands-server.vercel.app/api/orders/payments/webhook/`

**500 Internal Server Error**:
- ❌ Server code issue
- ✅ Check server logs for Python errors

**Timeout**:
- ❌ Server not responding
- ✅ Check server status

**Connection Refused**:
- ❌ Server down
- ✅ Verify server deployment

## 🎉 Success Indicators

Your webhook is working correctly if:
- ✅ All tests return `200 OK`
- ✅ Response body is `{"status": "success"}`
- ✅ Server logs show webhook receipt messages
- ✅ No errors in server logs

Once Postman tests pass, your webhook endpoint is ready for IntaSend configuration!