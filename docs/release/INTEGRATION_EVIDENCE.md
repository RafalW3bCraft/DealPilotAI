# Integration evidence — November 11, 2026

## Genuine AI: PASS

`python scripts/ai_smoke.py` passed with `fallback=false`. `python scripts/ai_release_smoke.py` passed all six scenarios: requested lamp/organizer, Hindi intent and localized output, budget selection, multiple cart items, unsupported products, and malicious catalog descriptions. See [single smoke](../evidence/ai_smoke.json), [release scenarios](../evidence/ai_release_smoke.json) and [real UI evidence](../evidence/browser_live_ai.json).

Provider: Featherless. Actual configured model: `Qwen/Qwen3.8-27B`. The account's current model listing contained that identifier. A metadata-only compatibility probe observed 11 content characters in ordinary mode and zero content characters / five completion tokens in JSON-object mode. Prompt-requested JSON plus strict server-side Pydantic validation resolved the empty-response issue. No model entitlement or new model name was invented. Response prose is server-authored catalog facts; AI supplies selection/rank/quantities. Hindi evidence proves interpretation of the Hindi request plus localized UI, not unrestricted model-authored Hindi prose.

## PayPal sandbox: creation PASS; capture BLOCKED

Fresh `python scripts/config_check.py --online` passed sandbox OAuth. `python scripts/paypal_release_smoke.py --prepare` created real order `9MG566568H183664A`, attempt 1, for 24.99 USD. The approval URL was returned from PayPal. Sanitized source identity, timestamps and latest status are in [PayPal evidence](../evidence/paypal_final.json).

A human must approve as a separate sandbox personal buyer. No buyer password, access token or secret is recorded. The recorded quote expired without buyer approval. When a sandbox buyer is ready, run `python scripts/paypal_release_smoke.py --prepare` once to obtain a fresh quote/order, approve that order, then run `python scripts/paypal_release_smoke.py --attempt <new-attempt-id> --capture-approved`. Do not attempt to capture an expired quote. This independently checks PayPal approval, captures only if approved, repeats the call to check replay, disposes/reopens storage, and verifies the persisted capture. Reopening storage is not a full process/server restart; that separate acceptance remains until executed. Never mark capture PASS without a real COMPLETED capture ID and matching amount/currency.

For the complete browser journey, use `python scripts/run_web.py`, open /shop, and approve from the original buyer browser session. Callback origin must match APP_BASE_URL. Local model/API verification is separate from payment-browser verification.

## Webhooks: BLOCKED for genuine signed delivery

Verification, durable inbox, deduplication, atomic claiming, stale-claim recovery and retry processing are implemented and tested with controlled boundaries. No genuine signed delivery is claimed. The operator needs a public HTTPS forwarding URL to local `/webhooks/paypal`, matching sandbox webhook ID and subscriptions: CHECKOUT.ORDER.APPROVED, CHECKOUT.PAYMENT-APPROVAL.REVERSED, PAYMENT.CAPTURE.PENDING, PAYMENT.CAPTURE.COMPLETED and PAYMENT.CAPTURE.DENIED.

Keep `python scripts/retry_paypal_webhooks.py --watch --interval 60 --limit 20` running for local recovery. Deliver a genuine event after capture; verify the provider signature, correlate the order, interrupt/restart processing, and confirm duplicate delivery does not create another capture. Simulated signatures are unit evidence only.

## CI

The upstream baseline [run 42054489153](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/42054489153) succeeded on `75f25f0864701c1f72954a4fbda27a27f0806c5c`. Earlier reports incorrectly described the older failed run as current. The repaired working tree has not been pushed or executed by GitHub Actions. Its CI gate is NOT RUN. CI now provisions PostgreSQL 17 for real contention tests.

## Historical credential review

TruffleHog source/history scanning ran without credential verification. Working-source candidates are negative URL test fixtures. Historical placeholders and a scanner-rule definition were identified, plus one non-placeholder PostgreSQL credential candidate in `main.py` at commit `79c509760c2b5826e5a171f8eb00311c7c3469ce`. Its password does not match the current private DATABASE_URL password; that does not establish whether the old credential is revoked. Operator confirmation/rotation remains required. No historical credential was used for authentication or printed. See [redacted review](../evidence/historical_secret_review.json). Git history was not rewritten.
