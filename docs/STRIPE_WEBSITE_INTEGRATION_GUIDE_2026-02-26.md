# How To Add Stripe To a Website (Subscription Checkout) - 2026-02-26

This guide documents a practical Stripe subscription integration using:

- Stripe-hosted Checkout (prebuilt payment page)
- Stripe Webhooks (server-to-server payment confirmation)
- A backend-managed trial (7-day free trial in app logic)

This is written for the `buildyoursmartcart.com` setup, but the pattern works for most websites.

## Architecture (Recommended)

Use this flow:

1. User clicks `Subscribe`
2. Frontend calls your backend to create a Stripe Checkout Session
3. Backend returns Stripe Checkout URL
4. Frontend redirects user to Stripe-hosted Checkout
5. Stripe redirects user back to your site after payment
6. Stripe sends webhook events to your backend (source of truth)
7. Backend updates your DB (`subscription_status`, customer/subscription IDs, billing dates)
8. Frontend reads subscription status from your backend and updates the UI

Important:
- Do not trust the frontend success page alone
- Trust Stripe webhook events to confirm payment/subscription state

## What You Need From Stripe

### API Keys

- `STRIPE_SECRET_KEY` (`sk_test_...` or `sk_live_...`) -> backend only
- `STRIPE_PUBLISHABLE_KEY` (`pk_test_...` or `pk_live_...`) -> frontend (optional for redirect-only flow, but keep it set)

### Product and Price

Create a Stripe product (for example):

- `SmartCart Weekly Meal Plan`

Then create a recurring monthly price (for example):

- `$9.99 / month`

Use the **Price ID**:

- `price_...` (correct)

Do not use the Product ID:

- `prod_...` (not valid for Checkout `line_items.price`)

### Webhook Signing Secret

- `STRIPE_WEBHOOK_SECRET` (`whsec_...`)

This comes from the Stripe webhook endpoint you create in the dashboard.

## Required Environment Variables (Website)

For this project:

- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_STANDARD_PRICE_ID` (preferred env var name for the monthly subscription price)
- `STRIPE_WEBHOOK_SECRET`

Backward-compatible aliases supported in this codebase:

- `STRIPE_SUBSCRIPTION_PRICE_ID`
- `STRIPE_PRICE_ID`

## Stripe Dashboard Setup

### 1. Create Product + Recurring Price

In Stripe:

1. Go to `Products`
2. Create product: `SmartCart Weekly Meal Plan`
3. Add price:
   - Type: `Recurring`
   - Amount: `$9.99`
   - Interval: `Monthly`
4. Open the price row and copy the `Price ID` (`price_...`)

Set in your environment:

- `STRIPE_STANDARD_PRICE_ID=price_...`

### 2. Add Webhook Endpoint

In Stripe:

1. Go to `Developers` -> `Webhooks`
2. Click `Add endpoint`
3. Destination name (example): `buildyoursmartcart-prod-webhook`
4. Endpoint URL:
   - `https://buildyoursmartcart.com/api/subscription/webhook`
5. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
6. Save
7. Copy the signing secret (`whsec_...`)

Set in your environment:

- `STRIPE_WEBHOOK_SECRET=whsec_...`

## Backend Responsibilities

Your backend should implement these endpoints (this project already has them):

- `GET /api/subscription/status/{user_id}`
- `POST /api/subscription/create-checkout`
- `GET /api/subscription/checkout/status/{session_id}` (optional polling helper)
- `POST /api/subscription/webhook`
- `POST /api/subscription/cancel/{user_id}`
- `POST /api/subscription/reactivate/{user_id}`
- `POST /api/subscription/create-billing-portal` (manage payment methods/invoices in Stripe)

### Create Checkout Session (Server)

When user clicks subscribe:

- Create Stripe Checkout Session with:
  - `mode: "subscription"`
  - `line_items: [{ price: STRIPE_STANDARD_PRICE_ID, quantity: 1 }]`
  - `success_url: https://your-site/subscription-success?session_id={CHECKOUT_SESSION_ID}`
  - `cancel_url: https://your-site/dashboard`

### Webhook Processing (Server)

Process Stripe webhook events and update your database:

- `checkout.session.completed` -> checkout finished (good trigger for initial sync)
- `customer.subscription.updated` -> status changes / cancel at period end / renewal dates
- `customer.subscription.deleted` -> subscription ended
- `invoice.paid` -> payment succeeded (strong confirmation)
- `invoice.payment_failed` -> mark account `past_due` (or similar)

Store useful fields on the user record:

