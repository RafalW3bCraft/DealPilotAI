# DealPilotAI Hackathon Changelog

**Repository:** https://github.com/RafalW3bCraft/DealPilotAI
**Submission branch:** `main`
**Previous baseline:** `6ae608c166a3bdf16e3225cbf939ccb1e9d81df0` (2026-11-01)
**Current HEAD:** `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9` (`feat: updates`, 2026-11-02)
**Current worktree:** additional local changes remain uncommitted; no new commit was made during this final verification pass.

## Baseline project

The pre-hackathon application was an Amazon affiliate deal bot with Telegram publishing, scheduled deal discovery, and a Flask dashboard. Its Amazon affiliate lane remains separate from the merchant checkout flow.

## Hackathon implementation present in the repository

- `ai/`: provider selection, catalog tools, structured recommendation schema, grounding, and deterministic offline fallback.
- `commerce/`: merchant catalog, cart quotes, checkout state machine, policy checks, and durable SQLAlchemy storage.
- `paypal_checkout/`: PayPal Orders v2 sandbox client with OAuth, idempotency request IDs, order retrieval, capture, and typed transport errors.
- `web/`: shop/cart/checkout/receipt routes, merchant pages, and webhook verification/recovery paths.
- `migrations/001_commerce.sql`: PostgreSQL commerce schema.
- Tests cover AI behavior, catalog/cart/checkout, PayPal client, web routes, security, and legacy deal posting.

## Changes present in current HEAD

- Checkout replay recovers an approval URL from the existing PayPal order, restricted to trusted HTTPS PayPal hosts.
- Privileged merchant authentication rejects query-string tokens and requires bearer authorization.
- Config diagnostics report separate syntax, credentials, auth, feature, and readiness outcomes.
- `.env.example` now documents offline and sandbox profiles, with catalog routes enabled in offline mode and no payment credentials.
- `AIShoppingService` client construction works with class-level monkeypatching used by the provider test.
- README and release evidence were refreshed; `requirements-dev.txt`, a Ruff correctness profile, a CI workflow, an AI release smoke runner, and release/demo documents were added.

## Additional uncommitted verification changes

- Add a Playwright desktop/mobile checkout test using real Flask/cart/storage code and a synthetic PayPal boundary.
- Provision Chromium and execute the browser test in CI; local execution is blocked before app startup by missing container libraries.
- Correct the exact current-HEAD/source revision and final gate state in the release records.
- Add Playwright to the development dependencies and ignore generated coverage XML.

## Verification on 2026-11-02

- Unit/integration suite excluding the browser test: 146 passed, 0 failed, 0 skipped.
- Targeted `ai`, `commerce`, `paypal_checkout`, and `web` coverage: 76%.
- Ruff correctness profile: passes; the unprofiled legacy scan found 336 findings.
- `pip-audit -r requirements.lock`: no known vulnerabilities reported.
- Genuine Featherless AI smoke: failed; fallback was true.
- PayPal sandbox OAuth: passed; buyer approval and capture not verified.
- Browser E2E: blocked locally before app startup by missing `libatk-1.0.so.0`; GitHub Actions run `41409296241` passed compile/tests/coverage/audit but failed Gitleaks on blank key examples. Its remediation is uncommitted. Signed live webhook, restart persistence after a real capture, hosted demo, and video remain unverified.

Detailed results are in [docs/release/TEST_REPORT.md](docs/release/TEST_REPORT.md) and the [release gate matrix](docs/release/RELEASE_GATE_MATRIX.md).
