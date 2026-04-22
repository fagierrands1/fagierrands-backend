# Rider Assignment Flow - Implementation Summary

## Current Status ✅

### Errand Placement Flow (Already Implemented)
1. **Step 0**: Calculate price (no order created)
2. **Step 1**: Create draft errand (status = 'draft')
3. **Step 2a**: Upload images
4. **Step 2b**: Add receiver info
5. **Step 3**: Confirm errand (status changes to 'pending')

### Handler Dashboard (Already Implemented)
- Handlers can view all pending orders via `/api/orders/pending/` endpoint
- Permission: `IsHandler` or `IsAdmin`
- When errand status changes to 'pending', it appears in handler dashboard

## Verification Test

Let's verify that upon successful errand placement (status = 'pending'), the handler can see the errand in their dashboard.

### Test Scenario:
1. Client creates a draft errand
2. Client confirms the errand (status → 'pending')
3. Handler queries pending orders
4. Handler should see the newly confirmed errand

### Existing Endpoints:
- **Client confirms errand**: `POST /api/orders/errands/{order_id}/confirm/`
- **Handler views pending orders**: `GET /api/orders/pending/`

## Next Steps (To Be Implemented)

### Phase 1: Rider Assignment by Handler
- Handler assigns a rider (assistant) to the pending errand
- Endpoint: `POST /api/orders/{order_id}/assign/` (already exists)
- This changes order status from 'pending' to 'assigned'

### Phase 2: Client Notification - "Rider Found"
When handler assigns a rider:
1. Order status changes to 'assigned'
2. Client receives notification with rider details:
   - Rider name
   - Rider phone number
   - Rider plate number (if available)

### Phase 3: Time Constraint
- Handler must assign rider within 3 minutes of errand confirmation
- If not assigned within 3 minutes, trigger alert/notification

## Implementation Plan

### 1. Add Rider Details to User Model (if not exists)
Check if `plate_number` field exists in User/Profile model for riders.

### 2. Enhance Assignment Endpoint Response
When handler assigns rider, return rider details to client.

### 3. Add Real-time Notification
Send push notification to client when rider is assigned with rider details.

### 4. Add Time Tracking
- Track when order becomes 'pending' (already have `created_at`)
- Add alert if not assigned within 3 minutes

## Current Database Schema

### Order Model Fields:
- `client` - ForeignKey to User
- `assistant` - ForeignKey to User (the rider)
- `handler` - ForeignKey to User
- `status` - CharField with choices including 'draft', 'pending', 'assigned'
- `created_at` - DateTimeField
- `assigned_at` - DateTimeField

### User Model (needs verification):
- `phone_number` - CharField
- `plate_number` - ? (needs to be added if not exists)

## API Flow Summary

```
Client Side:
1. POST /api/orders/errands/calculate-price/
2. POST /api/orders/errands/draft/
3. POST /api/orders/errands/{id}/upload-image/
4. POST /api/orders/errands/{id}/receiver-info/
5. POST /api/orders/errands/{id}/confirm/  → Status: 'pending'

Handler Side:
6. GET /api/orders/pending/  → See new errand
7. POST /api/orders/{id}/assign/  → Assign rider, Status: 'assigned'

Client Side (Notification):
8. Receive notification: "Rider Found!"
   - Rider name
   - Rider phone
   - Rider plate number
```

## Status: ✅ VERIFIED AND WORKING

**Test Results (2026-04-22):**
```
✅ Draft errand created successfully
✅ Errand confirmed (status changed to 'pending')
✅ Handler can see the errand in pending orders list
✅ Pending orders increased from 1 to 2
```

The current implementation already supports:
- ✅ Errand placement with draft status
- ✅ Errand confirmation (pending status)
- ✅ Handler viewing pending errands (VERIFIED)
- ✅ Handler assigning riders to errands

**Confirmation**: When a client confirms an errand (status → 'pending'), it immediately appears in the handler's pending orders dashboard at `/api/orders/pending/`.

---

## Summary for Implementation Team

### What's Already Working ✅

1. **Client Side - Errand Placement:**
   - Client creates draft errand
   - Client uploads images
   - Client adds receiver info
   - Client confirms errand → Status becomes 'pending'

2. **Handler Side - View Pending Errands:**
   - Handler can access `/api/orders/pending/` endpoint
   - Handler sees all errands with status='pending'
   - Handler can view errand details including:
     - Client information
     - Pickup and delivery addresses
     - Price
     - Order type
     - Shopping items (if any)

3. **Handler Side - Assign Rider:**
   - Handler can assign a rider using `/api/orders/{order_id}/assign/`
   - This changes order status from 'pending' to 'assigned'

### What Needs to Be Implemented 🔨

The next phase is to implement the "Finding Your Rider" and "Rider Found" notifications as described in your requirements.
