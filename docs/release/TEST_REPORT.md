# Test and Validation Report

**Date:** 2026-11-02
**Source SHA:** `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9` plus uncommitted browser-test and report changes
**Worktree:** not clean; these results are local and are not associated with a successful CI run.

## Environment

- Python 3.14.2 in an isolated `.venv`.
- Installed pinned project dependencies from `requirements.lock`; test coverage tools pinned in `requirements-dev.txt`.
- Tests ran in a clean environment with `PYTHON_DOTENV_DISABLED=1` so local `.env` values and exported provider credentials could not change test behavior.

## Results

| Check | Result |
|---|---|
| `python -m compileall -q .` | PASS |
| `python -m pip check` | PASS, no broken requirements |
| `python -m pytest -q --tb=no --ignore=tests/e2e` | PASS: 146 passed, 0 failed, 0 skipped; 6 deprecation warnings |
| `python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web --cov-report=term-missing -q --tb=no --disable-warnings --ignore=tests/e2e` | PASS: 146 passed; combined targeted coverage 76% |
| `tests/e2e/test_browser_checkout.py` | BLOCKED before app startup: Chromium could not load missing OS library `libatk-1.0.so.0`; no browser assertion passed. |
| `python -m ruff check .` with checked-in `pyproject.toml` | PASS under the explicitly selected correctness rules (`E9`, `F63`, `F7`, `F82`) |
| `pip-audit -r requirements.lock` | PASS: no known vulnerabilities reported |
| Unprofiled broad Ruff scan before configuration | FAIL: 336 legacy findings (including 124 BLE001 blind catches, modernization, and style findings); no mass autofix was applied |

The six ordinary pytest warnings are existing `datetime.utcnow()` deprecations. The local unsuppressed coverage run emitted 106 warnings and the GitHub Actions coverage run emitted 132, primarily SQLite resource warnings; these did not fail the unit/integration suite. No skipped tests were reported in the 146-test GitHub/local unit/integration runs. The separate browser test is not counted as passed or skipped.

## Live and browser checks

- `python scripts/ai_smoke.py`: FAIL; provider fallback occurred, so this is not genuine AI evidence.
- `python scripts/config_check.py --online`: PASS for config and PayPal sandbox OAuth only.
- Buyer-approved capture, persistence after restart, live signed webhook, and GitHub Actions run: NOT RUN/BLOCKED. Browser E2E is blocked before app startup by missing container libraries. See [release matrix](RELEASE_GATE_MATRIX.md) and [browser evidence](BROWSER_EVIDENCE.md).

## Reproduction

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true python -m pytest -q --ignore=tests/e2e
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web --cov-report=term-missing -q --ignore=tests/e2e
python -m playwright install --with-deps chromium
env -i PATH="$PATH" HOME="$HOME" PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true python -m pytest -q
python -m ruff check .
python -m pip_audit -r requirements.lock
```

The first two pytest commands reproduce the 146-test unit/integration baseline; the final pytest command includes `tests/e2e/` and requires Playwright's browser/system dependencies. Real AI and PayPal smoke commands use separately provisioned credentials and are not part of ordinary CI.
