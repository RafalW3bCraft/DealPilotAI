# DealPilotAI Hackathon Changelog

- **Repository:** https://github.com/RafalW3bCraft/DealPilotAI
- **Submission branch:** `main`
- **Baseline:** `6ae608c166a3bdf16e3225cbf939ccb1e9d81df0` (2026-11-01)
- **Current HEAD:** `f758a163f2683d56c2c90bc85bcb9a653977c144` (`feat: updates ..`, 2026-11-02)
- **Worktree:** contains uncommitted checkout/reconciliation hardening, merchant browser authentication, storefront redesign, safer client rendering, regression tests, and refreshed release records. These changes have not been published or run in GitHub Actions.

## Hackathon-period implementation in the repository

- `ai/`: provider selection, structured recommendation schema, catalog grounding, and explicitly disclosed deterministic fallback.
- `commerce/`: merchant catalog, cart quotes, checkout state machine, policy checks, and durable storage.
- `paypal_checkout/`: PayPal Orders v2 sandbox client with OAuth, idempotency request IDs, order retrieval, capture, and typed transport errors.
- `web/`: shop/cart/checkout/receipt routes, merchant pages, and webhook verification/recovery paths.
- `migrations/001_commerce.sql`: PostgreSQL commerce schema.
- Test coverage includes AI, catalog/cart/checkout, PayPal client, web/security routes, legacy deal posting, and a Playwright mocked browser flow.

Amazon affiliate referrals remain separate from merchant-owned PayPal checkout.

## Recent committed work

- `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9`: checkout approval-link recovery, merchant bearer-auth behavior, configuration diagnostics, README/release materials, CI workflow, AI release smoke, and test/developer dependencies.
- `f758a163f2683d56c2c90bc85bcb9a653977c144`: browser E2E and related documentation/evidence updates.

These are committed on the local `main` branch. The current uncommitted candidate listed below is not published or represented as merged.

## Current uncommitted candidate

- Added a standalone responsive commerce shell and redesigned the landing, shop, cart, checkout, receipt, and merchant pages.
- Added CSRF-protected merchant browser login/logout with an expiring session, preserving bearer authentication for programmatic clients.
- Hardened checkout replay, approval-link recovery, capture identity reconciliation, and strict integer quantity validation.
- Replaced dynamic AI response HTML insertion with DOM text nodes and tested an injected markup payload in the browser.
- Extended tests for merchant session lifecycle, quantity validation, safe rendering, and the browser-based merchant journey.
- Isolated pytest configuration from local dotenv/provider/payment credentials so a developer's `.env` cannot affect ordinary test runs.

## Verification on 2026-11-05

- Complete clean-venv isolated offline suite: 152 passed, 0 failed, 0 skipped.
- Targeted `ai`, `commerce`, `paypal_checkout`, and `web` coverage: 76%.
- Local Playwright desktop/mobile checkout with a synthetic PayPal gateway, merchant login/logout, and malicious AI text: 1 passed.
- Genuine landing and shop screenshots captured from the local offline application are included in `docs/screenshots/`; they do not represent live AI or payment evidence.
- Compilation, `pip check`, configured Ruff correctness profile, JavaScript syntax, and diff checks: passed.
- `pip_audit -r requirements.lock` reports no known vulnerabilities.
- Latest public GitHub Actions run [41413708891](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/41413708891) failed the test step. The current source changes have not been pushed or rerun.
- Last real AI attempt failed and reported fallback; no successful live inference is evidenced.
- Historical PayPal OAuth was read-only. No buyer-approved capture, real signed webhook, receipt restart recovery, hosted demo, or public video is verified.

The precise evidence and remaining release actions are in [the test report](docs/release/TEST_REPORT.md), [the release gate matrix](docs/release/RELEASE_GATE_MATRIX.md), and [remaining blockers](docs/release/REMAINING_BLOCKERS.md).
