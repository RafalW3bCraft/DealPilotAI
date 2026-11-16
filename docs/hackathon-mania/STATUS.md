# Hackathon Mania status

Updated: 2026-11-16.

## Current objective

Keep Telegraph and QDay unfunded until a permitted faucet check succeeds. The OpenMinion SDK now runs a catalog-priced recommendation, but the only verified provider is echo, so Cortensor is not submission-ready.

## Active phase

Phase 7 remains blocked on test funds. Phase 13 Cortensor has a real SDK turn and no model-backed result. Phase 11 verifies Aevum receipts and has no payment.

## Branch

- Repository: `https://github.com/RafalW3bCraft/AmazonAffiliatedBot.git`
- Branch: `hackathon-mania`
- Last pushed commit: `0f24820`
- `main` was not modified
- Working tree is uncommitted: Telegraph module, Aevum verifier, docs, and config notes

## Enhanced plan

Three finished submissions remain the goal. The finished count is still zero.

1. Telegraph. The dev node, intent, and unpaid 402 are real. A throwaway Sepolia address was created and stored only in gitignored `.env`. Its Sepolia balance is zero. Official faucets stopped on a human check: the Sepolia PoW faucet uses Cloudflare, and the Circle Base Sepolia faucet uses reCAPTCHA. Do not mark a 402 as a purchase.
2. QDay / Aevum. Registration is open and the build window started today. `eth_chainId` on `https://rpc-test.qday.info` returned `0xabe5` (44005) when the request included a user agent. The invoice module accepts a payment only after that chain id and an exact tUSD8 `Transfer` to the merchant. The official faucet will not fund a fresh address unless that address already holds a small Ethereum mainnet balance. No mainnet wallet was used, and no tUSD8 payment exists.
3. Cortensor. `openminion==0.1.20` is installed in the local virtualenv and is not in `requirements.lock`. An echo-provider turn completed and the quote stayed on the catalog price. Echo does not count as a model-backed demo.
4. CoinMarketCap, Terminal 3, Reactive, AlgoBharat, BCH, and Anna stay blocked on credentials, dates, or eligibility. Gensyn stays excluded.

## Completed

- Confirmed `hackathon-mania` matches remote `0f24820`.
- Telegraph client, policy, receipt store, and `/api/intelligence/telegraph` remain in the working tree.
- Created test wallet `0x8f262935A5Bc86e831Be3bf9055D8c99CC9b944D`. The private key is only in `.env`, which git ignores. It was not printed in the docs.
- Confirmed Aevum chain id 44005. Evidence: `evidence/aevum_chain.json`.
- Added `integrations/aevum/`. A paid invoice cannot be replaced by a second transaction. There is still no tUSD8 payment.
- Added `integrations/cortensor/`. A live echo turn selected nothing by itself. Evidence: `evidence/cortensor_echo.json`.

## In progress

A model-capable OpenMinion provider, or test funds for Telegraph. Both need a credential or a human faucet check that this session cannot complete.

## Blockers

- Telegraph: no testnet USDC and no Sepolia ETH. A human has to pass the faucet check, or supply test funds to the address above.
- QDay faucet: the published rule requires about 0.0001 ETH, or 1 USDT, or 1 USDC on Ethereum mainnet. That check was not bypassed.
- BCH BLAZE: registration closed 13 November 2026. No proof of registration.
- AlgoBharat: the open regional event and submission password were not found.
- Terminal 3, CoinMarketCap, and Anna: no sponsor credentials or adoption proof.
- Cortensor: no tool-capable model provider is configured. The router preset points at `127.0.0.1:8080`.
- Gensyn does not fit this product.
- The historical database credential is still waiting for the operator to confirm revocation. It was not printed or used.

## Next action

Pass the human check on https://sepolia-faucet.pk910.de/ for `0x8f262935A5Bc86e831Be3bf9055D8c99CC9b944D`, mint Telegraph test USDC, and run one authorized `CRYPTO_PRICE_USD` purchase. For Cortensor, configure a tool-capable provider and rerun the advisor before calling that submission ready.

## Tests

Aevum unit tests: `8 passed`. Aevum live chain probe: `1 passed`. Cortensor unit tests: `4 passed`. Cortensor echo turn: `1 passed`, `model_backed` false. Earlier Telegraph commerce/security run remains `226 passed, 1 skipped`, plus one opted-in unpaid live probe. No signed Telegraph payment has been run. Wallet balances were rechecked on 2026-11-16 and are still zero on Sepolia, Base Sepolia, and Aevum.
