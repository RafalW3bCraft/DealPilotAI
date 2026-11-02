# Devpost Submission Draft

**Status:** Draft only. Do not submit until the live AI, sandbox capture, public demo, and required links are verified. No hosted URL or YouTube URL is being invented here.

## Project title

DealPilotAI — Conversational Commerce with Verified PayPal Checkout

## Tagline

An AI shopping assistant that turns natural-language product discovery into secure, human-approved PayPal payments.

## The problem

Online discovery and checkout can be disconnected, and shoppers may have difficulty comparing products against a budget. A trustworthy assistant must use an authorized product source, preserve actual merchant prices, and keep the shopper in control of payment.

## Target customers

The prototype is aimed at shoppers who want conversational product discovery and small merchants who need a controlled catalog-to-checkout experience. The separate affiliate lane is for deal publishers using Telegram and Amazon referral links.

## What DealPilotAI does

DealPilotAI provides a conversational interface over a merchant-owned catalog, creates server-priced cart quotes, and integrates with PayPal Orders v2 in sandbox mode. The shopper must explicitly approve the PayPal transaction. A separate legacy affiliate lane can send shoppers to Amazon; those referrals are not PayPal orders and are not part of the merchant checkout catalog.

## Core features

- Merchant catalog with server-authoritative products, SKUs, prices, currencies, and availability.
- AI service with a Pydantic response schema, catalog grounding, and deterministic offline fallback clearly marked as non-AI.
- Cart quoting with decimal arithmetic, limits, and expiration.
- Sandbox-only PayPal Orders v2 integration with request idempotency, capture reconciliation, durable payment storage, and webhook verification/retry code.
- Flask buyer and merchant routes.
- Separate Telegram/Amazon affiliate functionality.

## How AI is used

The AIShoppingService sends the shopper's request and catalog context to an explicitly configured OpenAI-compatible provider. The service validates structured output, drops unknown SKUs, corrects prices from the merchant catalog, and never authorizes or captures payment. When inference is unavailable, the deterministic fallback is labeled as such. As of the current verification, the live provider did not return usable output, so a successful real inference has not been demonstrated; this submission section must be updated after a fresh successful smoke test.

## How PayPal is used

The application uses PayPal Orders v2 in sandbox only. It creates an order from a server-calculated quote, redirects the shopper to PayPal for human approval, and captures only after approval. Webhook code verifies signatures and reconciles events with authoritative order state. Sandbox OAuth was verified, but a buyer-approved completed capture has not yet been evidenced. Do not claim a completed payment until `PAYPAL_SANDBOX_EVIDENCE.md` contains current order and capture proof.

## Technical architecture

Python 3.11+ application; Flask web routes; Pydantic AI schemas; merchant catalog/cart/checkout domain; SQLAlchemy durable commerce storage; PayPal sandbox Orders v2 via `httpx`; legacy Telegram and Amazon referral modules. The commerce and affiliate lanes are distinct.

## How it was built

The existing Telegram/Amazon application was extended with the merchant catalog, AI shopping service, quote/cart layer, payment state machine, PayPal client, durable storage, buyer/merchant pages, and webhook recovery. Existing modules were preserved rather than replaced. The current repository includes regression tests and an offline catalog mode.

## Challenges and achievements

Key engineering challenges include keeping AI output subordinate to catalog truth, making checkout idempotent under retries, refusing live PayPal configuration, preserving payment records durably, and verifying webhook deliveries before reconciliation. Automated local tests pass, but genuine AI inference and a buyer-approved sandbox capture remain release blockers and must not be presented as completed achievements.

## Testing and verification

Current local test report: 146 passed, 0 failed, 0 skipped; 76% targeted coverage. A PayPal sandbox OAuth probe passed. Live AI smoke did not pass; no buyer-approved capture, real signed webhook, browser E2E, or GitHub Actions run is currently verified. See `docs/release/` for the evidence and exact blockers.

## Hackathon-period changes

See [HACKATHON_CHANGELOG.md](../HACKATHON_CHANGELOG.md). The latest local worktree changes are not committed or published, and must not be described as merged.

## Future development

Complete live provider and sandbox verification, browser coverage, recurring webhook retry scheduling, improve accessibility and responsive testing, and complete operational/security controls before any production evaluation.

## Demo and links

- Repository: https://github.com/RafalW3bCraft/DealPilotAI
- Hosted demo: not currently available.
- Public YouTube demo: not uploaded; URL unavailable.
- Hackathon: https://paypalaihackathon.devpost.com/
- Rules: https://paypalaihackathon.devpost.com/rules

## Known limitations and disclosure

The live AI provider/model is not verified, sandbox OAuth is not a capture, live signed webhook delivery is not verified, and the project is not production-ready. Amazon affiliate discovery routes to Amazon, while PayPal applies only to the separate merchant-authorized catalog. No sponsor integration other than the implemented PayPal sandbox Orders v2 integration is claimed.
