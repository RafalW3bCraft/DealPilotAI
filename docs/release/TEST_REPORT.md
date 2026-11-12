# Test and validation report — November 11, 2026

Source: `codex/paypal-final-submission-2026`, HEAD `23f23d0bfbd26c638adb973ba9a7d937ecba89d5` plus the repair diff. These are local working-tree results, not final-candidate GitHub Actions evidence. [Machine-readable verification](../evidence/local_verification.json) records the tested source fingerprint and summarized results.

## Environment and results

A fresh Python **3.14.9** environment installed `requirements-dev.txt`, including the runtime lockfile. Dependency consistency passed; the final installer dry run required no changes. Tests disable dotenv and isolate credentials. PostgreSQL **17** ran against an expendable UTF-8 database named `dealpilot_test`; Chromium provided real browser execution with controlled payment boundaries.

| Check | State | Result |
|---|---|---|
| Automated suite | PASS | **257 passed; zero failures, errors or skips**, 71.92 seconds |
| Browser scenarios | PASS | **16**, included in the total; desktop/mobile checkout, recovery, malicious content and legacy views |
| Real PostgreSQL tests | PASS | **3**, included in the total; transactions and competing capture finalization |
| Coverage: ai, commerce, paypal_checkout, web | PASS | **81.69%** statement coverage; 2,160 / 2,644 statements; required minimum 80% |
| Clean pinned Python installation | PASS | Python 3.14.9; requirements-dev.txt and lockfile |
| Compilation, dependency consistency, Ruff | PASS | Project compilation, pip check, configured correctness rules |
| JavaScript syntax and diff whitespace | PASS | Both application scripts; git diff --check |
| Lockfile vulnerability audit | PASS | pip-audit reported no known vulnerabilities |
| Working-source secret review | PASS | Scanner candidates are synthetic negative URL fixtures; credential validity not tested |
| Historical credential revocation | BLOCKED | One old non-placeholder database credential candidate; operator confirmation required |
| Repaired candidate CI | NOT RUN | Repair diff remains local; prior baseline CI succeeded |

The suite emitted six existing `datetime.utcnow()` deprecation warnings. Coverage measures the four named packages, not the whole repository. Checkout service coverage is **71%**, storage **92%** and AI agent **96%**. Passing the combined threshold does not establish exhaustive payment-state or production coverage.

## Scenarios exercised

Regressions cover real PayPal request callback fields, ownership before replay, paid and expired quote replay, ambiguity/recovery, atomic capture rollback and contention, terminal financial conflicts, distinct capture identities, UUID idempotency keys across installations, feature combinations, merchant session forgery, malformed quantities/budgets/bodies, unsafe deal/model content, catalog drift and strict proposed-cart budgets. Browser checks exercise selected recommendations, quantity edits, requoting, pending/canceled/failed/review feedback, mobile layouts, labels, keyboard focus and status announcements. This is not a comprehensive WCAG certification.

## Reproduce

Install as documented in [README](../../README.md), then use an expendable PostgreSQL 17 database named **dealpilot_test**. The PostgreSQL tests truncate this database; never point them at application data. Without TEST_POSTGRES_URL, those tests skip and the result does not reproduce the zero-skip release run.

```bash
export PYTHON_DOTENV_DISABLED=1 DEMO_MODE=true
export TEST_POSTGRES_URL=postgresql://dealpilot@127.0.0.1:55489/dealpilot_test
python -m pytest -q --tb=short --disable-warnings \
  --junitxml=junit.xml \
  --cov=ai --cov=commerce --cov=paypal_checkout --cov=web \
  --cov-fail-under=80 --cov-report=term --cov-report=json:coverage.json
python -m compileall -q ai commerce paypal_checkout web core scripts tests
python -m pip check
python -m ruff check .
node --check static/checkout/checkout.js
node --check static/js/dashboard.js
python -m pip_audit -r requirements.lock
git diff --check
```

The port above identifies the isolated service used for this assessment; provision your own database and adapt the connection URL. CI provisions its own PostgreSQL service. The final run's JUnit and coverage JSON were parsed to verify counts independently of terminal output.

## Genuine integration and release limits

Six genuine AI scenarios passed without fallback, and a real AI-to-cart browser rehearsal was captured. Real PayPal OAuth and order creation passed. Buyer-approved capture, full-process payment restart, and genuine signed webhook delivery remain **BLOCKED**. The prepared quote expired without approval; obtain a fresh quote when the buyer is ready. See [integration evidence](INTEGRATION_EVIDENCE.md), [audit](AUDIT.md) and [release gates](RELEASE_GATE_MATRIX.md).

The successful [baseline CI run](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/42054489153) is for `75f25f0864701c1f72954a4fbda27a27f0806c5c`. It does not validate this unpublished repair diff. No deployment, publication or submission was performed.
