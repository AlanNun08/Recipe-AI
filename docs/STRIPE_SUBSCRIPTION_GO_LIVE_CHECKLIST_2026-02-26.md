# Stripe Subscription Go-Live Checklist (2026-02-26)

Use this checklist to launch paid subscriptions for `buildyoursmartcart.com` safely.

## Scope

- 7-day free trial is handled by the app/backend (not Stripe trial mode)
- Stripe handles checkout, billing, payment methods, and webhook events
- App access is updated from Stripe webhooks

## 1. Create Live Stripe Product + Price

In Stripe **Live mode**:

1. Create product: `SmartCart Weekly Meal Plan`
2. Add recurring price:
   - Amount: `$9.99`
   - Billing period: `Monthly`
3. Copy the **Price ID** (`price_...`)

Important:
- Use the **Price ID** (`price_...`) in env vars, not the dollar amount `9.99`
- Do not use Stripe trial settings if the app’s own 7-day trial is enabled

## 2. Set Production Environment Variables (Google)

Required Stripe env vars:

- `STRIPE_SECRET_KEY` = `sk_live_...`
- `STRIPE_PUBLISHABLE_KEY` = `pk_live_...`
- `STRIPE_STANDARD_PRICE_ID` = `price_...` (live recurring monthly price)
- `STRIPE_WEBHOOK_SECRET` = `whsec_...`

Notes:
- `STRIPE_STANDARD_PRICE_ID` is the preferred env var name
- Backward-compatible aliases still supported: `STRIPE_SUBSCRIPTION_PRICE_ID`, `STRIPE_PRICE_ID`
- Keep test and live values separated (do not mix `sk_test` with live `price_...`, etc.)

## 3. Configure Stripe Webhook (Live Mode)

Create a webhook endpoint in Stripe **Live mode**:

- URL: `https://buildyoursmartcart.com/api/subscription/webhook`

Subscribe to events:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

Copy the webhook signing secret and set:

- `STRIPE_WEBHOOK_SECRET=whsec_...`

## 3A. Test Stripe Keys Before Launch (Recommended)

Validate keys before attempting a real customer checkout.

### A. Confirm key types and mode match

- `STRIPE_SECRET_KEY` must be a **live** secret key: `sk_live_...`
- `STRIPE_PUBLISHABLE_KEY` must be a **live** publishable key: `pk_live_...`
- `STRIPE_STANDARD_PRICE_ID` must be a **live-mode** price ID: `price_...`
- `STRIPE_WEBHOOK_SECRET` must be from the **live-mode** webhook endpoint: `whsec_...`

Do not mix test and live values.

Examples of bad combinations:
- `sk_live_...` + test-mode `price_...`
- `sk_test_...` + live-mode `price_...`
- live secret key + test webhook secret

### B. Fast server-side key check (without charging a card)

After updating Google env vars and redeploying, call the live checkout endpoint with a fake user:

- `POST /api/subscription/create-checkout` using:
  - `user_id: "test-user-id"`
  - `origin_url: "https://buildyoursmartcart.com"`

Expected result if Stripe config is loaded correctly:
- `404 {"detail":"User not found"}`

This means:
- the endpoint exists
- request passed schema validation
- Stripe config checks did not fail before user lookup

Common error responses and meaning:
- `503 Stripe is not configured on the server`
  - `STRIPE_SECRET_KEY` missing/placeholder
- `503 Stripe subscription price is not configured`
  - `STRIPE_STANDARD_PRICE_ID` missing
- `Failed to create checkout session: Expired API Key provided: sk_live_...`
  - live secret key in Google is revoked/expired/rotated
  - replace `STRIPE_SECRET_KEY` with the current Stripe live secret key and redeploy

### C. Test mode checkout (before live charges)

Before going fully live, run the full flow in Stripe **Test mode**:

- `STRIPE_SECRET_KEY=sk_test_...`
- `STRIPE_PUBLISHABLE_KEY=pk_test_...`
- `STRIPE_STANDARD_PRICE_ID` = test-mode `price_...`
- `STRIPE_WEBHOOK_SECRET` = test-mode `whsec_...`

Test card (success):
- `4242 4242 4242 4242`

Test card (decline):
- `4000 0000 0000 0002`

### D. After switching to live keys

When switching from test to live:

1. Update all Stripe env vars together (secret, publishable, price ID, webhook secret)
2. Redeploy Google
3. Verify webhook endpoint deliveries return `200`
4. Perform one controlled real checkout test
5. Confirm app user becomes `Premium` after webhook processing

## 4. Deploy Latest App Version

Make sure the latest `main` is deployed (Google auto-trigger via GitHub).

Features required for go-live include:

- Stripe checkout session endpoint
- Stripe webhook endpoint
- Cancel/reactivate subscription endpoints
- Billing Portal endpoint (`/api/subscription/create-billing-portal`)
- Settings page subscription + payment method controls
- Trial gating (generation blocked after trial expiry, history still available)

## 5. Production Smoke Test (Real Flow)

Run a real end-to-end test after deploy:

1. Create a new user account
2. Confirm account verification works (email code)
3. Confirm 7-day trial appears in dashboard/settings
4. Click `Subscribe to Premium` in Settings
5. Complete Stripe checkout
6. Return to app and confirm:
   - plan shows `Premium`
   - access remains enabled
   - cancel/reactivate controls appear

## 6. Verify Webhooks (Required)

In Stripe Dashboard -> Webhooks -> Deliveries:

- Confirm webhook deliveries return `200`
- Check `checkout.session.completed`
- Check `invoice.paid`
- Check `customer.subscription.updated`

If webhooks fail:
- users may pay successfully in Stripe
- but the app may not mark them as active reliably

## 7. Test Subscription Lifecycle Actions

From app `Settings`:

1. Click `Cancel at Period End`
2. Confirm status shows cancellation scheduled
3. Click `Reactivate Subscription`
4. Confirm scheduled cancellation is removed
5. Click `Manage Payment Methods` and verify Stripe Billing Portal opens

## 8. Trial / Access Rules Validation

Confirm app behavior matches business rules:

- Trial user:
  - recipe generation works
  - weekly recipes generation works
  - Starbucks generation works
- Expired trial user:
  - generation is blocked
  - recipe history remains available
  - gentle upgrade prompt is shown
- Paid user:
  - generation works again

## 9. Common Mistakes To Avoid

- Using a `prod_...` Product ID instead of a `price_...` Price ID
- Mixing test and live Stripe keys/price IDs
- Forgetting to add webhook events in Stripe
- Assuming Stripe success redirect alone is enough (webhook is source of truth)
- Forgetting to redeploy after changing Google environment variables

## 10. Rollback / Emergency Plan

If billing issues occur after go-live:

1. Keep signup/login active
2. Temporarily hide/disable `Subscribe to Premium` button in UI (optional fast frontend patch)
3. Check Stripe webhook delivery failures
4. Validate env vars in Google
5. Redeploy last known good commit if needed

## Quick Reference

- Product name: `SmartCart Weekly Meal Plan`
- Price type: `Recurring monthly ($9.99)`
- Env var for plan price: `STRIPE_STANDARD_PRICE_ID`
- Webhook URL: `https://buildyoursmartcart.com/api/subscription/webhook`
