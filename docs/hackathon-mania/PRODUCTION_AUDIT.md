# Production audit

Date: 2026-11-16. Commit: `cd1e579` on `hackathon-mania`. ECC skills used from a local checkout of `affaan-m/ECC`: `production-audit`, `verification-loop`, and `security-review`. The full Cursor installer was not copied in, because its minimal profile also installs unrelated skills.

## Verdict

Production audit: 46/100, blocked. A later storefront pass fixed defects a shopper can hit. It did not raise the score. PayPal capture is still unconfigured in the offline demo, GitHub Actions has not run this tree, and no sponsor payment was observed. No hackathon submission is ready, and the existing release gates still block live money.

## Hackathon readiness

| Competition | Submission-ready | Why |
|---|---|---|
| Telegraph | No | Unpaid HTTP 402 only. No settled purchase. |
| QDay / Aevum | No | Chain id `0xabe5` confirmed. No tUSD8 transfer. |
| Cortensor | No | OpenMinion 0.1.20 echo turn only. `model_backed` is false. |
| CoinMarketCap | No | No campaign key. Submissions were not open on this date. |
| Terminal 3 | No | No ADK account or real usage. |
| Reactive Omni | No | Not started. |
| AlgoBharat | No | Open regional event not identified. |
| BCH BLAZE | No | Registration closed 13 November 2026. No proof of entry. |
| Anna | No | No published native app or qualified users. |
| Gensyn | No | Excluded. Product does not mine prediction-market evidence. |

## Verification report

```text
Build:     PASS  (python -m compileall)
Types:     NOT RUN  (pyright is not installed; no TypeScript project)
Lint:      PASS  (ruff, changed Python files)
Tests:     PASS  (commerce, security, config, integration; live probes skipped)
Coverage:  73% of integrations plus commerce_routes in the first run.
           A later local run, excluding tests/e2e, covered ai, commerce, paypal_checkout, web, and integrations at 81% (287 passed, 8 skipped).
           The workflow file now includes integrations in the 80% gate. GitHub Actions was not run.
Security:  PASS for committed secrets. Matches were the documented placeholder and test fixtures.
Diff:      39 files in cd1e579
Overall:   NOT READY
Target:    NOT PERFORMED (GitHub push of cd1e579 failed on missing credentials, so CI has not run it)
```

## Blockers

- PayPal buyer capture, signed webhook recovery, and the historical database-credential revocation are still open in `docs/release/RELEASE_GATE_MATRIX.md`.
- Telegraph, Aevum, and Cortensor have no genuine external success that a judge can reproduce.
- `integrations/` is in the workflow coverage selection, and GitHub Actions has not run that change. `integrations/telegraph/signing.py` stays thinly covered because the signer is not exercised without a key.
- `cd1e579` is local only. Remote CI has not run it.

## High-value fixes

- `integrations` is now in the CI coverage selection. GitHub Actions has not confirmed it.
- SQLite connections in the Telegraph receipt store and the Aevum invoice store are closed. Commerce storage also survives a second `create_all` that loses the race.
- Keep the Telegraph route unpaid until a funded testnet purchase is stored.
- Confirm the old database credential was rotated before any production claim.

## Evidence checked

- `docs/release/RELEASE_GATE_MATRIX.md`
- `docs/release/AUDIT.md`
- `integrations/telegraph/`, `integrations/aevum/`, `integrations/cortensor/`
- `web/commerce_routes.py` Telegraph route
- `config.py` (the private key is validated and not written to the configuration log)
- `.github/workflows/ci.yml`
- Local compile, ruff, pytest, and a secret scan

## Evidence missing

- A settled Telegraph receipt.
- An Aevum tUSD8 transaction.
- A tool-capable OpenMinion model run.
- A green GitHub Actions run for `cd1e579` or this uncommitted tree.
- Playwright e2e. The local Chromium binary is not installed, so `tests/e2e` was not part of the 287-pass run.

## Storefront pass, same date

The offline app was started with `python scripts/run_web.py --offline` and clicked through in the browser.

Reproduced and fixed:

- The first concurrent requests both built services. SQLite `create_all` then failed with "table already exists", and the process fell back to in-memory storage. Service setup is now serialized, and an "already exists" error no longer abandons a database that is already there. After the fix, a quote survived a process restart.
- A browser request for a missing order returned raw JSON. It now renders an order page that says no payment was recorded. API clients that do not send `text/html` still receive JSON.
- With PayPal unset, the cart still said the shopper would approve payment on PayPal, and the community-deals lane said checkout happens on Amazon. The cart now says approval is unavailable and offers "Check checkout". That click returned "PayPal sandbox is not configured on this server". No attempt was stored. The affiliate lane and nav stay hidden unless external affiliate links are enabled.
- `checkout failed` no longer includes the exception text.

Browser flow that completed: catalog browse, assistant search for a desk lamp and a whiteboard, deterministic fallback with catalog prices, cart quote, quantity update from 24.99 to 49.98 and a two-item total of 59.97, rejected checkout, and the missing-order page. A 390px viewport did not overflow the shop or cart. Buyer approval on PayPal was not reached, because the sandbox credentials are empty. That is a blocked path, not a completed payment.

```text
compileall: PASS
pyright:    NOT RUN (not installed)
ruff:       PASS
pytest:     287 passed, 8 skipped, coverage 81%, tests/e2e excluded
secret scan: no private-key or AKIA match outside ignored files
```
