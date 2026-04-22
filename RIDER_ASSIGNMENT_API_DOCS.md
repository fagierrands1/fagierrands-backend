# Finding Your Rider & Rider Found - API Documentation

## Overview

This feature implements the "Finding Your Rider" loading screen and "Rider Found" notification with rider details.

## Implementation Summary

### Database Changes
- ✅ Added `plate_number` field to `Profile` model for riders
- ✅ Migration created and applied: `accounts/migrations/0014_profile_plate_number.py`

### New Endpoints
- ✅ `GET /api/orders/{order_id}/rider-status/` - Get order rider status
- ✅ Enhanced `POST /api/orders/{order_id}/assign/` - Returns rider details after assignment

---

## API Endpoints

### 1. Get Order Rider Status (Client Side)

**Endpoint:** `GET /api/orders/{order_id}/rider-status/`

**Authentication:** Required (Client must be order owner)

**Description:** Returns the current status of rider assignment for an order.

#### Response Examples:

**A) Finding Rider Phase (Status: 'pending')**
```json
{
  "order_id": 12,
  "status": "pending",
  "rider_status": "finding_rider",
  "message": "Finding you a rider...",
  "elapsed_time": {
    "seconds": 45,
    "minutes": 0,
    "formatted": "0m 45s"
  },
  "max_wait_time_minutes": 5
}
```

**B) Rider Found Phase (Status: 'assigned')**
```json
{
  "order_id": 12,
  "status": "assigned",
  "rider_status": "rider_found",
  "message": "Rider found!",
  "rider": {
    "id": 5,
    "name": "Mike Rider",
    "phone_number": "+254712345678",
    "plate_number": "KCA 123X",
    "profile_picture": "https://example.com/profile.jpg"
  },
  "assigned_at": "2026-04-22T07:09:14.256793Z"
}
```

**C) Other Statuses**
```json
{
  "order_id": 12,
  "status": "in_progress",
  "rider_status": "in_progress",
  "message": "Order is In Progress"
}
```

---

### 2. Assign Rider (Handler Side)

**Endpoint:** `POST /api/orders/{order_id}/assign/`

**Authentication:** Required (Handler or Admin only)

**Description:** Assigns a rider to a pending order and returns rider details.

#### Request Body:
```json
{
  "assistant_id": 5
}
```

#### Response:
```json
{
  "message": "Rider assigned successfully",
  "order_id": 12,
  "status": "assigned",
  "rider": {
    "id": 5,
    "name": "Mike Rider",
    "phone_number": "+254712345678",
    "plate_number": "KCA 123X",
    "profile_picture": "https://example.com/profile.jpg"
  },
  "assigned_at": "2026-04-22T07:09:14.256793Z"
}
```

---

## Frontend Implementation Guide

### Client App Flow

#### 1. After Errand Confirmation

When client confirms errand (status becomes 'pending'), show "Finding Your Rider" screen:

```javascript
// Poll the rider status endpoint every 3-5 seconds
const checkRiderStatus = async (orderId) => {
  const response = await fetch(`/api/orders/${orderId}/rider-status/`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (data.rider_status === 'finding_rider') {
    // Show loading screen with message
    showFindingRiderScreen({
      message: data.message,
      elapsedTime: data.elapsed_time.formatted,
      maxWaitTime: data.max_wait_time_minutes
    });
  } else if (data.rider_status === 'rider_found') {
    // Show rider found screen with details
    showRiderFoundScreen({
      riderName: data.rider.name,
      riderPhone: data.rider.phone_number,
      riderPlate: data.rider.plate_number,
      riderPhoto: data.rider.profile_picture
    });
    
    // Stop polling
    clearInterval(pollingInterval);
  }
};

// Start polling
const pollingInterval = setInterval(() => {
  checkRiderStatus(orderId);
}, 3000); // Poll every 3 seconds
```

#### 2. UI Components

