# Browser E2E Evidence

- **Assessment date:** 2026-11-05
- **Source:** HEAD `f758a163f2683d56c2c90bc85bcb9a653977c144` plus current uncommitted backend, storefront, and browser-test changes
- **State:** PASS for the mocked local browser journey only.

## Test

`tests/e2e/test_browser_checkout.py` uses the real Flask shop, deterministic fallback disclosure, catalog-backed cart quote, session and CSRF behavior, checkout state machine, receipt, browser-based merchant login/logout, and a synthetic PayPal gateway. It verifies malicious provider text remains text (no injected image/event handler), and exercises desktop and a 390px mobile viewport. The external payment boundary is fake (`MOCK-*`), and the AI path is deterministic fallback; this is not evidence of live AI or PayPal.

## Local execution

Command:

```bash
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true \
  .venv/bin/python -m pytest -q tests/e2e/test_browser_checkout.py
```

Result: **1 passed**. The current browser run covers the full mocked checkout journey, merchant session authentication, safe dynamic AI text rendering, and mobile overflow. It still emits existing `datetime.utcnow()` deprecation warnings.

GitHub Actions has not verified these local corrections. The current public run failed before they were applied; see [CI evidence](CI_EVIDENCE.md). No genuine sandbox approval/capture or AI-backed browser journey has been run.
