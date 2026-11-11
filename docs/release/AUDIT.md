# Release audit and remediation

Reviewed source: workspace HEAD `23f23d0bfbd26c638adb973ba9a7d937ecba89d5` plus the current repair diff. Verified upstream baseline: `75f25f0864701c1f72954a4fbda27a27f0806c5c`. This report consolidates the previous baseline, architecture, frontend, business-logic and security reports. Git history retains earlier assessments.

| ID | Priority / CWE | Location / behavior | Repair and regression |
|---|---|---|---|
| P01 | P1 | PayPal client omitted redirect context | Validated APP_BASE_URL; real request-body and callback-derived browser fake tests |
| P02 | P1 / CWE-862 | Merchant feature flag bypass | Gates at route, service construction and domain; disabled-flow tests |
| P03 | P1 / CWE-79 | Legacy scraped fields in HTML/handlers | Safe DOM text, event listeners and validated Amazon links; browser injection tests |
| P04 | P1 | AI commercial claims and invalid proposals | Server-authored catalog facts; availability, duplicates, quantity and whole-budget validation |
| P05 | P1 / CWE-918 | Scraping controls unused / substring URL checks | Boundary policy, exact Amazon host checks, HTTPS, no automatic redirects |
| P06 | P2 | Invalid quantities and budgets returned server errors | Explicit body, bounds and Decimal validation; malformed request regressions |
| P07 | P2 | Paid replay and pending browser dead ends | Ownership-first replay, stable order URLs, bounded polling/manual refresh, requoting |
| P08 | P1 | Capture/attempt/quote committed separately | Atomic finalization; rollback, restart, race and PostgreSQL contention tests |
| P09 | P2 | Terminal conflict reported false PAID | Persist capture and review audit; retain terminal state and suppress successful receipt |
| P10 | P1 / CWE-287 | Public demo signing key could forge merchant sessions | Private signing key required with merchant token or PayPal configuration; forged-cookie regression |
| P11 | P2 | Demo login loop and separate legacy auth | Consistent token/session policy; aggregate users view and real dashboard initialization |
| P12 | P2 | Empty AI evidence and stale CI reports | Nonempty/relevance/Hindi/cart release contracts; actual integration and CI distinctions |
| P13 | P1 | PostgreSQL UUID/string mismatch | Dialect-specific UUID mapping, malformed-ID handling, real PostgreSQL tests |
| P14 | P2 | Offline fallback shallow snapshots and weak validation | Deep-copy quote snapshots, ownership/expiry/drift checks, valid catalog entries and bounded relevant fallback |
| P16 | P1 | Capture keys based on local attempt IDs could collide across installations | New claims persist UUID keys; old persisted keys remain stable; cross-database and replay regressions |
| P17 | P1 / CWE-798 | Historical non-placeholder database credential candidate | Not in current source; old revocation/rotation awaits operator confirmation; no history rewrite |
| P15 | P2 | Remote PAYER_ACTION_REQUIRED lost on replay/cancel | Accept valid payer-action navigation and cancellable pre-capture state; regression |

## Frontend and assets

Retained Flask/Jinja and the storefront visual system. Added product-specific SVG illustrations, selectable recommendations, cart selection persistence, editable quantities/requoting, disabled-payment feedback, focus visibility and status announcements. Repaired aggregate legacy users, table selectors, chart ordering and duplicate polling. Screenshots in `docs/screenshots` show the actual application. The browser recording is a local AI-to-cart rehearsal with payment disabled, not a completed PayPal transaction.

## Review method and remaining risk

ECC security-review and verification-loop guidance was read from the installed reference checkout. Independent agents reviewed AI, storefront, legacy frontend and payment/security code; native ECC commands/hooks were not invoked. Financial/auth regressions were written before repairs; a fresh payment review also found the demo-cookie and payer-action issues. Environment-provided credentials were used only after the operator confirmed rotation. No values were committed or printed.

Remaining release gates are centralized in RELEASE_GATE_MATRIX.md. Application-wide distributed limits, full keyboard/screen-reader certification, warehouse inventory, refunds and live operations remain production work. The current local sandbox scope must not be presented as certified WCAG compliance or production readiness.

Storefront comparison: [before](../screenshots/shop-local-offline.png), [repaired desktop](../screenshots/shop-desktop-repaired.png), [repaired mobile](../screenshots/shop-mobile-repaired.png), [genuine live AI](../screenshots/shop-ai-live.png).
