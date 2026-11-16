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

## Not run

- A signed Telegraph retry.
- Browser checkout.
- PostgreSQL suite.
- An Aevum tUSD8 transfer. The faucet requires an existing mainnet balance, which was not used.
