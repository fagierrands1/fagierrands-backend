# ✅ Correct 3-Step Order Flow with Price Preview

## 📱 User Experience Flow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 0: CALCULATE PRICE (Before Draft)                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  User fills:                                        │     │
│  │  • Order type                                       │     │
│  │  • Pickup address                                   │     │
│  │  • Delivery address                                 │     │
│  │  • Distance (calculated from addresses)            │     │
│  │                                                     │     │
│  │  → Calculate Price Button                          │     │
│  └────────────────────────────────────────────────────┘     │
│                         ↓                                    │
│  🔄 POST /api/orders/v1/calculate-price/                    │
│  ✅ Response: { base_fee: 200, distance_fee: 40, total: 240 }│
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │  💰 PRICE PREVIEW:                                  │     │
│  │  Base Fee: KSh 200                                  │     │
│  │  Distance Fee: KSh 40 (2km extra)                   │     │
│  │  ─────────────────────                              │     │
│  │  Total: KSh 240                                     │     │
│  │                                                     │     │
│  │  [Next: Create Order] ✅                            │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘

                         ↓

┌─────────────────────────────────────────────────────────────┐
│  STEP 1: CREATE DRAFT ORDER                                 │
│  User clicks "Next" → Draft created with calculated price   │
│                         ↓                                    │
│  🔄 POST /api/orders/v1/draft/                              │
│  ✅ Response: { order_id: 123, pricing: {...} }             │
│  ⚠️  NO SMS/Notification sent yet                           │
└─────────────────────────────────────────────────────────────┘

                         ↓

┌─────────────────────────────────────────────────────────────┐
│  STEP 2: UPLOAD IMAGES                                      │
│  User uploads proof images                                  │
│                         ↓                                    │
│  🔄 POST /api/orders/v1/123/upload-image/                   │
│  ✅ Response: { image_id: 456, total_images: 2 }            │
└─────────────────────────────────────────────────────────────┘

                         ↓

┌─────────────────────────────────────────────────────────────┐
│  STEP 3: REVIEW & CONFIRM                                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │  📋 Order Summary:                                  │     │
│  │  • Pickup: Westlands                                │     │
│  │  • Delivery: CBD                                    │     │
│  │  • Distance: 9 km                                   │     │
│  │  • Price: KSh 240                                   │     │
│  │  • Images: 2 uploaded                               │     │
│  │                                                     │     │
│  │  [Place Order] 🚀                                   │     │
│  └────────────────────────────────────────────────────┘     │
│                         ↓                                    │
│  🔄 POST /api/orders/v1/123/confirm/                        │
│  ✅ Response: { status: "pending" }                         │
│  📱 SMS sent to client ✅                                    │
│  🔔 Notification sent ✅                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 API Endpoints

### Step 0: Calculate Price (BEFORE creating order)
```
POST /api/orders/v1/calculate-price/
```

**Request:**
```json
{
  "order_type_id": 1,
  "distance": 9.0,
  "is_heavy": false
}
```

**Response:**
```json
{
  "order_type": "Pickup & Delivery",
  "pricing_breakdown": {
    "base_fee": 200.0,
    "distance_fee": 40.0,
    "heavy_load_surcharge": 0.0,
    "total": 240.0,
    "distance_km": 9.0
  },
  "calculation_note": "Regular delivery base price"
}
```

---

### Step 1: Create Draft Order
```
POST /api/orders/v1/draft/
```

**Request:**
```json
{
  "order_type_id": 1,
  "title": "Deliver laptop",
  "pickup_address": "Westlands",
  "delivery_address": "CBD",
  "distance": 9.0,
  "approximate_value": 50000,
  "items": [{"name": "Laptop", "quantity": 1}]
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
    "total": 240.0
  },
  "next_step": "Upload images"
}
```

---

### Step 2: Upload Images
```
POST /api/orders/v1/{order_id}/upload-image/
```

**Request (multipart/form-data):**
- `image`: File
- `caption`: String (optional)

---

### Step 3: Confirm Order
```
POST /api/orders/v1/{order_id}/confirm/
```

**Response:**
```json
{
  "order_id": 123,
  "status": "pending",
  "message": "Order confirmed!",
  "pricing": {
    "total": 240.0,
    "distance_km": 9.0
  }
}
```
📱 **SMS sent at this point!**

