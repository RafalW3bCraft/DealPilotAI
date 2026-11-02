# DealPilotAI Demo Runbook

**Target recording length:** 170 seconds (within the 165-175 second requirement).
**Status:** Preparation only; do not record a fake AI result or payment. The live provider and buyer-approved capture gates are currently blocked.

## Before recording

- Rotate credentials exposed in local output and configure fresh sandbox-only values privately.
- Run `python scripts/ai_smoke.py` and the AI release smoke; confirm `fallback=false` and save sanitized evidence.
- Run the full PayPal sandbox buyer journey and confirm a completed capture, receipt after restart, and merchant dashboard entry.
- Confirm webhooks and recurring retry are working or explicitly disclose any gap.
- Use a real local/hosted app and actual sandbox buyer approval. Never edit states, substitute fixtures, or display a mock capture as real.
- Close terminals, environment files, secret managers, and browser tabs that could reveal credentials. Use a fresh browser profile with no private data.
- Capture current desktop app screens; test mobile layout separately. Record the real URLs only if a hosted environment exists.
- Prepare sandbox buyer login in advance without recording the password; pause the recording if interactive approval takes longer than the segment.

## 170-second shot list and voiceover

| Time | On-screen action | Voiceover |
|---|---|---|
| 0-15s | Show the real DealPilotAI shop and project name. | "Finding the right product and checking out are usually separate tasks. DealPilotAI connects conversational discovery to a merchant-owned catalog and keeps payment approval in the shopper's hands." |
| 15-40s | Submit a natural English shopping request in the actual app. Show the real provider/model evidence only if the live result passed. | "I can describe what I need in plain language. The assistant uses a configured model, but every recommendation is checked against the merchant catalog. If inference is unavailable, the app labels its deterministic fallback instead of pretending it is AI." |
| 40-65s | Inspect grounded products and prices, then add a recommendation to cart. | "These SKUs and prices come from the server catalog. The model cannot invent an item, change its price, or issue a payment. The cart total is calculated on the server." |
| 65-110s | Start checkout, show the real PayPal sandbox approval page, approve as the sandbox buyer, and wait for the real return/capture. | "Checkout creates a PayPal sandbox order from the server quote. I review and approve it on PayPal. Only after that explicit approval does the application request capture." |
| 110-135s | Show actual receipt/capture details and merchant dashboard, then restart and retrieve the same receipt if prepared. | "The receipt reflects the authoritative capture result and is stored for later retrieval. The merchant view reads the same persisted order. This recording uses the actual sandbox transaction, not a fixture." |
| 135-155s | Show a small code or architecture view for catalog grounding, state machine, and webhook verification. Do not expose secrets. | "AI and payment are separate trust boundaries. Idempotency and reconciliation protect retries, and webhook events must be verified and checked against PayPal's order state before they can change payment status." |
| 155-170s | Return to the app and show technologies/summary. | "DealPilotAI combines Flask, a grounded AI shopping service, durable commerce storage, and PayPal Orders v2 sandbox checkout. Amazon affiliate discovery remains a separate referral path. This is a sandbox demonstration, not production payment processing." |

## Exact recording checklist

- [ ] All live evidence gates required for claims passed on the candidate build.
- [ ] The actual app is visible and responsive; no static mockup is substituted.
- [ ] Natural-language request and recommendations are genuine provider output with `fallback=false`.
- [ ] Prices/SKUs match the real merchant catalog.
- [ ] PayPal page is sandbox, with no passwords or account details visible.
- [ ] A real buyer-approved capture completes; receipt and merchant dashboard match it.
- [ ] Restart/recovery is shown only if performed in the recording session.
- [ ] No credential, bearer token, webhook signature, email, or buyer PII appears.
- [ ] Video is 165-175 seconds and under the Devpost three-minute limit.
- [ ] Upload to the owner's YouTube account as appropriate and verify public/unlisted playback before documenting the URL.
- [ ] Record actual repository, hosted demo, YouTube, and Devpost URLs; never invent links.

**Manual action still required:** a human must approve the PayPal sandbox order and the project owner must perform the YouTube upload/Devpost submission. No video or hosted URL exists yet.
