# Test and Validation Report

- **Assessment date:** 2026-11-05
- **HEAD:** `f758a163f2683d56c2c90bc85bcb9a653977c144`
- **Tested source:** HEAD plus the current uncommitted backend, storefront, security-test, and browser-test changes. These results are not GitHub Actions evidence.

## Environment and isolation

- Python 3.14.2 in the existing virtual environment.
- A fresh virtual environment at `/tmp/dealpilot-clean-2026` installed `requirements-dev.txt` successfully on Python 3.14.2; its full pytest run passed.
- `tests/conftest.py` now disables dotenv and clears external provider/payment credentials before application imports, so tests do not consume local `.env` credentials.
- The fresh-venv run also used a cleared environment; no credential values were loaded or printed.
- No dependency manifests were changed.
- No PostgreSQL test service was available/configured, so PostgreSQL-specific transaction and multiworker concurrency checks were not run.

## Results

| Check | Result |
|---|---|
| `python -m compileall -q .` | PASS |
| `python -m pip check` | PASS, no broken requirements |
| `python -m ruff check .` | PASS under the checked-in correctness rules (`E9`, `F63`, `F7`, `F82`) |
| `python -m pip_audit -r requirements.lock` | PASS, no known vulnerabilities reported |
| Full pytest suite, including `tests/e2e/` | PASS: **152 collected, 152 passed, 0 failed, 0 skipped**; 6 warnings emitted |
| Targeted coverage for `ai`, `commerce`, `paypal_checkout`, and `web` | PASS: **76% combined coverage**; the coverage run also reports 152 passed, 0 failed, 0 skipped and 112 warnings |
| Focused routes, security, and browser tests | PASS: **30 passed**; includes landing-page rendering, merchant login/logout, CSRF/expiry, integer quantity validation, desktop/mobile checkout, and malicious AI text rendering |
| `pip check`, Ruff, compileall, JavaScript syntax, and `git diff --check` | PASS |
| `pip-audit -r requirements.lock` | PASS: no known vulnerabilities reported |
| CI workflow YAML | PASS: `.github/workflows/ci.yml` parsed with Ruby's YAML parser; no workflow file changed in this worktree |
| Current GitHub Actions workflow run | FAIL: run [41413708891](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/41413708891) failed on pre-correction source; no run exists for this uncommitted candidate |

Warnings include existing `datetime.utcnow()` deprecations, pytest-asyncio's unset fixture loop-scope notice, and SQLite resource warnings during coverage. They were not counted as skipped tests.

## Changes exercised

The current candidate adds the commerce page shell and responsive layouts, browser-session merchant login/logout, stricter cart quantity validation, safer AI response rendering with `textContent`, explicit handling of pending checkout recovery, and stronger checkout replay/capture reconciliation checks. Regression tests cover the changed user and payment flows. These local results do not prove live AI inference, a real PayPal capture, production security, or CI.

An initial run before test isolation, with local dotenv settings loaded, reported 14 failed and 138 passed. After adding test-only dotenv/credential isolation, both the ordinary project-venv run and the fresh-venv run pass all 152 tests.

## Live checks and boundaries

- **AI:** not rerun in this assessment. The latest recorded real call failed and used fallback; the affected credentials were identified for rotation before further live testing. See [AI evidence](AI_LIVE_EVIDENCE.md).
- **PayPal:** no buyer-approved transaction or capture was performed. Historical sandbox OAuth is not capture evidence. See [PayPal evidence](PAYPAL_SANDBOX_EVIDENCE.md).
- **Webhooks:** no real signed sandbox delivery or scheduled retry was demonstrated. See [webhook evidence](WEBHOOK_EVIDENCE.md).
- **CI:** no successful run exists for this corrected working tree. GitHub CLI is not authenticated here.

## Reproduction

```bash
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= FEATHERLESS_API_KEY= OPENAI_API_KEY= \
  .venv/bin/python -m compileall -q .
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= FEATHERLESS_API_KEY= OPENAI_API_KEY= \
  .venv/bin/python -m pip check
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= FEATHERLESS_API_KEY= OPENAI_API_KEY= \
  .venv/bin/python -m pytest -q --disable-warnings
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= FEATHERLESS_API_KEY= OPENAI_API_KEY= \
  .venv/bin/python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web \
  --cov-report=term-missing -q --disable-warnings
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= FEATHERLESS_API_KEY= OPENAI_API_KEY= \
  .venv/bin/python -m ruff check .
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= FEATHERLESS_API_KEY= OPENAI_API_KEY= \
  .venv/bin/python -m pip_audit -r requirements.lock
```

Real AI and PayPal smoke tests require separately provisioned, rotated credentials. They must not be run with exposed values or used as ordinary CI dependencies.
