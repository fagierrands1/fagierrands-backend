# NCBA Till API Integration Guide

This document outlines the implementation of the NCBA Till API for mobile payments, which has completely replaced the legacy Safaricom Daraja integration across the entire stack.

## Architecture Overview
The system has moved from a webhook-dependent model to a **polling-based model**. The backend handles direct communication with NCBA, while the frontend polls the backend to verify transaction completion. All user-facing references have been rebranded from "M-Pesa" to **"NCBA Till Pay"**.

## Backend Components (`fagierrandsbackup/orders/`)

### 1. NCBA Service (`ncba_service.py`)
The core service class `NCBAService` handles all API interactions:
- **Authentication**: `get_access_token()` retrieves and caches Bearer tokens.
- **STK Push**: `initiate_stk_push(phone, amount, account)` triggers the payment prompt.
- **Status Query**: `stk_query(transaction_id)` checks the real-time status of a transaction.
- **QR Generation**: `generate_qr(amount, narration)` creates Base64-encoded QR codes.

### 2. Payment Processing (`views_payment_ncba.py`)
- **`InitiatePaymentView`**:
  - Automatically formats phone numbers to the required `254...` format.
  - Standardizes the `TransactionID` from NCBA into the `mpesa_checkout_request_id` field (retained for backward compatibility).
  - Sets the initial payment status to `processing`.
- **`PaymentStatusView`**:
  - The primary polling target for the frontend.
  - Performs a synchronous `stk_query` check if a payment is in `processing` state.
  - Automatically transitions `Payment` and `Order` statuses to `completed` upon a `SUCCESS` response.

### 3. Shopping Prepayments (`views.py`)
- **`ShoppingOrderView`**:
  - Calculates a mandatory 30% deposit for shopping items.
  - Initiates an NCBA STK push immediately upon order creation.
  - Uses `OrderPrepayment` records to track these initial deposits separately from final service payments.

## Frontend Components

### 1. Payment Service (`services/paymentService.ts`)
- **`NCBA` Constant**: Defined as the primary mobile payment method.
- **`pollPaymentStatus`**: A robust polling utility with exponential backoff and a 5-minute timeout.
- **`initiatePayment` & `processPayment`**: Updated to use the `ncba` payment method ID.

### 2. UI Rebranding
- **Screens**: `CheckoutMarketplaceScreen`, `Home-MaintainanceOrderScreen`, `ShopOrderScreen`, `PaymentMethodsScreen`, and `OrderDetailsScreen` have been updated to reflect "NCBA Till Pay".
- **Help & Support**: FAQ answers in `HelpSupportScreen.tsx` updated to list NCBA Till Pay as the supported mobile payment method.
- **Modals**: `AutomaticFacilitationFeeModal.tsx` now uses NCBA logic for fee payments.

## Key Configuration
The following variables must be configured in the environment/settings:
- `NCBA_USERNAME`: API Gateway username.
- `NCBA_PASSWORD`: API Gateway password.
- `NCBA_PAYBILL_NO`: The shortcode used for AccountNo identification.
- `NCBA_TILL_NO`: The specific Till number for QR code generation.

## Technical Notes
- **Database Fields**: Fields like `mpesa_checkout_request_id` in the `Payment` model are now populated with NCBA transaction identifiers. This approach was chosen to maintain data continuity without requiring expensive database migrations.
- **Phone Formatting**: Ensure numbers are sent as `2547XXXXXXXX`. Both frontend and backend services include validation and formatting logic.
- **Status Polling**: The frontend initiates polling immediately after a successful STK initiation response from the backend.

## Troubleshooting
- **Phone Formatting**: If STK push fails, verify the number is in the `254...` format.
- **Status Stuck**: If a payment stays in `processing` for >5 minutes, the polling will timeout. Use the Django Admin to manually refresh the status if needed.
- **Manual Refresh**: Administrators can trigger a status refresh via the Django Admin, which uses the same `stk_query` logic.
