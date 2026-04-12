# 2-Step Errand Placement Flow (Normal Errands)

## Overview
This is a streamlined 2-step process for placing normal errands (Pickup & Delivery). The flow separates price calculation from order creation and uses a DRAFT → PENDING status transition.

---

## 📱 User Flow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: CREATE DRAFT ERRAND                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │  User fills:                                        │     │
│  │  • Order type (dropdown)                            │     │
│  │  • Pickup location (map/typing)                     │     │
│  │  • Delivery location (map/typing)                   │     │
│  │  • Distance (auto-calculated)                       │     │
│  │  • Title & Description                              │     │
│  │                                                     │     │
│  │  💰 PRICE BREAKDOWN (same page):                   │     │
│  │  Base Fee: KSh 200 (first 7km)                     │     │
│  │  Distance Fee: KSh 40 (2km extra @ KSh 20/km)      │     │
│  │  ─────────────────────                              │     │
│  │  Total: KSh 240                                     │     │
│  │                                                     │     │
│  │  [Next] →                                           │     │
│  └────────────────────────────────────────────────────┘     │
│                         ↓                                    │
│  🔄 POST /api/orders/errands/draft/                         │
│  ✅ Response: { order_id: 123, status: "draft" }            │
│  ⚠️  Status: DRAFT (not visible to riders yet)             │
└─────────────────────────────────────────────────────────────┘

                         ↓

┌─────────────────────────────────────────────────────────────┐
│  STEP 2: COMPLETE & CONFIRM                                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │  User adds:                                         │     │
│  │  • Upload images (proof/reference)                  │     │
│  │  • Estimated value of items                         │     │
│  │  • Receiver name                                    │     │
│  │  • Receiver contact number                          │     │
│  │                                                     │     │
│  │  📋 Order Summary:                                  │     │
│  │  From: Westlands                                    │     │
│  │  To: CBD                                            │     │
│  │  Price: KSh 240                                     │     │
│  │  Images: 2 uploaded                                 │     │
│  │                                                     │     │
│  │  [Confirm Order] 🚀                                 │     │
│  └────────────────────────────────────────────────────┘     │
│                         ↓                                    │
│  🔄 POST /api/orders/errands/123/confirm/                   │
│  ✅ Response: { status: "pending" }                         │
│  📱 SMS sent to client ✅                                    │
│  🔔 Notification sent ✅                                     │
│  👀 Now visible to riders ✅                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 API Endpoints

### Optional: Calculate Price (Before Creating Draft)
If you want to show price before creating the draft:

```
POST /api/orders/errands/calculate-price/
```

**Request:**
```json
{
  "order_type_id": 1,
  "distance": 9.0
}
```

**Response:**
```json
{
  "order_type": "Pickup & Delivery",
  "pricing_breakdown": {
    "base_fee": 200.0,
    "distance_fee": 40.0,
    "total": 240.0,
    "distance_km": 9.0
  },
  "calculation_note": "Base fee KSh 200 for first 7km, KSh 20/km thereafter"
}
```

---

### Step 1: Create Draft Errand

```
POST /api/orders/errands/draft/
```

**Request:**
```json
{
  "order_type_id": 1,
  "title": "Deliver laptop to client",
  "description": "Dell laptop in black bag",
  "pickup_address": "Westlands, Nairobi",
  "delivery_address": "CBD, Nairobi",
  "pickup_latitude": -1.2634,
  "pickup_longitude": 36.8078,
  "delivery_latitude": -1.2864,
  "delivery_longitude": 36.8172,
  "distance": 9.0
}
```

**Response:**
```json
{
  "order_id": 123,
  "status": "draft",
  "pricing_breakdown": {
    "base_fee": 200.0,
    "distance_fee": 40.0,
    "total": 240.0,
    "distance_km": 9.0
  },
  "order": {
    "id": 123,
    "title": "Deliver laptop to client",
    "pickup_address": "Westlands, Nairobi",
    "delivery_address": "CBD, Nairobi",
    "price": 240.0,
    "status": "draft",
    "created_at": "2026-04-12T20:00:00Z"
  },
  "next_step": "Upload images and add receiver contact info"
}
```

---

### Step 2a: Upload Images

