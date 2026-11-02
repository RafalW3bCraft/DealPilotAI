# PayPal Sandbox Evidence

**Date:** 2026-11-02
**Source revision:** `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9`
**Environment:** sandbox only
**State:** BLOCKED; OAuth passed, but no buyer-approved capture was performed.

## Verified

`python scripts/config_check.py --online` reported `PayPal sandbox OAuth: OK` and `PASS (0 problems, 0 warnings)`. This is a read-only client-credentials probe only. It does not create an order, approve an order, capture funds, or prove receipt persistence.

## Not verified

- Current-release order creation and approval URL in a browser.
- Buyer approval using a sandbox buyer.
- Capture ID, completed status, amount, and currency from PayPal.
- Durable receipt and merchant dashboard after application restart.
- Duplicate-return/capture behavior against the same real order.

No order ID or capture ID is claimed in this evidence report. Earlier historical probes are not evidence of a current buyer-approved capture.

## Operator procedure

After rotating credentials exposed in local output, configure `PAYPAL_ENVIRONMENT=sandbox`, fresh sandbox client credentials, a valid webhook ID, `DEMO_MODE=false`, `ENABLE_MERCHANT_CHECKOUT=true`, a strong `FLASK_SECRET_KEY`, and durable `COMMERCE_DATABASE_URL`. Run `python scripts/config_check.py --online`, launch the app, create a cart from the merchant catalog, follow the returned PayPal sandbox approval URL, sign in as the sandbox buyer and approve, then verify the return, authoritative capture, stored receipt, and merchant dashboard. Restart the app and retrieve the same receipt; repeat the return and verify no new capture is made. Record only sanitized order/capture identifiers, amount, currency, status, persistence, and timestamps.

**Buyer approval is an interactive human action.** It has not been performed in this workspace. Do not use live PayPal credentials or real-money payment paths.
