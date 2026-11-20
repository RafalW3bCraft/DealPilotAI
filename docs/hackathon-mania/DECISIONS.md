# Decisions

## 2026-11-16 — Work on the writable hackathon-mania clone

`/mnt/hostshare/DealPilotAI` is owned by uid 1000 and is not writable by this user. The implementation continues in `/home/watcher/work/DealPilotAI` on `hackathon-mania` at `0f24820`. `main` is not checked out for edits.

Alternative considered: editing the host-share tree. Rejected because every write returned permission denied.

## 2026-11-16 — Telegraph is the only integration started

Official dev-node discovery and an unpaid ask both succeeded. The other competitions are either closed, missing a required credential, or a poor product fit. BCH is not started because registration cannot be confirmed after the published close date.

## 2026-11-16 — Telegraph stays out of PayPal

The new code lives in `integrations/telegraph/` and one commerce route. Checkout state, PayPal capture, and catalog prices are unchanged. An external USD reference is displayed as evidence and converted with `Decimal` only for a budget comparison.

## 2026-11-16 — Default networks are the dev-node testnets

The observed 402 accepts `eip155:11155111` (Sepolia), `eip155:84532` (Base Sepolia), a Solana devnet cluster, and an escrow personal-sign option. The client pays only an `exact` option on the configured allowlist, which defaults to the two EVM testnets. Escrow and Solana are not silently substituted.

## 2026-11-16 — x402 is an optional signer, not a core lockfile dependency

`x402==2.28.0` with the `evm` extra was installed in the local virtualenv and inspected. It is imported only when a private key is present. It was not added to `requirements.lock`, so the existing application install does not grow a Web3 stack until a purchase is authorized.

## 2026-11-16 — Gensyn is excluded

Agent Arena scores evidence submitted to Delphi prediction markets. DealPilotAI's catalog, quotes, and checkout do not perform that job. Building a forecasting product only to enter would be a different application.

## 2026-11-16 — Faucet checks are not bypassed

The throwaway signer is `0x8f262935A5Bc86e831Be3bf9055D8c99CC9b944D`. Its private key stays in gitignored `.env`. Sepolia ETH was not mined because the PoW faucet requires a Cloudflare human check, and Circle's Base Sepolia drip requires reCAPTCHA. The QDay faucet additionally requires a small existing Ethereum mainnet balance. No mainnet key was loaded and the on-chain faucet was not called to get around that rule.

## 2026-11-16 — OpenMinion echo is not a Cortensor submission

`openminion==0.1.20` runs through `integrations/cortensor/advisor.py`. The verified provider is `echo`. Echo repeats the prompt, so the advisor ignores it when choosing a product and always prices from the catalog. A tool-capable provider is required before `model_backed` can be true. The package stays out of `requirements.lock`, matching the earlier x402 decision.

## 2026-11-16 — A paid Aevum invoice cannot be replaced

Once an invoice stores a transaction hash, a different hash is rejected. A paid record stays paid. A missing receipt still leaves the invoice awaiting payment.

`integrations/aevum/` records an invoice and marks it paid only when the configured RPC reports chain id `0xabe5` and the receipt contains an exact tUSD8 `Transfer` to that invoice's merchant. Overpayment becomes `requires_review`. A missing receipt stays `awaiting_payment`. There is no checkout route, because no testnet payment has been observed. A bare Python request to the RPC returned HTTP 403; the same call with a user agent returned `0xabe5`.

## 2026-11-16 — November 2026 CoinMarketCap Round 2 is a reference client only

The Round 2 page at `https://coinmarketcap.com/api/resources/api-hackathon-2026-11/` opens submissions on 2026-11-18 00:00 UTC and closes them on 2026-12-09 23:59 UTC. It requires each participant's own campaign key. `CMC_API_KEY` is not set. `integrations/coinmarketcap/` calls `/v3/cryptocurrency/quotes/latest` with `X-CMC_PRO_API_KEY` and refuses a missing key, HTTP 429, error codes 1008–1011, a non-v3 body, and any price that is not one exact positive USD decimal from that body. The returned object sets `checkout_rate` false. No live call was made, including the keyless public path. Older round dates were not reused.

