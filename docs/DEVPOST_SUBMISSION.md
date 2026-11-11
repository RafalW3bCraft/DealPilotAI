# Devpost submission draft

## Title and tagline

**DealPilotAI** — Find the right products. Approve the payment yourself.

## Problem and audience

Shoppers describe a need in natural language, but still have to translate it into product selections and a trustworthy checkout. Small merchants need discovery that uses their actual catalog without handing financial authority to a model.

## What it does

DealPilotAI connects a Flask storefront, catalog-grounded AI recommendations, a server-priced cart and PayPal Orders v2 sandbox checkout. A shopper asks for products and a budget, reviews the recommendations, chooses quantities and approves payment directly at PayPal. The server validates the capture before displaying a successful receipt. Amazon affiliate referrals remain a separate optional lane.

## AI and PayPal

The verified Featherless model is Qwen/Qwen3.8-27B. It selects/ranks catalog SKUs and proposes quantities. Server code validates typed JSON, current catalog facts, availability and the total budget, then renders commercial facts in English or Hindi. Deterministic fallback is visibly labeled. Live release scenarios passed without fallback; the server, not the model, controls every payment action.

PayPal integration uses sandbox OAuth, Orders creation, buyer approval, capture verification, durable records, idempotency and reconciliation. Webhook code verifies signatures and uses a durable retry inbox. Real order creation is verified; buyer-approved capture and genuine signed webhook evidence must still be completed before submission claims are finalized.

## Implementation and innovation

Flask/Jinja, Python, Pydantic, SQLAlchemy, SQLite/PostgreSQL, Featherless/OpenAI-compatible inference, PayPal Orders v2 and Playwright. The central design separates probabilistic product selection from deterministic pricing and human-controlled payment approval. Atomic capture finalization and explicit ambiguity recovery protect interrupted checkout workflows.

## Hackathon work and impact

The pre-existing Telegram affiliate project gained a merchant commerce domain, AI shopping workflow and PayPal integration in commits dated October 31–November 1, 2026; subsequent November work repaired validation, state, security and UX. See HACKATHON_CHANGELOG.md and actual Git history. The intended impact is a clearer discovery-to-checkout workflow for small merchants. No measured conversion, revenue or market-share improvement is claimed.

## Evidence and links

Repository: https://github.com/RafalW3bCraft/DealPilotAI . MIT license included. Local setup: README.md. Test and integration evidence: docs/release. AI-assisted engineering used OpenAI Codex, ECC review guidance and independent review agents. Product illustrations are repository-native SVG; demo listing copy is identified as authored demo content.

Public YouTube video: **not yet supplied**. Hosted demo: not planned; local judge setup is provided. No actual Devpost submission is claimed.

## Compliance checklist

Official source: https://paypalaihackathon.devpost.com/rules . Deadline: November 12, 2026, 3:00 PM Eastern. Access must remain available through the judging period ending December 15, 2026.

| Requirement | State | Evidence / action |
|---|---|---|
| Meaningful PayPal sandbox + genuine AI | BLOCKED | AI passed; finish buyer-approved capture and end-to-end recording |
| Significant changes during submission period | PASS | Dated commerce/AI/PayPal commits and changelog; organizer decides eligibility |
| Public code + open-source license | BLOCKED | Existing public repository and MIT LICENSE; current repair candidate still requires owner publication |
| Working build and complete source/assets | BLOCKED | Local setup/test artifacts present; complete full integration access gate |
| English text/testing instructions | PASS | This draft, README and demo runbook |
| Demonstration footage / public YouTube under 3 minutes | BLOCKED | 170-second script and local rehearsal; actual full-flow video/upload pending |
| Free judge access through December 15 | BLOCKED | Local offline setup works; complete free integration access unresolved |
| Entrant eligibility, ownership and third-party rights | BLOCKED | Entrant must confirm personal/team eligibility and rights; not inferred from code |
| Submission form and final URLs | BLOCKED | Owner review and authorized submission required |
