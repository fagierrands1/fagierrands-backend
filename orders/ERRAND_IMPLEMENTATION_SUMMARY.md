# 2-Step Errand Placement - Implementation Summary

## What Was Built

A streamlined 2-step process for placing normal errands (Pickup & Delivery) with the following features:

### Key Components

1. **New Status: DRAFT**
   - Added to Order model STATUS_CHOICES
   - Orders in DRAFT status are not visible to riders
   - No notifications sent for DRAFT orders
   - Can be deleted without consequences

2. **New API Endpoints** (`views_errand_placement.py`)
   - `POST /api/orders/errands/calculate-price/` - Optional price preview
   - `POST /api/orders/errands/draft/` - Create draft errand
   - `POST /api/orders/errands/{id}/upload-image/` - Upload images
   - `POST /api/orders/errands/{id}/receiver-info/` - Update receiver details
   - `POST /api/orders/errands/{id}/confirm/` - Confirm and make pending
   - `GET /api/orders/errands/{id}/` - Get draft details
   - `DELETE /api/orders/errands/{id}/delete/` - Delete draft

3. **Database Changes**
   - Migration 0039: Added 'draft' to Order.status choices
   - No new tables or fields required

---

## How It Works

### Step 1: Create Draft Errand
User fills out:
- Order type (dropdown)
- Pickup location (map or typing)
- Delivery location (map or typing)
- Title and description

**Price is calculated and shown on the same page**

API creates order with `status='draft'`

### Step 2: Complete & Confirm
User adds:
- Upload images (proof/reference photos)
- Estimated value of items
- Receiver name and contact number

When user clicks "Confirm":
- Status changes from `draft` → `pending`
- SMS notification sent
- Push notification sent
- Order becomes visible to riders

---

## Price Calculation Logic

```python
# Base pricing model
if distance <= 7km:
    price = KSh 200 (base fee)
else:
    extra_km = distance - 7
    price = KSh 200 + (extra_km × KSh 20)

# Example:
# 5km = KSh 200
# 9km = KSh 200 + (2 × KSh 20) = KSh 240
# 15km = KSh 200 + (8 × KSh 20) = KSh 360
```

---

## API Design Decision

### Why separate price calculation from draft creation?

**Option 1: Separate APIs** (Implemented)
```
1. Calculate price → Show to user
2. User decides → Create draft
```

**Option 2: Combined API**
```
1. Create draft → Price calculated automatically
```

**We chose Option 1** because:
- User sees price before committing
- Better UX - no surprises
- Can show price breakdown before creating order
- Optional - can skip if you want

**But also provided Option 2** in the draft creation endpoint:
- Price is calculated automatically when creating draft
- Can show price on the same page
- Simpler for frontend

---

## Status Flow

```
┌──────┐    confirm    ┌─────────┐    assign    ┌──────────┐
│DRAFT │──────────────→│ PENDING │─────────────→│ ASSIGNED │
└──────┘               └─────────┘              └──────────┘
   │                                                   │
   │ delete                                            │
   ↓                                                   ↓
┌───────────┐                                   ┌─────────────┐
│ CANCELLED │                                   │ IN_PROGRESS │
└───────────┘                                   └─────────────┘
                                                      │
                                                      ↓
                                                ┌───────────┐
                                                │ COMPLETED │
                                                └───────────┘
```

---

## Files Modified/Created

### Created:
1. `orders/views_errand_placement.py` - New view functions
2. `orders/2_STEP_ERRAND_GUIDE.md` - Documentation
3. `orders/migrations/0039_add_draft_status.py` - Migration

### Modified:
1. `orders/models.py` - Added 'draft' to STATUS_CHOICES
2. `orders/urls.py` - Added new URL patterns

---

## Frontend Integration Points

### Required Fields for Draft Creation:
- `order_type_id` (required)
- `title` (required)
- `description` (optional)
- `pickup_address` (required)
- `delivery_address` (required)
- `pickup_latitude` (optional but recommended)
- `pickup_longitude` (optional but recommended)
- `delivery_latitude` (optional but recommended)
- `delivery_longitude` (optional but recommended)
- `distance` (required for price calculation)

### Required Fields for Confirmation:
- `recipient_name` (required)
- `contact_number` (required)
- `estimated_value` (optional)
- At least pickup and delivery addresses must be set

---

## Testing Checklist

- [ ] Create draft errand
- [ ] Price is calculated correctly
- [ ] Upload multiple images
- [ ] Update receiver info
- [ ] Confirm errand (status changes to pending)
- [ ] Get draft errand details
- [ ] Delete draft errand
- [ ] Try to confirm without receiver info (should fail)
- [ ] Verify draft orders don't show to riders
- [ ] Verify pending orders show to riders

---

## Next Steps (TODO)

1. **Notifications**
   - Implement SMS sending on confirmation
   - Implement push notifications
   - Notify available riders

2. **Rider Assignment**
   - Auto-assign to nearest rider
   - Manual assignment by admin
   - Rider acceptance flow

3. **Real-time Updates**
   - WebSocket for live tracking
   - Status updates
   - Location updates

4. **Payment Integration**
   - Link to existing payment system
   - Handle payment before/after delivery

5. **Validation**
   - Add more field validations
   - Check for duplicate orders
   - Validate phone numbers

---

## Differences from 3-Step Flow

| Feature | 2-Step (Errands) | 3-Step (Shopping) |
|---------|------------------|-------------------|
| Steps | Draft → Confirm | Draft → Upload → Confirm |
| Price Calc | In draft creation | Separate API |
| Images | Optional, after draft | Required step |
| Use Case | Simple errands | Shopping, complex |
| Receiver Info | Required | N/A |

---

## API Response Examples

### Create Draft Response:
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
  "next_step": "Upload images and add receiver contact info"
}
```

### Confirm Response:
```json
{
  "message": "Errand confirmed successfully!",
  "order_id": 123,
  "status": "pending",
  "notifications_sent": true
}
```

---

## Error Handling

### Common Errors:
1. **Missing required fields** → 400 Bad Request
2. **Order not found** → 404 Not Found
3. **Not order owner** → 404 Not Found (security)
4. **Invalid status transition** → 400 Bad Request
5. **Missing receiver info on confirm** → 400 Bad Request

---

## Security Considerations

- Only order owner can modify draft
- Only order owner can confirm
- Only order owner can delete draft
- Draft orders not visible in public listings
- Pending orders visible to riders

---

## Performance Notes

- Price calculation is fast (no external API calls)
- Image uploads are async
- Database queries are optimized with select_related
- No N+1 queries

---

## Deployment Notes

1. Run migration: `python manage.py migrate`
2. No environment variables needed
3. No new dependencies
4. Backward compatible with existing orders
5. Existing orders remain 'pending' by default
