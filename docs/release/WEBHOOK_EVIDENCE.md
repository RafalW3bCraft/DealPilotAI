# Webhook Evidence

**Date:** 2026-11-02  
**State:** BLOCKED for live delivery and scheduled recovery.

## Implementation present

The commerce routes use PayPal's verification endpoint for webhook signature verification, store event identifiers durably, and expose retry processing through `scripts/retry_paypal_webhooks.py`. Unit tests exercise webhook and retry-related behavior with controlled responses. The retry script can be invoked once or scheduled by an operator.

## Evidence available

- Automated suite: 146 passed, 0 failed, 0 skipped. See [TEST_REPORT.md](TEST_REPORT.md).
- Sandbox OAuth: verified separately; this does not authenticate a webhook.
- No real signed sandbox webhook delivery was received during this verification.
- No deployment scheduler or recurring worker is configured or demonstrated.

## Unverified live cases

Signature verification for a real event, duplicate delivery, out-of-order delivery, event after capture, unknown order, database/network outage, worker crash/stale claim, and successful scheduled retry remain unproven against a live sandbox delivery. Do not mark an event recovered based only on its status payload; reconcile with the authoritative PayPal order and capture.

## Required operator action

Configure the sandbox webhook URL and event subscriptions (`CHECKOUT.ORDER.APPROVED`, `CHECKOUT.PAYMENT-APPROVAL.REVERSED`, `PAYMENT.CAPTURE.PENDING`, `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`) with the current webhook ID. Deliver a genuine signed event, verify durable receipt and reconciliation, redeliver it to confirm idempotency, induce a recoverable failure in a non-production test environment, run `python scripts/retry_paypal_webhooks.py`, and configure a recurring scheduler in the selected host. Save sanitized delivery and retry logs. Never include request signatures, bearer tokens, or webhook secrets.
