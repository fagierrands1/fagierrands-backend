# 2-Step Errand Placement - Quick Reference

## 🎯 What We Built

A streamlined errand placement system where:
1. **Step 1**: User creates draft with locations → sees price immediately
2. **Step 2**: User uploads images, adds receiver info → confirms order

## 📊 System Design

### Price Calculation (Same Page as Step 1)
```
┌─────────────────────────────────┐
│ Distance ≤ 7km: KSh 200         │
│ Distance > 7km: KSh 200 + extra │
│ Extra = (distance - 7) × KSh 20 │
└─────────────────────────────────┘
```

### Status Flow
```
DRAFT → PENDING → ASSIGNED → IN_PROGRESS → COMPLETED
  ↓
CANCELLED
```

### Key Decision: Price API Design

**Question**: Should price calculation be a separate API or combined with draft creation?

**Answer**: We implemented BOTH options!

#### Option A: Separate (Optional)
```
1. POST /errands/calculate-price/  → Get price
2. POST /errands/draft/            → Create with known price
```

#### Option B: Combined (Recommended)
```
1. POST /errands/draft/  → Create draft + get price in same response
```

**Why Option B is better for your use case:**
- Price shown on same page as form
- One less API call
- Simpler frontend logic
- Price is calculated automatically when creating draft

**When to use Option A:**
- User wants to see price before filling all details
- Multiple price scenarios to compare
- Price needs to be shown before any commitment

## 🔗 API Endpoints (7 total)

```
POST   /api/orders/errands/calculate-price/     [Optional]
POST   /api/orders/errands/draft/               [Step 1]
POST   /api/orders/errands/{id}/upload-image/   [Step 2]
POST   /api/orders/errands/{id}/receiver-info/  [Step 2]
POST   /api/orders/errands/{id}/confirm/        [Step 2]
GET    /api/orders/errands/{id}/                [Utility]
DELETE /api/orders/errands/{id}/delete/         [Utility]
```

## 📱 Frontend Flow

### Screen 1: Create Errand
```
┌─────────────────────────────────┐
│ Order Type: [Pickup & Delivery] │
│ Pickup: [Map/Type] 📍           │
│ Delivery: [Map/Type] 📍         │
│ Title: [...]                    │
│ Description: [...]              │
│                                 │
│ 💰 Price: KSh 240               │
│    (9km: Base 200 + Extra 40)   │
│                                 │
│ [Next →]                        │
└─────────────────────────────────┘
```

### Screen 2: Complete & Confirm
```
┌─────────────────────────────────┐
│ Order #123 • KSh 240            │
│                                 │
│ 📸 Upload Images                │
│ [✓ Image 1] [✓ Image 2]         │
│                                 │
│ 💰 Estimated Value              │
│ [KSh 50,000]                    │
│                                 │
│ 👤 Receiver                     │
│ Name: [John Doe]                │
│ Phone: [+254712345678]          │
│                                 │
│ [Confirm Order 🚀]              │
└─────────────────────────────────┘
```

## 🔐 Security & Validation

### Draft Creation
- ✅ User must be authenticated
- ✅ Order type must exist
- ✅ Distance required for price calculation
- ✅ Pickup & delivery addresses required

### Confirmation
- ✅ Must be order owner
- ✅ Order must be in DRAFT status
- ✅ Receiver contact required
- ✅ Pickup & delivery addresses must be set

## 📊 Database Changes

### Order Model
```python
STATUS_CHOICES = (
    ('draft', 'Draft'),        # NEW!
    ('pending', 'Pending'),
    ('assigned', 'Assigned'),
    ('in_progress', 'In Progress'),
    ('payment_pending', 'Payment Pending'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
)
```

## 🎯 Key Features

| Feature | Status |
|---------|--------|
| DRAFT status | ✅ Implemented |
| Price calculation | ✅ Implemented |
| Image upload | ✅ Implemented |
| Receiver info | ✅ Implemented |
| Order confirmation | ✅ Implemented |
| SMS notification | ⏳ TODO |
| Push notification | ⏳ TODO |
| Rider notification | ⏳ TODO |

## 💡 Design Decisions

### 1. Why DRAFT status?
- Orders not visible to riders until confirmed
- User can abandon without consequences
- No premature notifications
- Clean separation of intent vs commitment

### 2. Why price in draft creation?
- User sees cost immediately
- No surprise pricing
- Better UX - price on same page
- Reduces API calls

### 3. Why separate receiver info?
- Not needed for price calculation
- Can be added later
- Flexible user flow
- Required only at confirmation

### 4. Why image upload separate?
- Images can be large
- Multiple images supported
- Can upload incrementally
- Optional but recommended

## 🧪 Testing

Run test script:
```bash
python manage.py shell < test_errand_flow.py
```

Expected output:
```
✅ Price calculation working
✅ Draft order created
✅ Receiver info updated
✅ Status changed: draft → pending
✅ All tests passed!
```

## 📚 Documentation Files

1. **2_STEP_ERRAND_GUIDE.md** - Complete user guide (detailed)
2. **ERRAND_IMPLEMENTATION_SUMMARY.md** - Technical details
3. **ERRAND_COMPLETE.md** - Completion summary
4. **QUICK_REFERENCE.md** - This file (quick overview)

## 🚀 Ready to Use!

The system is fully implemented and tested. Frontend can now integrate using the API endpoints.

**Next**: Integrate SMS and push notifications on order confirmation.
