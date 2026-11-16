# Telegraph integration

Status: **not complete**. A real purchase has not settled.

## What was verified

On 2026-11-16 the public dev node answered:

- `GET https://devnode.telegraphprotocol.com/api/miners?limit=5` — HTTP 200. Miner `9002` / TxLens advertises `CRYPTO_PRICE_USD` and a minimum price of `10000` atomic units (0.01 USDC).
- `POST https://devnode.telegraphprotocol.com/engine/v1/ask` with `{"intent":"CRYPTO_PRICE_USD","params":{"symbol":"BTC"}}` and no payment header — HTTP 402.
- Decoded `PAYMENT-REQUIRED` header: `x402Version` 2, exact payments of `10000` units on Sepolia (`eip155:11155111`, asset `0xcc194e1a843B658526D0D5C431f670028582Ae17`, payTo `0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b`) and Base Sepolia (`eip155:84532`, asset `0x036CbD53842c5426634e7929541eC2318f3dCF7e`). An escrow personal-sign option and a Solana option were also offered. This client does not use those unless the allowlist and scheme selection are changed.

The opt-in test `tests/integration/test_telegraph_live.py` repeated discovery and the unpaid ask. Result: `1 passed`. Saved summary: `evidence/telegraph_unpaid_ask.json`.

## Sources

- Protocol introduction: https://docs.telegraphprotocol.com/docs/introduction.md
- API specs: https://github.com/telegraphprotocol/Telegraph-api-docs
- Pay-per-request flow, including the dev-node URL and the Sepolia test USDC mint example: https://anjoman.ai/docs/using/x402-inference
- Signer library inspected locally: `x402==2.28.0` (`x402ClientSync`, `ExactEvmScheme`, `encode_payment_signature_header`)

No Telegraph intent was invented. `CRYPTO_PRICE_USD` was present on the live catalog. The shopping flow uses that intent only when the buyer names BTC, ETH, SOL, or BCH.

## Application behavior

`POST /api/intelligence/telegraph` requires a CSRF token, `buyer_authorized: true`, and a `budget_usdc` decimal string.

1. Search the merchant catalog. Catalog prices are copied, not rewritten.
2. If the query does not name a supported reference asset, no Telegraph call is made.
3. Discover a miner that lists `CRYPTO_PRICE_USD`.
4. Refuse the ask when the published minimum or the 402 amount exceeds the buyer budget or `TELEGRAPH_MAX_SPEND_USDC` (default `0.05`).
5. Without `TELEGRAPH_PRIVATE_KEY`, return HTTP 402 and `paid: false`.
6. With a key, sign one exact EVM payment and retry the same ask once.
7. Accept the body only when it contains one positive USD price and a provenance id (`signal_hash`, `request_id`, or `job_id`). The symbol echo, when present, must match.
8. Store a paid receipt in `TELEGRAPH_RECEIPT_DB`. A repeated purchase with the same actor, intent, and params returns that receipt and does not call the network again.
9. Show the catalog USD total divided by the verified reference price. That quotient is context. It is not a checkout amount.

PayPal checkout is not called.

## How to reproduce the unpaid probe

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
TELEGRAPH_LIVE=1 python -m pytest tests/integration/test_telegraph_live.py -q
```

Signing additionally needs `pip install 'x402[evm]==2.28.0'` and a private key that is not committed:

```bash
TELEGRAPH_PRIVATE_KEY=0x...   # Sepolia or Base Sepolia test wallet
TELEGRAPH_NETWORK=eip155:11155111
```

## Known limitations

- No settled payment, no `PAYMENT-RESPONSE`, and no signal body from a paid ask have been recorded.
- A throwaway signer `0x8f262935A5Bc86e831Be3bf9055D8c99CC9b944D` is in gitignored `.env`. Its Sepolia balance was `0` on 2026-11-16. The PoW faucet and Circle faucet both stopped on a human check, so the key has not signed a payment.
- The dev-node facilitator and test USDC mint were not exercised.
- Solana and escrow schemes are parsed and ignored by the default policy.
- A free HTTP 200 without a prior signature is rejected. The dev node did not return one.
- The receipt database is a separate SQLite file, not the commerce order ledger.
- This is not a completed hackathon submission.
