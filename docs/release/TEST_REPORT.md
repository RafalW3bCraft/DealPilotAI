# Test and Validation Report

**Date:** 2026-11-02  
**Base SHA:** `6ae608c166a3bdf16e3225cbf939ccb1e9d81df0`  
**Worktree:** uncommitted changes; this report is local evidence and is not tied to a published candidate commit.

## Environment

- Python 3.14.2 in an isolated `.venv`.
- Installed pinned project dependencies from `requirements.lock`; test coverage tools pinned in `requirements-dev.txt`.
- Tests ran with `PYTHON_DOTENV_DISABLED=1` and neutral AI variables to prevent local `.env` values from changing test behavior.

## Results

| Check | Result |
|---|---|
| `python -m compileall -q .` | PASS |
| `python -m pip check` | PASS, no broken requirements |
| `python -m pytest -q --tb=no` | PASS: 146 passed, 0 failed, 0 skipped; 6 deprecation warnings |
| `python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web --cov-report=term-missing -q --tb=no` | PASS: 146 passed; combined targeted coverage 76% |
| `python -m ruff check .` with checked-in `pyproject.toml` | PASS under the explicitly selected correctness rules (`E9`, `F63`, `F7`, `F82`) |
| `python -m pip-audit -r requirements.lock` | PASS: no known vulnerabilities reported |
| Unprofiled broad Ruff scan before configuration | FAIL: 336 legacy findings (including 124 BLE001 blind catches, modernization, and style findings); no mass autofix was applied |

The six pytest warnings are existing `datetime.utcnow()` deprecations. Coverage output also surfaced SQLite resource warnings in tests; these did not fail the suite. No skipped tests were reported.

## Live and browser checks

- `python scripts/ai_smoke.py`: FAIL; provider fallback occurred, so this is not genuine AI evidence.
- `python scripts/config_check.py --online`: PASS for config and PayPal sandbox OAuth only.
- Buyer-approved capture, persistence after restart, live signed webhook, browser E2E, and GitHub Actions run: NOT RUN/BLOCKED. See [release matrix](RELEASE_GATE_MATRIX.md).

## Reproduction

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= OPENAI_API_KEY= FEATHERLESS_API_KEY= python -m pytest -q
PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true AI_PROVIDER= OPENAI_API_KEY= FEATHERLESS_API_KEY= python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web --cov-report=term-missing -q
python -m ruff check .
python -m pip-audit -r requirements.lock
```

Real smoke commands use separately provisioned credentials and are not part of ordinary CI.
