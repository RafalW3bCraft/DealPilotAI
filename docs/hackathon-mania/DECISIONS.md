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

## 2026-11-16 — A 402 is not a completed purchase

Receipts are written only after a signed retry returns HTTP 200 and the body has one positive USD price plus a provenance identifier. Missing signer, timeout, invalid body, and a rejected signature leave no paid receipt.
