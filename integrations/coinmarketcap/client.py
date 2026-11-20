"""Server-side quotes for CoinMarketCap API Hackathon, November 2026 Round 2.

The campaign key is sent only in the ``X-CMC_PRO_API_KEY`` header. A missing
key, a throttle, or a body without one exact USD price raises. Nothing in this
module is a checkout rate.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .errors import MissingApiKey, QuoteUnavailable, RateLimited

ROUND_ID = "2026-11-round-2"
BASE_URL = "https://pro-api.coinmarketcap.com"
ENDPOINT_PATH = "/v3/cryptocurrency/quotes/latest"
ATTRIBUTION = "Data provided by CoinMarketCap"
ATTRIBUTION_URL = "https://coinmarketcap.com/"
RATE_LIMIT_CODES = {1008, 1009, 1010, 1011}


class CmcClient:
    def __init__(self, api_key: str, transport):
        key = (api_key or "").strip()
        if not key:
            raise MissingApiKey("CMC_API_KEY is required")
        self._api_key = key
        self.transport = transport

    def latest_usd_quote(self, symbol: str) -> dict:
        ticker = _symbol(symbol)
        query = urlencode({"symbol": ticker, "convert": "USD"})
        url = f"{BASE_URL}{ENDPOINT_PATH}?{query}"
        status, body = self.transport.send(
            url,
            {"X-CMC_PRO_API_KEY": self._api_key, "Accept": "application/json"},
        )
        if status == 429 or _error_code(body) in RATE_LIMIT_CODES:
            code = _error_code(body)
            raise RateLimited(code, "CoinMarketCap rate limit reached")
        if status != 200 or _error_code(body) not in (0, None):
            raise QuoteUnavailable("CoinMarketCap did not return a quote")
        price, last_updated = _usd_price(body, ticker)
        return {
            "round_id": ROUND_ID,
            "endpoint": ENDPOINT_PATH,
            "symbol": ticker,
            "convert": "USD",
            "price": price,
            "last_updated": last_updated,
            "attribution": ATTRIBUTION,
            "attribution_url": ATTRIBUTION_URL,
            "checkout_rate": False,
            "reference_only": True,
        }


def from_env(transport=None):
    key = os.environ.get("CMC_API_KEY", "").strip()
    if not key:
        raise MissingApiKey("CMC_API_KEY is required")
    return CmcClient(key, transport or UrllibTransport())


class UrllibTransport:
    """Used only when a real campaign key is present. Tests inject their own transport."""

    def __init__(self, timeout: float = 20):
        self.timeout = timeout

    def send(self, url: str, headers: dict) -> tuple[int, object]:
        request = Request(
            url,
            headers={**headers, "User-Agent": "DealPilotAI/coinmarketcap"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                status = response.status
        except HTTPError as exc:
            raw = exc.read()
            status = exc.code
        except (URLError, TimeoutError) as exc:
            raise QuoteUnavailable("CoinMarketCap did not return a quote") from exc
        try:
            body = json.loads(raw.decode(), parse_float=Decimal, parse_int=Decimal)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise QuoteUnavailable("CoinMarketCap did not return a quote") from exc
        return status, body


def _symbol(symbol: str) -> str:
    ticker = (symbol or "").strip().upper()
    if not ticker or len(ticker) > 10 or not ticker.isalnum():
        raise QuoteUnavailable("symbol must be one ticker")
    return ticker


def _error_code(body: object) -> int | None:
    if not isinstance(body, dict):
        return None
    status = body.get("status")
    if not isinstance(status, dict):
        return None
    code = status.get("error_code")
    if isinstance(code, bool) or not isinstance(code, (int, Decimal)):
        return None
    return int(code)


def _usd_price(body: object, symbol: str) -> tuple[str, str | None]:
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        raise QuoteUnavailable("CoinMarketCap quote shape was not the v3 array")
    matches = [
        row for row in body["data"]
        if isinstance(row, dict) and str(row.get("symbol", "")).upper() == symbol
    ]
    if len(matches) != 1:
        raise QuoteUnavailable("CoinMarketCap did not return one matching symbol")
    quotes = matches[0].get("quote")
    if not isinstance(quotes, list):
        raise QuoteUnavailable("CoinMarketCap quote shape was not the v3 array")
    usd = [
        item for item in quotes
        if isinstance(item, dict) and str(item.get("symbol", "")).upper() == "USD"
    ]
    if len(usd) != 1:
        raise QuoteUnavailable("CoinMarketCap did not return one USD quote")
    updated = usd[0].get("last_updated")
    if updated is not None and not isinstance(updated, str):
        raise QuoteUnavailable("CoinMarketCap last_updated was not a string")
    return _exact_price(usd[0].get("price")), updated


def _exact_price(value: object) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise QuoteUnavailable("price must be an exact decimal from the API")
    try:
        if isinstance(value, Decimal):
            amount = value
        elif isinstance(value, int):
            amount = Decimal(value)
        elif isinstance(value, str):
            amount = Decimal(value)
        else:
            raise QuoteUnavailable("price must be an exact decimal from the API")
    except (InvalidOperation, ValueError) as exc:
        raise QuoteUnavailable("price must be an exact decimal from the API") from exc
    if not amount.is_finite() or amount <= 0:
        raise QuoteUnavailable("price must be a positive decimal from the API")
    return format(amount, "f")