---

## 💡 Frontend Implementation

### React/React Native Example

```javascript
// STEP 0: Calculate Price
const handleCalculatePrice = async () => {
  const response = await fetch('/api/orders/v1/calculate-price/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      order_type_id: formData.orderTypeId,
      distance: formData.distance,
      is_heavy: formData.isHeavy
    })
  });
  
  const pricing = await response.json();
  
  // Show price to user
  setPriceBreakdown(pricing.pricing_breakdown);
  setShowPricePreview(true);
};

// STEP 1: Create Draft (after user sees price)
const handleCreateDraft = async () => {
  const response = await fetch('/api/orders/v1/draft/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formData)
  });
  
  const draft = await response.json();
  setOrderId(draft.order_id);
  
  // Navigate to image upload
  navigation.navigate('UploadImages', { 
    orderId: draft.order_id,
    pricing: draft.pricing_breakdown 
  });
};

// STEP 2: Upload Images
const handleUploadImages = async (orderId, images) => {
  for (const image of images) {
    const formData = new FormData();
    formData.append('image', image);
    
    await fetch(`/api/orders/v1/${orderId}/upload-image/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
  }
  
  // Navigate to confirmation
  navigation.navigate('ConfirmOrder', { orderId });
};

// STEP 3: Confirm Order
const handleConfirmOrder = async (orderId) => {
  const response = await fetch(`/api/orders/v1/${orderId}/confirm/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const result = await response.json();
  
  // SMS sent! Show success
  Alert.alert('Success', 'Order placed! SMS confirmation sent.');
  navigation.navigate('OrderTracking', { orderId });
};
```

---

## 🎨 UI Screens

### Screen 1: Order Form + Price Calculator
```
┌─────────────────────────────────┐
│  Create Order                   │
├─────────────────────────────────┤
│  Order Type: [Pickup & Delivery]│
│  Pickup: [Westlands]            │
│  Delivery: [CBD]                │
│  Distance: 9 km                 │
│                                 │
│  [Calculate Price] 🧮           │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 💰 Price Breakdown:       │ │
│  │ Base Fee: KSh 200         │ │
│  │ Distance: KSh 40          │ │
│  │ ─────────────────         │ │
│  │ Total: KSh 240            │ │
│  └───────────────────────────┘ │
│                                 │
│  [Next: Create Order] →         │
└─────────────────────────────────┘
```

### Screen 2: Upload Images
```
┌─────────────────────────────────┐
│  Upload Proof Images            │
├─────────────────────────────────┤
│  Order #123                     │
│  Total: KSh 240                 │
│                                 │
│  📸 [Take Photo]                │
│  📁 [Choose from Gallery]       │
│                                 │
│  Uploaded:                      │
│  ✅ Image 1                     │
│  ✅ Image 2                     │
│                                 │
│  [Next: Review] →               │
└─────────────────────────────────┘
```

### Screen 3: Review & Confirm
```
┌─────────────────────────────────┐
│  Review Order                   │
├─────────────────────────────────┤
│  📋 Order Summary               │
│  From: Westlands                │
│  To: CBD                        │
│  Distance: 9 km                 │
│                                 │
│  💰 Price: KSh 240              │
│                                 │
│  📸 Images: 2 uploaded          │
│                                 │
│  [Place Order] 🚀               │
└─────────────────────────────────┘
```

---

## ✅ Key Points

1. **Price shown BEFORE draft creation** ✅
2. User sees price → decides to proceed
3. Draft created (no SMS yet)
4. Images uploaded
5. Order confirmed → **SMS sent** ✅

---

## 🧪 Testing Flow

```bash
# 1. Calculate price first
curl -X POST http://localhost:8000/api/orders/v1/calculate-price/ \
  -H "Content-Type: application/json" \
  -d '{"order_type_id": 1, "distance": 9}'

# 2. Create draft (after seeing price)
curl -X POST http://localhost:8000/api/orders/v1/draft/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 3. Upload image
curl -X POST http://localhost:8000/api/orders/v1/123/upload-image/ \
  -H "Authorization: Bearer TOKEN" \
  -F "image=@photo.jpg"

# 4. Confirm (SMS sent here!)
curl -X POST http://localhost:8000/api/orders/v1/123/confirm/ \
  -H "Authorization: Bearer TOKEN"
```