**Finding Rider Screen:**
```
┌─────────────────────────────────┐
│                                 │
│     [Loading Animation]         │
│                                 │
│   Finding you a rider...        │
│                                 │
│   Time elapsed: 0m 45s          │
│   Max wait: 5 minutes           │
│                                 │
└─────────────────────────────────┘
```

**Rider Found Screen:**
```
┌─────────────────────────────────┐
│                                 │
│     ✅ Rider Found!             │
│                                 │
│   [Rider Photo]                 │
│                                 │
│   Name: Mike Rider              │
│   Phone: +254712345678          │
│   Plate: KCA 123X               │
│                                 │
│   [Track Rider Button]          │
│                                 │
└─────────────────────────────────┘
```

### Handler App Flow

#### 1. View Pending Orders

```javascript
// Get pending orders
const response = await fetch('/api/orders/pending/', {
  headers: {
    'Authorization': `Bearer ${handlerToken}`
  }
});

const pendingOrders = await response.json();
```

#### 2. Assign Rider

```javascript
// Assign rider to order
const assignRider = async (orderId, riderId) => {
  const response = await fetch(`/api/orders/${orderId}/assign/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${handlerToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      assistant_id: riderId
    })
  });
  
  const result = await response.json();
  
  if (response.ok) {
    console.log('Rider assigned:', result.rider);
    // Show success message
    // Client will automatically see "Rider Found" screen
  }
};
```

---

## Testing

### Test Script
Run the test script to verify the complete flow:

```bash
python test_rider_assignment_flow.py
```

### Expected Output:
```
✅ Client confirms errand → Status: 'pending'
✅ Client sees 'Finding you a rider...' message
✅ Handler assigns rider → Status: 'assigned'
✅ Client sees 'Rider Found!' with rider details
```

---

## Time Constraint (5 Minutes)

The system tracks elapsed time from when the order becomes 'pending'. The frontend should:

1. Display elapsed time to the client
2. Show max wait time (5 minutes)
3. Optionally show a warning if approaching 5 minutes

**Note:** Backend does not enforce the 5-minute limit automatically. This is a business rule that handlers should follow. Future enhancement can add automatic alerts.

---

## Notes

1. **No Breaking Changes:** All changes are additive. Existing functionality remains intact.

2. **Rider Plate Number:** Handlers/Admins should ensure riders have their plate numbers set in their profiles.

3. **ETA Feature:** Not implemented yet. Will be added when rider tracking is implemented.

4. **Polling Frequency:** Recommended 3-5 seconds for good UX without overloading the server.

5. **Stop Polling:** Always stop polling once rider is found to save resources.

---

## Status Transitions

```
draft → pending → assigned → in_progress → completed
         ↑           ↑
    (Finding)   (Rider Found)
```

- **draft:** Errand being created
- **pending:** Errand confirmed, finding rider (max 5 min)
- **assigned:** Rider found and assigned
- **in_progress:** Rider started the errand
- **completed:** Errand completed

---

## Error Handling

### Client Side
```javascript
try {
  const data = await checkRiderStatus(orderId);
  // Handle response
} catch (error) {
  console.error('Error checking rider status:', error);
  // Show error message to user
  // Retry after a delay
}
```

### Handler Side
```javascript
try {
  const result = await assignRider(orderId, riderId);
  // Show success
} catch (error) {
  console.error('Error assigning rider:', error);
  // Show error message
  // Common errors:
  // - Order not pending
  // - Rider not available
  // - Deposit not paid (for shopping orders)
}
```

---

## Summary

✅ **Implemented:**
- Finding Your Rider status endpoint
- Rider Found with rider details
- Plate number field for riders
- Enhanced assignment endpoint

⏳ **Not Implemented (Future):**
- ETA calculation (requires rider tracking)
- Automatic 5-minute timeout alerts
- Real-time notifications (currently using polling)

🎯 **Ready for Frontend Integration**
