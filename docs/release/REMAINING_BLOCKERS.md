# Remaining Release Blockers

1. **Rotate exposed credentials.** Replace the Featherless API key, PayPal sandbox client secret, Telegram bot token, dashboard token, and Flask session key that appeared in local session/tool output. Check provider consoles for revocation/rotation and do not paste replacements into chat or source files.
2. **Prove real AI.** After rotation, verify Featherless key/model entitlements and JSON-mode support or configure an authorized OpenAI provider. Require `fallback=false` and grounded results from `scripts/ai_smoke.py`; complete the release scenarios including Hindi, budget, cart, unknown SKU, and malicious catalog text.
3. **Complete sandbox capture.** Use a sandbox buyer to approve an order in the browser, then verify authoritative capture ID/status/amount/currency, durable receipt, merchant view, restart recovery, and duplicate-return idempotency.
4. **Prove webhooks and recovery.** Deliver an authentic signed sandbox event, validate duplicate/out-of-order/retry behavior, and configure recurring execution of `scripts/retry_paypal_webhooks.py` in the deployment environment.
5. **Run browser E2E.** Exercise shop -> AI -> cart -> checkout -> PayPal approval -> receipt -> merchant dashboard on desktop and mobile, with ordinary CI payment calls mocked and a separate real sandbox run.
6. **Run GitHub Actions.** Push the reviewed candidate with no secrets exposed to pull-request jobs, wait for a green workflow, and record its actual run URL and exact SHA.
7. **Finish public demo artifacts.** Capture genuine app screenshots, complete a real 165-175 second demo, upload it to YouTube, and record the actual URL. No hosted demo URL currently exists.
8. **Publish/verify Devpost entry.** Use the draft in `docs/DEVPOST_SUBMISSION.md`, verify all public links and rules, and manually submit only with the project owner's authorization.
9. **Final security review.** Reassess after key rotation, inspect secret history and the candidate diff, and resolve any high-severity issue before release.

The order above preserves the brief's priorities. External actions require the owner's accounts and human sandbox approval; local code and docs can be completed without those credentials.