```
POST /api/orders/errands/{order_id}/upload-image/
```

**Request (multipart/form-data):**
- `image`: File (required)
- `caption`: String (optional)

**Response:**
```json
{
  "image_id": 456,
  "image": {
    "id": 456,
    "image_url": "https://example.com/media/orders/image.jpg",
    "description": "Laptop in bag",
    "uploaded_at": "2026-04-12T20:05:00Z"
  },
  "total_images": 2
}
```

---

### Step 2b: Update Receiver Info

```
POST /api/orders/errands/{order_id}/receiver-info/
```

**Request:**
```json
{
  "recipient_name": "John Doe",
  "contact_number": "+254712345678",
  "estimated_value": 50000
}
```

**Response:**
```json
{
  "message": "Receiver info updated",
  "order": {
    "id": 123,
    "recipient_name": "John Doe",
    "contact_number": "+254712345678",
    "estimated_value": 50000.0
  }
}
```

---

### Step 2c: Confirm Errand

```
POST /api/orders/errands/{order_id}/confirm/
```

**Response:**
```json
{
  "message": "Errand confirmed successfully!",
  "order_id": 123,
  "status": "pending",
  "order": {
    "id": 123,
    "status": "pending",
    "price": 240.0,
    "pickup_address": "Westlands, Nairobi",
    "delivery_address": "CBD, Nairobi",
    "recipient_name": "John Doe",
    "contact_number": "+254712345678"
  },
  "notifications_sent": true
}
```

**What happens:**
- Status changes from `draft` → `pending`
- SMS sent to client
- Push notification sent
- Order becomes visible to riders
- Can now be assigned to a rider

---

## 📱 Additional Endpoints

### Get Draft Errand

```
GET /api/orders/errands/{order_id}/
```

**Response:**
```json
{
  "order": {
    "id": 123,
    "status": "draft",
    "title": "Deliver laptop to client",
    "price": 240.0
  },
  "images_count": 2,
  "can_confirm": true
}
```

---

### Delete Draft Errand

```
DELETE /api/orders/errands/{order_id}/delete/
```

**Response:**
```json
{
  "message": "Draft errand deleted successfully"
}
```

---

## 💡 Frontend Implementation

### React/React Native Example

```javascript
import { useState } from 'react';

// STEP 1: Create Draft
const handleCreateDraft = async () => {
  const response = await fetch('/api/orders/errands/draft/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      order_type_id: formData.orderTypeId,
      title: formData.title,
      description: formData.description,
      pickup_address: formData.pickupAddress,
      delivery_address: formData.deliveryAddress,
      pickup_latitude: formData.pickupLat,
      pickup_longitude: formData.pickupLng,
      delivery_latitude: formData.deliveryLat,
      delivery_longitude: formData.deliveryLng,
      distance: formData.distance
    })
  });
  
  const draft = await response.json();
  setOrderId(draft.order_id);
  setPricing(draft.pricing_breakdown);
  
  // Navigate to Step 2
  navigation.navigate('CompleteErrand', { 
    orderId: draft.order_id,
    pricing: draft.pricing_breakdown 
  });
};

// STEP 2: Upload Images
const handleUploadImages = async (orderId, images) => {
  for (const image of images) {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('caption', 'Item photo');
    
    await fetch(`/api/orders/errands/${orderId}/upload-image/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
  }
};

