# 170-second demonstration and recording runbook

## Prepare

Install the pinned environment, use private rotated keys, set the callback origin, start `python scripts/run_web.py`, and run the live AI checks. Use a sandbox merchant and a separate sandbox personal buyer. Keep password entry, tokens, emails and account details off-screen. Do not replace a failed live integration with a fixture while calling it real.

The local `docs/demo/live-ai-cart-rehearsal.webm` records genuine AI-to-cart behavior with payment deliberately disabled. It is rehearsal footage, not the final complete transaction video. Screenshots and integration JSON contain the current independently observed evidence.

| Time | Screen / action | Narration |
|---|---|---|
| 0–15s | Storefront and target shopper need | “DealPilotAI connects a natural-language shopping request to a merchant catalog and a checkout the shopper controls.” |
| 15–40s | Submit a real lamp/organizer request; show actual live recommendations | “The AI selects catalog products. The server checks each SKU, price, availability and the whole cart budget. Fallback is labeled when inference is unavailable.” |
| 40–65s | Select recommendations, edit quantity and review server quote | “These prices come from the merchant catalog. Changing quantities creates a new server quote; the model cannot invent a charge.” |
| 65–110s | Follow genuine PayPal sandbox approval and approve as buyer | “PayPal receives the verified quote. I review and approve the sandbox payment myself. Only then can the application capture it.” |
| 110–135s | Actual completed receipt, capture ID and restart retrieval | “The receipt shows the verified capture and persisted amount. This is the same transaction after reopening the application.” |
| 135–155s | Merchant dashboard and compact architecture | “The merchant sees the durable record. Atomic finalization, idempotency, signature verification and reconciliation protect retries.” |
| 155–170s | Technologies, separate affiliate path and sandbox statement | “Flask, grounded AI and PayPal Orders v2 provide a controlled commerce demonstration. Amazon referrals are separate. This is sandbox software, with no real charges or physical shipping.” |

## Required recording gates

Use the capture and restart narration only after those actions are executed. Use the webhook claim as an implemented safeguard until genuine signed delivery is evidenced. Complete buyer approval in advance of recording if login takes too long; never expose the password. Show the actual final app, not screenshots standing in for interaction.

The owner must record the full verified flow, make a YouTube upload publicly visible, verify playback and duration below three minutes, add the real URL to Devpost, and submit before November 12, 2026, 3:00 PM Eastern. No upload or submission has been performed. A locally reproducible project is the selected judge-access path; no hosting deployment is planned.
