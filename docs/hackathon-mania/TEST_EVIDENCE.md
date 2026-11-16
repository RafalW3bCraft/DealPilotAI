# Test evidence

Date: 2026-11-16. Environment: local virtualenv, Python 3.13, dependencies from `requirements-dev.txt`. `x402[evm]==2.28.0` is installed in that virtualenv only.

## Deterministic

```bash
.venv/bin/python -m ruff check integrations/telegraph tests/commerce/test_telegraph.py tests/integration/test_telegraph_live.py web/commerce_routes.py config.py
.venv/bin/python -m pytest tests/commerce/test_telegraph.py -q
.venv/bin/python -m pytest tests/commerce tests/security tests/test_config.py -q
```

Observed: ruff passed. Telegraph file: `14 passed`. Broader set: `226 passed, 1 skipped`. The skip is the live Telegraph test, which does not run unless `TELEGRAPH_LIVE=1`. These tests use a scripted transport. They are not chain evidence.

## Live and unpaid

```bash
TELEGRAPH_LIVE=1 .venv/bin/python -m pytest tests/integration/test_telegraph_live.py -q
```

Observed: `1 passed` in about 10 seconds. The dev node returned miner `CRYPTO_PRICE_USD` and HTTP 402 for an ask with no `PAYMENT-SIGNATURE`. Networks included `eip155:11155111` and `eip155:84532`. `paid` is false. See `evidence/telegraph_unpaid_ask.json`.

## Live Aevum chain id

```bash
AEVUM_LIVE=1 .venv/bin/python -m pytest tests/integration/test_aevum_live.py -q
```

Observed on 2026-11-16: `1 passed`. `https://rpc-test.qday.info` returned `0xabe5` (44005). `paid` is false. See `evidence/aevum_chain.json`. An earlier call without a user agent received HTTP 403. No transaction was sent.

```bash
.venv/bin/python -m ruff check integrations/aevum tests/commerce/test_aevum.py tests/integration/test_aevum_live.py
.venv/bin/python -m pytest tests/commerce/test_aevum.py -q
```

Observed: ruff passed. `7 passed`. These tests use a scripted RPC.

## Live OpenMinion echo

```bash
CORTENSOR_LIVE=1 .venv/bin/python -m pytest tests/integration/test_cortensor_live.py -q
```

Observed on 2026-11-16: `1 passed` in about 8 seconds. SDK `openminion==0.1.20`, provider `echo`, selected SKU `HP-2`, quote `25.00`, `model_backed` false. See `evidence/cortensor_echo.json`. This is not a Cortensor model run. The package is installed in `.venv` only.

Unit tests: `tests/commerce/test_cortensor.py` — `4 passed`.

## Resource close and coverage

```bash
.venv/bin/python -W always::ResourceWarning -m pytest tests/commerce/test_coinmarketcap.py tests/commerce/test_terminal3.py tests/commerce/test_reactive.py tests/commerce/test_bch.py tests/commerce/test_telegraph.py tests/commerce/test_aevum.py -q
.venv/bin/python -m ruff check integrations tests/commerce/test_coinmarketcap.py tests/commerce/test_terminal3.py tests/commerce/test_reactive.py tests/commerce/test_bch.py tests/commerce/test_telegraph.py tests/commerce/test_aevum.py tests/integration/test_reactive_live.py tests/integration/test_bch_live.py web_dashboard_clean.py
.venv/bin/python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web --cov=integrations --cov-fail-under=80 -q tests/commerce tests/security tests/test_config.py
```

Observed on 2026-11-16: ruff passed. The sponsor file run was `41 passed` and printed no unclosed-SQLite or unclosed-event-loop resource warning. The coverage command was `257 passed`, total coverage 80.51%. This is not a GitHub Actions result. The signer happy path is still untested because it needs a funded purchase.

## CoinMarketCap, Terminal 3, Reactive, and BCH