// STEP 2: Update Receiver Info
const handleUpdateReceiverInfo = async (orderId) => {
  await fetch(`/api/orders/errands/${orderId}/receiver-info/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      recipient_name: receiverData.name,
      contact_number: receiverData.phone,
      estimated_value: receiverData.estimatedValue
    })
  });
};

// STEP 2: Confirm Order
const handleConfirmOrder = async (orderId) => {
  const response = await fetch(`/api/orders/errands/${orderId}/confirm/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const result = await response.json();
  
  // Success! SMS sent, order is now pending
  Alert.alert('Success', 'Errand placed successfully!');
  navigation.navigate('OrderTracking', { orderId });
};
```

---

## 🎨 UI Screens

### Screen 1: Create Errand + Price Preview

```
┌─────────────────────────────────┐
│  Create Errand                  │
├─────────────────────────────────┤
│  Order Type:                    │
│  [Pickup & Delivery ▼]          │
│                                 │
│  📍 Pickup Location:            │
│  [Westlands, Nairobi]  📍       │
│                                 │
│  📍 Delivery Location:          │
│  [CBD, Nairobi]  📍             │
│                                 │
│  Distance: 9 km                 │
│                                 │
│  Title:                         │
│  [Deliver laptop to client]     │
│                                 │
│  Description:                   │
│  [Dell laptop in black bag]     │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 💰 Price Breakdown:       │ │
│  │ Base Fee: KSh 200         │ │
│  │ Distance: KSh 40          │ │
│  │ ─────────────────         │ │
│  │ Total: KSh 240            │ │
│  └───────────────────────────┘ │
│                                 │
│  [Next] →                       │
└─────────────────────────────────┘
```

### Screen 2: Complete Errand Details

```
┌─────────────────────────────────┐
│  Complete Errand Details        │
├─────────────────────────────────┤
│  Order #123 • KSh 240           │
│                                 │
│  📸 Upload Images:              │
│  [Take Photo] [Gallery]         │
│                                 │
│  ✅ Image 1                     │
│  ✅ Image 2                     │
│                                 │
│  💰 Estimated Value:            │
│  [KSh 50,000]                   │
│                                 │
│  👤 Receiver Details:           │
│  Name: [John Doe]               │
│  Phone: [+254712345678]         │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 📋 Summary:               │ │
│  │ From: Westlands           │ │
│  │ To: CBD                   │ │
│  │ Price: KSh 240            │ │
│  │ Images: 2                 │ │
│  └───────────────────────────┘ │
│                                 │
│  [Confirm Order] 🚀             │
└─────────────────────────────────┘
```

---

## ✅ Key Features

1. **Price shown immediately** on the same page as order creation
2. **DRAFT status** - order not visible to riders until confirmed
3. **No notifications** sent until confirmation
4. **Flexible image upload** - can upload multiple images
5. **Receiver info required** before confirmation
6. **Clean separation** between draft and pending states

---

## 🔄 Status Flow

```
DRAFT → PENDING → ASSIGNED → IN_PROGRESS → COMPLETED
  ↓
CANCELLED (can cancel draft without penalty)
```

---

## 🧪 Testing with cURL

```bash
# Step 1: Create Draft
curl -X POST http://localhost:8000/api/orders/errands/draft/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type_id": 1,
    "title": "Deliver laptop",
    "description": "Dell laptop",
    "pickup_address": "Westlands",
    "delivery_address": "CBD",
    "pickup_latitude": -1.2634,
    "pickup_longitude": 36.8078,
    "delivery_latitude": -1.2864,
    "delivery_longitude": 36.8172,
    "distance": 9.0
  }'

# Step 2a: Upload Image
curl -X POST http://localhost:8000/api/orders/errands/123/upload-image/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@photo.jpg" \
  -F "caption=Laptop photo"

# Step 2b: Update Receiver Info
curl -X POST http://localhost:8000/api/orders/errands/123/receiver-info/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_name": "John Doe",
    "contact_number": "+254712345678",
    "estimated_value": 50000
  }'

# Step 2c: Confirm Order
curl -X POST http://localhost:8000/api/orders/errands/123/confirm/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🆚 Comparison: 2-Step vs 3-Step

| Feature | 2-Step (Errands) | 3-Step (Shopping) |
|---------|------------------|-------------------|
| Price Calculation | Same API as draft creation | Separate API call |
| Image Upload | After draft creation | Separate step |
| Receiver Info | Same screen as images | N/A |
| Use Case | Normal errands | Shopping, complex orders |
| Simplicity | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 📝 Notes

- **Price is calculated automatically** when creating the draft based on distance
- **Optional price preview** endpoint available if you want to show price before creating draft
- **DRAFT orders don't trigger notifications** - only PENDING orders do
- **Can delete draft orders** without any consequences
- **Receiver contact is required** before confirmation
- **Images are optional** but recommended

---

## 🚀 Next Steps

After implementing this flow, you can:
1. Add SMS notifications on confirmation
2. Add push notifications to available riders
3. Implement rider assignment logic
4. Add real-time tracking
5. Implement payment integration
