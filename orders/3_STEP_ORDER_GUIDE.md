# 3-Step Order Creation Process

## Overview
This implements a user-friendly 3-step order creation flow where clients:
1. Fill form and create draft order
2. Upload images as proof/evidence
3. Confirm and place the errand

---

## API Endpoints

### Step 1: Create Draft Order
**POST** `/api/orders/v1/draft/`

Creates a draft order with form data and returns `order_id`.

**Request Body:**
```json
{
  "order_type_id": 1,
  "title": "Deliver laptop to office",
  "additional_description": "Handle with care",
  "pickup_address": "Westlands, Nairobi",
  "delivery_address": "CBD, Nairobi",
  "pickup_latitude": -1.2634,
  "pickup_longitude": 36.8047,
  "delivery_latitude": -1.2864,
  "delivery_longitude": 36.8172,
  "recipient_name": "John Doe",
  "contact_number": "+254712345678",
  "distance": 5.2,
  "approximate_value": 50000,
  "items": [
    {"name": "Laptop", "quantity": 1},
    {"name": "Charger", "quantity": 1}
  ]
}
```

**Response:**
```json
{
  "order_id": 123,
  "status": "draft",
  "pricing_breakdown": {
    "base_fee": 200.0,
    "distance_fee": 0.0,
    "heavy_load_surcharge": 0.0,
    "total": 200.0,
    "distance_km": 5.2
  },
  "next_step": "Upload images at /api/orders/v1/123/upload-image/",
  "message": "Draft order created. Please upload images next."
}
```

---

### Step 2: Upload Images
**POST** `/api/orders/v1/{order_id}/upload-image/`

Upload one or more images as proof/evidence. Can be called multiple times.

**Request (multipart/form-data):**
- `image`: Image file (required)
- `caption`: Optional description

**Response:**
```json
{
  "message": "Image uploaded successfully",
  "image_id": 456,
  "caption": "Item to be delivered",
  "uploaded_at": "2026-04-11T20:30:00Z",
  "total_images": 2,
  "next_step": "Confirm order at /api/orders/v1/123/confirm/"
}
```

---

### Step 3: Confirm Order
**POST** `/api/orders/v1/{order_id}/confirm/`

Confirms and places the order. Sends SMS notification to client.

**Response:**
```json
{
  "order_id": 123,
  "status": "pending",
  "message": "Order confirmed and placed successfully!",
  "pricing": {
    "total": 200.0,
    "distance_km": 5.2
  },
  "images_uploaded": 2,
  "next_step": "Wait for assistant assignment"
}
```

---

## Frontend Implementation

### React/React Native Example

```javascript
// Step 1: User fills form
const handleCreateDraftOrder = async (formData, selectedImages) => {
  try {
    // Create draft order
    const draftResponse = await fetch('/api/orders/v1/draft/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    });
    
    const draft = await draftResponse.json();
    const orderId = draft.order_id;
    
    // Navigate to image upload screen
    navigation.navigate('UploadImages', { orderId, pricing: draft.pricing_breakdown });
    
  } catch (error) {
    console.error('Error creating draft:', error);
  }
};

// Step 2: Upload images
const handleUploadImages = async (orderId, images) => {
  try {
    for (const image of images) {
      const formData = new FormData();
      formData.append('image', {
        uri: image.uri,
        type: 'image/jpeg',
        name: 'photo.jpg'
      });
      formData.append('caption', image.caption || '');
      
      await fetch(`/api/orders/v1/${orderId}/upload-image/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
    }
    
    // Navigate to confirmation screen
    navigation.navigate('ConfirmOrder', { orderId });
    
  } catch (error) {
    console.error('Error uploading images:', error);
  }
};

// Step 3: Confirm order
const handleConfirmOrder = async (orderId) => {
  try {
    const response = await fetch(`/api/orders/v1/${orderId}/confirm/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const result = await response.json();
    
    // Show success and navigate to order tracking
    Alert.alert('Success', result.message);
    navigation.navigate('OrderTracking', { orderId });
    
  } catch (error) {
    console.error('Error confirming order:', error);
  }
};
```

---

## User Flow

```
┌─────────────────────┐
│  1. Fill Form       │
│  - Order details    │
│  - Addresses        │
│  - Items            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Click "Next"       │
│  → Draft Created    │
│  → Get order_id     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. Upload Images   │
│  - Take photos      │
│  - Add captions     │
│  - Upload multiple  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Click "Next"       │
│  → Images uploaded  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. Review & Place  │
│  - See pricing      │
│  - See images       │
│  - Confirm order    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Order Placed! ✅   │
│  - SMS sent         │
│  - Status: pending  │
│  - Wait for rider   │
└─────────────────────┘
```

---

## Image Stages

| Stage | Who | When | Purpose |
|-------|-----|------|---------|
| `before` | Client | During order creation | Show item before pickup |
| `during` | Assistant | After pickup | Proof of pickup/transit |
| `after` | Assistant | After delivery | Proof of delivery |

**Note:** Client uploads during order creation are always marked as `before` stage.

---

## Error Handling

### No Images Uploaded
If user tries to confirm without uploading images:
```json
{
  "error": "Please upload at least one image before confirming order"
}
```

### Unauthorized Access
If user tries to upload/confirm another user's order:
```json
{
  "error": "Not authorized"
}
```

### Order Not Found
```json
{
  "error": "Order not found"
}
```

---

## Testing with cURL

```bash
# Step 1: Create draft
curl -X POST http://localhost:8000/api/orders/v1/draft/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type_id": 1,
    "title": "Test Order",
    "pickup_address": "Location A",
    "delivery_address": "Location B",
    "distance": 5,
    "approximate_value": 1000,
    "items": [{"name": "Item 1", "quantity": 1}]
  }'

# Step 2: Upload image
curl -X POST http://localhost:8000/api/orders/v1/123/upload-image/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@/path/to/image.jpg" \
  -F "caption=Item photo"

# Step 3: Confirm order
curl -X POST http://localhost:8000/api/orders/v1/123/confirm/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Benefits

✅ **User-Friendly**: Clear 3-step process
✅ **Flexible**: Upload multiple images
✅ **Reliable**: Order created even if image upload fails
✅ **Recoverable**: Can retry image upload without recreating order
✅ **Clean**: Separation of concerns
✅ **Trackable**: Each step has clear status

---

## Next Steps

After order confirmation:
1. Order status: `pending`
2. SMS sent to client
3. Order visible to assistants
4. Assistant can accept order
5. Tracking begins
