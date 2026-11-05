# PayPal Sandbox Evidence

- **Last probe:** 2026-11-02
- **Probe source revision:** `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9`
- **Current assessment:** 2026-11-05
**Environment:** sandbox only
**State:** BLOCKED; OAuth passed, but no buyer-approved capture was performed.

## Verified

The historical `python scripts/config_check.py --online` run reported `PayPal sandbox OAuth: OK` and `PASS (0 problems, 0 warnings)`. This was a read-only client-credentials probe only. It does not create an order, approve an order, capture funds, or prove receipt persistence. The current assessment did not repeat the probe because the credentials were previously identified for rotation.

## Not verified

- Current-release order creation and approval URL in a browser.
- Buyer approval using a sandbox buyer.
- Capture ID, completed status, amount, and currency from PayPal.
- Durable receipt and merchant dashboard after application restart.
- Duplicate-return/capture behavior against the same real order.

No order ID or capture ID is claimed in this evidence report. Earlier historical probes are not evidence of a current buyer-approved capture.

## Operator procedure

After rotating the exposed `PAYPAL_CLIENT_ID`/`PAYPAL_CLIENT_SECRET` and any other credentials from local output, configure `PAYPAL_ENVIRONMENT=sandbox`, fresh sandbox client credentials, a valid webhook ID, `DEMO_MODE=false`, `ENABLE_MERCHANT_CHECKOUT=true`, a strong `FLASK_SECRET_KEY`, and durable `COMMERCE_DATABASE_URL`. Run `python scripts/config_check.py --online`, launch the app, create a cart from the merchant catalog, follow the returned PayPal sandbox approval URL, sign in as the sandbox buyer and approve, then verify the return, authoritative capture, stored receipt, and merchant dashboard. Restart the app and retrieve the same receipt; repeat the return and verify no new capture is made. Record only sanitized order/capture identifiers, amount, currency, status, persistence, and timestamps.

**Buyer approval is an interactive human action.** It has not been performed in this workspace. Do not use live PayPal credentials or real-money payment paths.
