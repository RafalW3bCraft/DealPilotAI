# DealPilotAI Hackathon Changelog

**Repository:** https://github.com/RafalW3bCraft/DealPilotAI
**Submission branch:** `main`
**Reviewed base commit:** `6ae608c166a3bdf16e3225cbf939ccb1e9d81df0` (2026-11-01)
**Current worktree:** contains uncommitted local changes; no commit or publication was made in this session.

## Baseline project

The pre-hackathon application was an Amazon affiliate deal bot with Telegram publishing, scheduled deal discovery, and a Flask dashboard. Its Amazon affiliate lane remains separate from the merchant checkout flow.

## Hackathon implementation present in the repository

- `ai/`: provider selection, catalog tools, structured recommendation schema, grounding, and deterministic offline fallback.
- `commerce/`: merchant catalog, cart quotes, checkout state machine, policy checks, and durable SQLAlchemy storage.
- `paypal_checkout/`: PayPal Orders v2 sandbox client with OAuth, idempotency request IDs, order retrieval, capture, and typed transport errors.
- `web/`: shop/cart/checkout/receipt routes, merchant pages, and webhook verification/recovery paths.
- `migrations/001_commerce.sql`: PostgreSQL commerce schema.
- Tests cover AI behavior, catalog/cart/checkout, PayPal client, web routes, security, and legacy deal posting.

## Current session changes (uncommitted)

- Checkout replay recovers an approval URL from the existing PayPal order, restricted to trusted HTTPS PayPal hosts.
- Privileged merchant authentication rejects query-string tokens and requires bearer authorization.
- Config diagnostics report separate syntax, credentials, auth, feature, and readiness outcomes.
- `.env.example` now documents offline and sandbox profiles, with catalog routes enabled in offline mode and no payment credentials.
- `AIShoppingService` client construction works with class-level monkeypatching used by the provider test.
- README and release evidence were refreshed; `requirements-dev.txt`, a Ruff correctness profile, a CI workflow, and release/demo documents were added.

These changes are local and uncommitted. No claim is made that they are merged or present on GitHub.

## Verification on 2026-11-02

- Clean local suite: 146 passed, 0 failed, 0 skipped.
- Targeted `ai`, `commerce`, `paypal_checkout`, and `web` coverage: 76%.
- Ruff correctness profile: passes; the unprofiled legacy scan found 336 findings.
- `pip-audit -r requirements.lock`: no known vulnerabilities reported.
- Genuine Featherless AI smoke: failed; fallback was true.
- PayPal sandbox OAuth: passed; buyer approval and capture not verified.
- GitHub Actions, browser E2E, signed live webhook, restart persistence after a real capture, hosted demo, and video: not verified.

Detailed results are in [docs/release/TEST_REPORT.md](docs/release/TEST_REPORT.md) and the [release gate matrix](docs/release/RELEASE_GATE_MATRIX.md).