The 41 passing tests include 5 CoinMarketCap, 5 Terminal 3, 3 Reactive, and 4 BCH tests, plus the Telegraph and Aevum files. CoinMarketCap used a scripted transport. No `CMC_API_KEY` was present, and no price was fetched. Terminal 3 decisions set `sdk_called` false. Reactive results set `observed_testnet_hash` null. BCH results set `checkout_complete` false.

## Live Lasna chain id

```bash
REACTIVE_LIVE=1 .venv/bin/python -m pytest tests/integration/test_reactive_live.py -q
```

Observed on 2026-11-16: `1 passed`. `https://lasna-rpc.rnk.dev/` returned `0x512577` (5318007). No transaction was sent. See `evidence/reactive_lasna.json`.

## Live Bitcoin Cash chain tip

```bash
BCH_LIVE=1 .venv/bin/python -m pytest tests/integration/test_bch_live.py -q
```

Observed on 2026-11-16: `1 passed`. `https://api.blockchair.com/bitcoin-cash/stats` returned `best_block_height` 977651. The test did not request a transaction. `checkout_complete` is false. See `evidence/bch_chain.json`.

## Browser signup and balance recheck

On 2026-11-16 the public pages were opened and no form was submitted:

- `https://pro.coinmarketcap.com/signup/?plan=0` shows email, name, password, and plan. No account was created.
- Terminal 3's claim dialog offers Google sign-in or an email, plus name, industry, and role. No key was shown.
- `https://anna.partners/register` asks for an email verification code. No account was created.
- `https://chipnet.bch.ninja/` asks for a Chipnet address. No address was entered.
- Sepolia `eth_getBalance` for `0x8f262935A5Bc86e831Be3bf9055D8c99CC9b944D` returned `0x0` from `https://ethereum-sepolia-rpc.publicnode.com`. Base Sepolia returned `0x0` from `https://sepolia.base.org`. No transaction was sent.

## Offline storefront lifecycle

```bash
.venv/bin/python -m compileall -q .
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest --cov=ai --cov=commerce --cov=paypal_checkout --cov=web --cov=integrations --cov-report=term --ignore=tests/e2e -q
.venv/bin/python scripts/run_web.py --offline --port 5000
```

Observed on 2026-11-16: compileall passed, ruff passed, and pytest reported `287 passed, 8 skipped` at 81% coverage. pyright is not installed and was not added. `tests/e2e` was excluded because Playwright's Chromium binary is not installed. A secret scan for private-key blocks and AKIA-style tokens found no match outside ignored files. `.env` was not printed.

The browser then used `http://127.0.0.1:5000`:

- `/shop` listed eight catalog products. The assistant query "a compact desk lamp under $30" returned the lamp at 24.99 USD and the disclaimer "deterministic ranking, not AI". A second query, "mini whiteboard for desk notes", returned the whiteboard at 21.40 USD.
- A cart with one lamp at quantity 2 quoted 49.98 USD. A later cart with the plant and two lamps quoted 59.97 USD. After a restart, quote `51ec52bb-26a7-4545-8250-33f415f98bdb` still showed the plant and one lamp at 34.98 USD.
- "Check checkout" returned "PayPal sandbox is not configured on this server". No PayPal approval page opened and no order was created.
- `/orders/not-a-real-order` rendered "Order not found" and "No payment was recorded."
- At a 390px viewport, the shop and cart document scroll width stayed 390.

The first server start logged `table merchant_products already exists` and fell back to in-memory storage. That path was fixed before the restart that kept the quote.

## Not run

- A signed Telegraph retry.
- A PayPal buyer-approval page. Offline mode has empty PayPal credentials, so checkout is rejected before an order exists.
- PostgreSQL suite.
- An Aevum tUSD8 transfer. The faucet requires an existing mainnet balance, which was not used.
- A CoinMarketCap quote. `CMC_API_KEY` is unset.
- A Terminal 3 ADK handshake or `invoke()`.
- A Reactive compile, deployment, or callback transaction.
- A BCH payment lookup or broadcast.
- `anna-app`, because Node is v20.19.2 and `@anna-ai/cli` 0.1.64 requires Node 22 or newer.
- GitHub Actions for this uncommitted tree.
