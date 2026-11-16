# Eligibility matrix

Research date: 2026-11-16. Scores are engineering judgments from 1 (poor fit) to 5 (strong fit), not sponsor scores. ELIGIBLE means the published entry conditions were checked. It does not mean a submission is ready.

| Competition | Eligibility | Compatibility | Reuse | Mandatory sponsor tech | Minimum scope | Hours (estimate) | Risk | External dependencies | Deadline | Demo readiness | Commercial value | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Telegraph verified intelligence | Not a named prize. Dev node is reachable. | 5 | Catalog search, Decimal money, CSRF route | Engine `POST /engine/v1/ask` paid with x402 USDC | One authorized `CRYPTO_PRICE_USD` purchase that changes a recommendation | 16, of which the client and tests exist | Medium until a testnet payment settles | Dev node, x402 2.28.0, funded Sepolia or Base Sepolia test USDC | None found | Unpaid 402 is demonstrated. Paid demo is not | High: paid evidence for procurement | Continue. Do not mark complete |
| QDay / Aevum Builder Challenge | ELIGIBLE on published rules. Build window opened 2026-11-16 06:00 UTC. Registration page says it is open | 4 | New invoice verifier only. Prior code cannot be submitted as the payment | Aevum testnet chain `44005`, tUSD8 `0x456569838f1d43009A91ebA4263147Afd7233483` | One new testnet stablecoin payment flow | 24–40, verifier already written | High until a tUSD8 transfer is observed | RPC confirmed `0xabe5`. Faucet requires a small existing mainnet balance | Submissions close 2026-12-11 08:00 UTC | Chain probe only. Not a payment demo | High if testnet checkout is real | Keep the verifier. Do not call it submitted |
| Cortensor Hackathon #5 | ELIGIBLE | 3 | Catalog search and quote math. The agent must still use OpenMinion | `openminion==0.1.20` and a real model run | One repeatable model-backed workflow plus feedback notes | 20–30, SDK wiring exists | Medium. Echo is done; a model provider is not | Local SDK 0.1.20. Router default is `127.0.0.1:8080`. No model key | 2026-12-18 Pacific | Echo turn only. Not a model demo | Medium | Keep the advisor. Do not submit the echo run |
| CoinMarketCap API Hackathon, Round 2 | CONDITIONAL | 4 | Price display must stay server-side | Campaign Startup-tier key. Do not use an older round | Live quotes for named assets with attribution and rate-limit handling | 12–20 | Medium | Key issued at signup. Submissions open 2026-11-18 00:00 UTC | Close 2026-12-09 23:59 UTC | Not started | Medium. Market quotes are not settlement rates | Wait for a campaign key. Round 1 dates were not reused |
| Reactive Omni Buildathon | CONDITIONAL | 2 | Almost none. Needs new contracts | Reactive contract, origin event, destination callback | Full loop with correlated transaction hashes | 40+ | High | Lasna or mainnet, destination gas, public repo | 2026-12-05 20:00 UTC | Not started | Medium | Do not start until the three stronger entries are demonstrable |
| Terminal 3 Build+Scale grant | CONDITIONAL | 3 | Policy engine can sit beside the ADK | ADK identity or delegated authorization, real DID usage | A blocked unauthorized action and an audited allowed action | 30+ plus adoption time | High. Score is 80% traction | ADK account, credits, real users | 2026-12-24 | Not started | High only with real users | Do not build a badge. Do not invent traction |
| AlgoBharat / Algorand x402 | CONDITIONAL | 3 | None until the event is identified | A working x402 endpoint on Algorand TestNet for the Algorand track | Official protocol payment, not a custom header | 30+ | High | Exact regional event, TestNet USDC ASA `10458941` where that track applies, facilitator | Global x402 registration closed 2026-09-01. No open regional deadline verified | Not started | High if the right event is still open | Blocked. Do not implement a lookalike |
| BCH BLAZE 2026 | CONDITIONAL | 2 | Checkout UX only. Payment must be separate | Mainnet BCH transaction and WizardConnect | Live mainnet checkout plus the required stream and Telegram proof | 30+ | High, and possibly ineligible | DoraHacks registration by 2026-11-13, a prep stream, mainnet funds | Submissions 2026-11-14 to 2026-11-22 14:00 UTC | Not started | Medium | Do not implement until registration and attendance are shown |
| Anna Founding Builder | CONDITIONAL | 2 | Shopping copy could be ported | `anna-app` publish workflow and qualified runs | A native app, approved and published | 40+ and distribution | High | Developer console, review, 200 qualified MAU | Qualification discussed through 2026-11-30 in forum replies; this is a grant, not a prize | Not started | Low without an audience | Do not package a landing page as an integration |
| Gensyn Agent Arena | INELIGIBLE for this product | 1 | None | Delphi evidence submissions on prediction markets | At least 10 judged submissions across 3 markets | Not estimated | Product mismatch | Delphi account, API key from 2026-11-23 | Mining 2026-11-23 17:00 UTC to 2026-12-11 17:00 UTC | Excluded | Low for DealPilotAI | Exclude |

## Reordered work

1. Finish the Telegraph payment once the test wallet holds Sepolia test USDC. The address is `0x8f262935A5Bc86e831Be3bf9055D8c99CC9b944D`; the key is not in git.
2. QDay payment, after an address that already meets the faucet's mainnet-balance rule receives tQDAY and tUSD8. The chain id is already confirmed. The verifier is not a submission.
3. Cortensor, after a tool-capable provider replaces the echo runtime check.
4. CoinMarketCap Round 2, after a campaign key exists on or after 18 November.
5. Reactive only if contract deployment and gas are actually available before 5 December.
6. Terminal 3 only with an ADK account and honest usage.
7. AlgoBharat only after the operator names the open regional event.
8. BCH only with proof of registration and stream attendance.
9. Anna only if publication access and a real user path exist.
10. Gensyn stays off the roadmap.

Three finished submissions are the goal. The current finished count is zero.
