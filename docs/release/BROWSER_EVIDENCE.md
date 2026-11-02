# Browser E2E Evidence

**State:** BLOCKED locally; the browser test did not reach the application.

## Test added

`tests/e2e/test_browser_checkout.py` exercises the real Flask shop, deterministic fallback disclosure, catalog-backed cart quote, session and CSRF behavior, checkout state machine, receipt, merchant dashboard, and a 390px mobile viewport. Only the external PayPal boundary is synthetic and clearly named `MOCK-*`; this test is not evidence of live AI or PayPal.

The CI workflow installs Playwright Chromium with `python -m playwright install --with-deps chromium` and runs the test. The workflow has not yet been executed by GitHub Actions.

## Local attempt

Command: `PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= OPENAI_API_KEY= FEATHERLESS_API_KEY= .venv/bin/python -m pytest -q tests/e2e/test_browser_checkout.py -s`

Result: browser launch stopped before the Flask app was exercised because the container lacks `libatk-1.0.so.0`. Playwright/Chromium downloads succeeded, but OS-level browser libraries require privileged package installation. The current workspace user is non-root; no `sudo` or system package modification was attempted.

To run locally, an administrator must install Playwright's Chromium system dependencies (for example, `python -m playwright install --with-deps chromium` in a permitted environment), then rerun the command above. Alternatively, push the reviewed workflow and capture the actual GitHub Actions browser-test result.

No screenshot or viewport assertion is claimed as passing.