## 2026-11-16 — Terminal 3 is a local delegation boundary

The Build+Scale grant is open through 2026-12-24 15:59 UTC on DoraHacks. The member-delegation document requires an agent DID from an authenticated ADK session and separate member and org grants. `@terminal3/t3n-sdk` was not installed or called. `integrations/terminal3/` records allow and deny decisions for one function, denies payment-named functions, and stores no traction figure. `sdk_called` is false on every decision.

## 2026-11-16 — Reactive Omni has source and a simulated loop, not a transaction

The Omni docs describe `react()`, `requestCallbackV_1_0`, a zero-address placeholder, and destination checks for the proxy and the reactive sender. Those rules are encoded in `integrations/reactive/`. The in-memory test leaves `observed_testnet_hash` null. `https://lasna-rpc.rnk.dev/` returned `eth_chainId` `0x512577` (5318007). No contract was compiled or deployed, and no callback transaction was sent. The published `reactive-lib` main branch still shows the older callback-event interface, so these sources were not compiled against that package.

## 2026-11-16 — AlgoBharat stays unimplemented

Participation is confirmed. The exact open regional event was not found. DoraHacks `algobharat-regional-hack` is the host sponsorship program through 2026-12-31. The sponsorship page requires a working x402 endpoint on Algorand TestNet for that track. `algorand.co/hackathons` does not list a new named regional event open on this date. No header, endpoint, or payment module was added.

## 2026-11-16 — BCH BLAZE is an observer, not a completed payment

`bchblaze.cash` closes registration on 13 November 2026 and the build window on 22 November 2026 at 14:00 UTC. The operator confirmed participation during the build window. The DoraHacks resources page tells builders to use Chipnet for tests and, for the mainnet track, only minimal funds they can recover. It names CashScript, Mainnet.cash, Libauth, BCH Connect, and the XO stack. It does not name WizardConnect; CompeteHub and Hackathon Radar do. A PayPal merchant checkout does not send BCH, so it does not by itself qualify. `integrations/bch/` can match a chain document to a cashaddr and an amount. It stores no seed, accepts no user-supplied hash without outputs, and has no broadcast path. `checkout_complete` stays false. Blockchair reported height 977651. No payment transaction was requested.

## 2026-11-16 — Anna stops at the SDK requirement

The Founding Builder program needs an approved published app. The official CLI is `@anna-ai/cli` 0.1.64, and its npm `engines` field requires Node `>=22`. This machine reports Node v20.19.2. The shopping workflow was not run, and no landing page was added.

## 2026-11-16 — Signup and faucet attempts stopped at identity and balance checks

The browser opened the public forms and did not submit any of them. CoinMarketCap Basic signup asks for an email, a name, and a password. Terminal 3's claim dialog asks for Google sign-in or an email. Anna registration asks for an email verification code. No mailbox or Google session was available, and those checks were not bypassed. No account, API key, or DID was created. The Reactive docs fund lREACT by sending Sepolia or Base Sepolia ETH to a faucet contract. The test wallet's balance on both networks was `0x0`, so nothing was sent. The Chipnet faucet asks for a cashaddr. No BCH seed was generated or stored. `.env` was not given a new secret.

## 2026-11-16 — Offline checkout stays a rejection, and the shop must say so

`python scripts/run_web.py --offline` leaves PayPal credentials empty. The cart used to promise PayPal approval, and the community-deals lane described Amazon checkout, while both paths were off. The cart now says approval is unavailable. "Check checkout" calls the existing `/checkout/start` route and shows the 503. It does not create an attempt. The affiliate lane is shown only when external affiliate links are enabled. A missing order renders an HTML page for browsers and JSON for other clients. Checkout failures log the exception type and return a fixed message. Concurrent first requests no longer drop durable SQLite storage when `create_all` loses a race. None of this is a captured payment.

## 2026-11-16 — A 402 is not a completed purchase

Receipts are written only after a signed retry returns HTTP 200 and the body has one positive USD price plus a provenance identifier. Missing signer, timeout, invalid body, and a rejected signature leave no paid receipt.
