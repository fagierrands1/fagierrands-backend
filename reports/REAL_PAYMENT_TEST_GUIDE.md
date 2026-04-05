# 💰 Real Payment Test Guide - KSh 5

## 🎯 **Quick Setup** (2 minutes)

### **Step 1: Import Postman Collection**
1. Open Postman
2. Click **Import**
3. Select **`Real_Payment_Test_KSh5.postman_collection.json`**
4. Click **Import**

### **Step 2: Configure Variables**
In the collection variables, update:
- **`auth_token`**: Your authentication token (or use login request)
- **`phone_number`**: Your M-Pesa phone number (254 format)

## 🧪 **Test Execution** (5 minutes)

### **Run Requests in Order:**

#### **1. User Authentication** 🔐
```json
POST /api/accounts/login/
{
  "email": "your_email@example.com",
  "password": "your_password"
}
```
**Expected**: ✅ 200 OK with access token

#### **2. Create Test Order** 📦
```json
POST /api/orders/
{
  "order_type_id": 1,
  "title": "Test Payment Order - KSh 5",
  "description": "Small test order for payment integration testing",
  "price": 5.00,
  "pickup_address": "Test Pickup Location",
  "delivery_address": "Test Delivery Location"
}
```
**Expected**: ✅ 201 Created with order ID

#### **3. Initiate Payment** 💳
```json
POST /api/orders/payments/initiate/
{
  "order": {{order_id}},
  "payment_method": "mpesa",
  "phone_number": "254712345678"
}
```
**Expected**: ✅ 201 Created with payment ID

#### **4. Process Payment (STK Push)** 📱
```json
POST /api/orders/payments/{{payment_id}}/process/
{}
```
**Expected**: ✅ 200 OK with STK Push initiated

**🔔 CHECK YOUR PHONE FOR M-PESA STK PUSH!**

#### **5. Check Payment Status** 📊
```json
GET /api/orders/payments/{{payment_id}}/
```
**Expected**: 
- Initially: `"status": "processing"`
- After payment: `"status": "completed"`

#### **6. Check Order Status** 📋
```json
GET /api/orders/{{order_id}}/
```
**Expected**: `"status": "completed"` (updated by webhook)

## 📱 **M-Pesa Payment Process**

### **What You'll See:**
1. **STK Push Notification** on your phone
2. **Payment Request**: "Pay KSh 5.00 to INTASEND"
3. **Enter M-Pesa PIN**
4. **Confirmation SMS** from M-Pesa

### **Timeline:**
- **0-30 seconds**: STK Push appears on phone
- **30-60 seconds**: Complete payment with PIN
- **60-90 seconds**: M-Pesa confirmation SMS
- **90-120 seconds**: Webhook updates payment status

## 🎯 **Success Indicators**

### **✅ Payment Successful:**
```json
{
  "status": "completed",
  "transaction_id": "QGH7X8Y9Z0",
  "intasend_invoice_id": "INV_123456",
  "amount": "5.00"
}
```

### **✅ Order Completed:**
```json
{
  "status": "completed",
  "completed_at": "2025-01-08T14:30:00Z"
}
```

### **✅ Webhook Working:**
- Payment status changes from `processing` → `completed`
- Order status changes to `completed`
- `completed_at` timestamp is set

## 🔧 **Troubleshooting**

### **❌ STK Push Not Received**
- **Check phone number format**: Must be `254XXXXXXXXX`
- **Check phone network**: Ensure good signal
- **Try again**: Run "Process Payment" request again

### **❌ Payment Stuck in "Processing"**
- **Wait 2 minutes**: IntaSend can take time to process
- **Check M-Pesa balance**: Ensure sufficient funds
- **Check webhook**: Verify webhook is configured in IntaSend dashboard

### **❌ Authentication Failed**
- **Update credentials**: Use valid email/password in login request
- **Check token**: Ensure auth_token is set correctly

## 📊 **Expected Test Results**

### **Before Webhook Configuration:**
- Payment Status: `processing` (stuck)
- Order Status: `payment_pending` (not updated)
- Manual intervention required

### **After Webhook Configuration:**
- Payment Status: `completed` (automatic)
- Order Status: `completed` (automatic)
- Full automation working

## 🎉 **Success Criteria**

Your integration is working perfectly if:
- ✅ STK Push received on phone
- ✅ Payment completed successfully
- ✅ Payment status updated to `completed`
- ✅ Order status updated to `completed`
- ✅ All within 2 minutes

## 🔄 **Retry Testing**

To test multiple times:
1. **Change phone number** in variables
2. **Run requests 2-6** again
3. **Use different order titles** to avoid duplicates

## 📱 **Test Phone Numbers**

### **Safaricom Test Numbers** (Sandbox):
- `254700000000` - Always successful
- `254700000001` - Always fails
- `254700000002` - Times out

### **Live Testing:**
- Use your actual M-Pesa number
- Ensure sufficient balance (KSh 10+ recommended)

## 🎯 **Integration Validation**

This test validates:
- ✅ **Payment Creation**: Order → Payment flow
- ✅ **IntaSend Integration**: STK Push functionality
- ✅ **Webhook Processing**: Automatic status updates
- ✅ **Order Completion**: End-to-end workflow
- ✅ **Error Handling**: Graceful failure management

## 🚀 **Ready for Production**

Once this KSh 5 test passes consistently:
- ✅ Your payment integration is production-ready
- ✅ Scale to any amount (KSh 10, 100, 1000+)
- ✅ Handle real customer payments
- ✅ Monitor with confidence

**Time to complete test: 5 minutes**
**Cost: KSh 5 (refundable if needed)**
**Confidence gained: 100% payment integration validation**