# IntaSend Webhook Configuration Guide

## Root Cause of Stuck Payments

The payments are getting stuck in "processing" status because **IntaSend webhooks are not properly configured** to notify our server when payment status changes occur.

## Current Status ✅

- **Webhook endpoint**: Working correctly (`/api/orders/payments/webhook/`)
- **Payment processing**: Working correctly (STK push successful)
- **Issue**: IntaSend is not sending webhook notifications to our server

## Required Configuration

### 1. IntaSend Dashboard Configuration

You need to configure webhooks in your IntaSend dashboard:

#### For Live Environment:
1. Login to: https://payment.intasend.com
2. Go to **Settings** → **Webhooks**
3. Add webhook URL: `https://fagierrands-server.vercel.app/api/orders/payments/webhook/`
4. Enable these events:
   - ✅ `payment.completed`
   - ✅ `payment.failed`
   - ✅ `payment.cancelled`

#### For Test Environment:
1. Login to: https://sandbox.intasend.com
2. Follow same steps as above

### 2. Webhook Events Explanation

| Event | Description | Action Taken |
|-------|-------------|--------------|
| `payment.completed` | Payment successful | Status → `completed`, Order → `completed` |
| `payment.failed` | Payment failed | Status → `failed` |
| `payment.cancelled` | Payment cancelled by user | Status → `cancelled` |

### 3. Webhook URL Format

**Correct URL**: `https://fagierrands-server.vercel.app/api/orders/payments/webhook/`

**Important Notes**:
- Must include `/api/` prefix
- Must end with `/`
- Must use HTTPS
- Must be accessible from internet

## Verification Steps

### 1. Test Webhook Delivery

After configuring webhooks in IntaSend dashboard:

1. Make a test payment
2. Check IntaSend dashboard → Webhooks → Delivery logs
3. Verify webhook was sent successfully
4. Check our server logs for webhook receipt

### 2. Manual Webhook Test

Run this command to test webhook endpoint:

```bash
python test_webhook_endpoint.py
```

### 3. Monitor Webhook Logs

Check server logs for webhook activity:
- Look for: "Received IntaSend webhook"
- Look for: "Payment X status updated"

## Current Configuration Status

✅ **Working**:
- Webhook endpoint accessible
- Webhook processing logic correct
- Payment creation working
- STK push working

❌ **Missing**:
- Webhook URL not configured in IntaSend dashboard
- Webhook events not enabled

## Immediate Actions Required

### 1. Configure IntaSend Webhooks (URGENT)
- Login to IntaSend dashboard
- Add webhook URL
- Enable payment events
- Test webhook delivery

### 2. Fix Current Stuck Payments
```bash
python fix_stuck_payments_now.py
```

### 3. Monitor Future Payments
- Check webhook logs
- Monitor payment status updates
- Verify automatic status changes

## Expected Results After Configuration

Once webhooks are properly configured:

1. **Payment Flow**:
   - User initiates payment → Status: `processing`
   - IntaSend processes payment → Webhook sent
   - Our server receives webhook → Status: `completed`/`failed`/`cancelled`

2. **No More Stuck Payments**:
   - Payments will automatically update status
   - No manual intervention needed
   - Real-time status updates

3. **Monitoring**:
   - Webhook logs will show activity
   - Payment status changes will be logged
   - Admin panel will show correct statuses

## Troubleshooting

### If Webhooks Still Don't Work

1. **Check IntaSend Dashboard**:
   - Verify webhook URL is correct
   - Check webhook delivery logs
   - Look for failed deliveries

2. **Check Server Logs**:
   - Look for webhook receipt logs
   - Check for processing errors
   - Verify payment updates

3. **Test Webhook Manually**:
   - Use IntaSend dashboard test feature
   - Send test webhook payload
   - Verify endpoint response

### Common Issues

| Issue | Solution |
|-------|----------|
| Webhook URL returns 404 | Check URL format, ensure `/api/` prefix |
| Webhook delivery fails | Check server accessibility, firewall settings |
| Payment not found | Verify `intasend_invoice_id` is saved correctly |
| Status not updating | Check webhook event types enabled |

## Monitoring and Maintenance

### 1. Regular Checks
- Monitor webhook delivery success rate
- Check for stuck payments daily
- Review webhook logs weekly

### 2. Automated Monitoring
- Set up Celery task to check stuck payments
- Configure alerts for webhook failures
- Monitor payment completion rates

### 3. Backup Solutions
- Manual payment status checking
- Automatic stuck payment fixing
- Admin panel bulk actions

## Contact Information

**IntaSend Support**:
- Email: support@intasend.com
- Dashboard: https://payment.intasend.com
- Documentation: https://developers.intasend.com

**Next Steps**:
1. ✅ Configure webhooks in IntaSend dashboard
2. ✅ Test webhook delivery
3. ✅ Fix current stuck payments
4. ✅ Monitor future payments

---

**Last Updated**: August 6, 2025  
**Status**: Configuration Required  
**Priority**: HIGH - Affects payment processing