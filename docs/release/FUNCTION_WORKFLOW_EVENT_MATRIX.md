# Function, Workflow, and Event Matrix

| Surface | Required behavior | Automated evidence | Live/browser evidence | Current state |
|---|---|---|---|---|
| AI provider selection | Explicit provider and key precedence | `tests/commerce/test_ai_agent.py` | Featherless request attempted; no valid output | BLOCKED |
| AI grounding/schema | Pydantic contract; authorized SKUs and server prices | `tests/commerce/test_ai_agent.py` | Live smoke used fallback | Automated PASS / live BLOCKED |
| Catalog | Active merchant products and authoritative price/currency/stock | `tests/commerce/test_catalog.py` | Local catalog present | Automated PASS |
| Cart | Quote totals, quantity, ownership, expiry | `tests/commerce/test_cart_service.py` | Browser cart not run | Automated PASS / browser NOT RUN |
| Checkout create/replay | Idempotent attempt and approval URL recovery | `tests/commerce/test_checkout_service.py` | No current live order | Automated PASS / live BLOCKED |
| Checkout capture | Buyer ownership, PayPal approval, amount/currency/state | `tests/commerce/test_checkout_service.py`, `tests/commerce/test_paypal_client.py` | No buyer-approved capture | Automated PASS / live BLOCKED |
| Payment persistence | Capture and receipt survive process restart | Storage tests and route tests | No real capture to restart/recover | BLOCKED |
| `CHECKOUT.ORDER.APPROVED` | Verify signature, reconcile authoritative order | Webhook tests in `tests/commerce/test_web_routes.py` and security tests | No genuine signed event | BLOCKED |
| `CHECKOUT.PAYMENT-APPROVAL.REVERSED` | Reconcile reversal without false fulfillment | Webhook unit coverage | No genuine event | BLOCKED |
| `PAYMENT.CAPTURE.PENDING` | Keep payment pending; do not fulfill | Webhook/checkout unit coverage | No genuine event | BLOCKED |
| `PAYMENT.CAPTURE.COMPLETED` | Verify order/capture identity, amount, and currency | Webhook/checkout unit coverage | No genuine event | BLOCKED |
| `PAYMENT.CAPTURE.DENIED` | Record failure without marking paid | Webhook/checkout unit coverage | No genuine event | BLOCKED |
| Duplicate/out-of-order webhook | Durable idempotency and safe reconciliation | Webhook tests | Live redelivery not run | BLOCKED |
| Webhook retry worker | Retry recoverable events; recurring schedule | `scripts/retry_paypal_webhooks.py` exists | One-off and recurring execution not demonstrated | BLOCKED |
| Buyer web flow | Shop -> AI -> cart -> checkout -> receipt | Flask route tests | No Playwright/browser run | NOT RUN |
| Merchant access | Bearer auth; query-string token rejected | `tests/security/test_web_security.py` | Browser/session flow not run | Automated PASS / browser NOT RUN |
| Legacy deal posting | No duplicate post per run | `tests/integration/test_post_deals_once.py` | No external Telegram publish in this pass | Automated PASS / live NOT RUN |

This matrix distinguishes mocked/unit behavior from real provider and browser evidence. Unit tests do not establish external service delivery or a completed payment.