- `stripe_customer_id`
- `stripe_subscription_id`
- `subscription_status`
- `cancel_at_period_end`
- `subscription_start_date`
- `subscription_end_date`
- `next_billing_date`

## Frontend Responsibilities

### Subscribe Flow

1. Call backend `POST /api/subscription/create-checkout`
2. Redirect browser to returned Stripe URL

### Success Return Flow

When Stripe sends user back to:

- `/subscription-success?session_id=...`

Do this:

1. Read `session_id` from the URL
2. Call `GET /api/subscription/checkout/status/{session_id}` to poll status
3. When `payment_status === "paid"`:
   - show success state
   - refresh subscription status
   - route user back to dashboard/settings

Important:
- Even if success page shows “paid”, webhook is still the source of truth for long-term account state

### Settings / Billing UI (Recommended)

Show:

- current plan (`Trial`, `Premium`, `Trial Ended`)
- trial countdown
- next billing date
- cancel/reactivate subscription controls
- `Manage Payment Methods` button (Stripe Billing Portal)

## Trial Logic (If Managed By Your App)

This project uses a backend-managed `7-day` trial (not Stripe trial mode).

Recommended rule split:

- Backend enforces access:
  - allow generation during trial
  - block generation after trial ends
  - allow history/viewing after trial ends
- Frontend shows:
  - trial countdown
  - gentle upgrade prompt
  - subscription CTA

Do not run duplicate trial logic in both Stripe and your app unless you intentionally designed it.

## Testing (Before Live Launch)

### Use Stripe Test Mode First

Use test values together:

- `STRIPE_SECRET_KEY=sk_test_...`
- `STRIPE_PUBLISHABLE_KEY=pk_test_...`
- `STRIPE_STANDARD_PRICE_ID` = test `price_...`
- `STRIPE_WEBHOOK_SECRET` = test `whsec_...`

Test cards:

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

### Verify Webhook Connectivity

In Stripe Dashboard -> Webhooks -> your endpoint:

- Send test event (`invoice.paid` is a good one)
- Confirm delivery status is `200`

### Verify End-to-End

1. Complete checkout
2. Confirm webhook deliveries succeed
3. Confirm your app user becomes `Premium`
4. Confirm cancel/reactivate works
5. Confirm billing portal opens

## Subscription UX Behavior (Current App)

### Auto-Renew Choice at Checkout

Users can choose whether the subscription should auto-renew when starting checkout:

- `Auto-renew monthly` = ON
  - Stripe subscription renews monthly until the user cancels
- `Auto-renew monthly` = OFF
  - Checkout still creates the monthly subscription
  - Backend disables renewal after checkout completes (`cancel_at_period_end=true`)
  - User keeps access for the current paid month only

Where users can set this:

- `Settings` -> `Subscription & Billing`
- `Subscription` modal

### Cancel / Reactivate in Settings

Users can manage an active subscription in `Settings`:

- `Cancel at Period End`
  - does not immediately remove access
  - keeps premium access until the current monthly billing period ends
- `Reactivate Subscription`
  - removes the scheduled cancellation before the period ends

### Billing Date Display / DB Backfill

The backend stores and returns billing dates for UI display:

- `subscription_start_date`
- `subscription_end_date`
- `next_billing_date`

If Stripe billing dates are temporarily missing for an active subscription, the backend backfills monthly dates from `subscription_start_date` so the UI can still show:

- `Next Billing` (auto-renew ON)
- `Access Until` (auto-renew OFF / cancel at period end)

## Common Mistakes

- Using `prod_...` in `STRIPE_STANDARD_PRICE_ID` (must be `price_...`)
- Mixing test and live values
- Forgetting webhook events
- Not redeploying after environment variable changes
- Exposing raw Stripe errors directly to users (better to show a friendly billing error message)

## Troubleshooting

### Error: `Expired API Key provided: sk_live_...`

Meaning:

- Your server is using an old/revoked Stripe live secret key

Fix:

1. Copy current live secret key from Stripe
2. Update `STRIPE_SECRET_KEY` in Google
3. Redeploy
4. Retry checkout

### Error: `No such price`

Usually means:

- wrong `price_...` value
- using test `price_...` with live key (or vice versa)
- accidental Product ID `prod_...` instead of Price ID

### Webhook returns `400 Invalid webhook payload`

Usually means:

- `STRIPE_WEBHOOK_SECRET` does not match the Stripe endpoint mode (test/live)
- backend not redeployed after updating webhook secret

## Production Go-Live Reference

For a deployment checklist, webhook validation, and rollback steps, see:

- `docs/STRIPE_SUBSCRIPTION_GO_LIVE_CHECKLIST_2026-02-26.md`
