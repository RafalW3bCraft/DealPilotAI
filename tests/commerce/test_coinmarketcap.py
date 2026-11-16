"""CoinMarketCap Round 2 quotes from a scripted transport. No live price is fetched."""

import pytest

from integrations.coinmarketcap.client import ROUND_ID, CmcClient, from_env
from integrations.coinmarketcap.errors import MissingApiKey, QuoteUnavailable, RateLimited


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def send(self, url, headers):
        self.calls.append((url, dict(headers)))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _quote(price="63319.87", symbol="BTC"):
    return {
        "data": [
            {
                "symbol": symbol,
                "quote": [{"symbol": "USD", "price": price, "last_updated": "2026-11-16T00:00:00.000Z"}],
            }
        ],
        "status": {"error_code": 0, "error_message": ""},
    }


def test_missing_key_makes_no_request():
    transport = ScriptedTransport([])
    with pytest.raises(MissingApiKey):
        CmcClient("", transport).latest_usd_quote("BTC")
    assert transport.calls == []


def test_quote_uses_the_header_and_is_not_a_checkout_rate():
    transport = ScriptedTransport([(200, _quote())])
    quote = CmcClient("campaign-key", transport).latest_usd_quote("btc")
    url, headers = transport.calls[0]
    assert headers["X-CMC_PRO_API_KEY"] == "campaign-key"
    assert "campaign-key" not in url
    assert "CMC_PRO_API_KEY" not in url
    assert "/v3/cryptocurrency/quotes/latest" in url
    assert quote["price"] == "63319.87"
    assert quote["round_id"] == ROUND_ID
    assert quote["attribution"] == "Data provided by CoinMarketCap"
    assert quote["checkout_rate"] is False
    assert quote["reference_only"] is True


def test_rate_limit_does_not_return_a_price_that_was_in_the_body():
    body = _quote()
    body["status"] = {"error_code": 1008, "error_message": "minute limit"}
    transport = ScriptedTransport([(429, body)])
    with pytest.raises(RateLimited) as caught:
        CmcClient("campaign-key", transport).latest_usd_quote("BTC")
    assert caught.value.error_code == 1008
    assert not hasattr(caught.value, "price")


def test_float_duplicate_symbol_and_non_usd_quote_are_refused():
    transport = ScriptedTransport([
        (200, _quote(price=1.25)),
        (200, {"data": [_quote()["data"][0], _quote()["data"][0]], "status": {"error_code": 0}}),
        (200, {"data": [{"symbol": "BTC", "quote": {"USD": {"price": "1"}}}], "status": {"error_code": 0}}),
        (200, {"data": [{"symbol": "BTC", "quote": [{"symbol": "EUR", "price": "1"}]}], "status": {"error_code": 0}}),
    ])
    client = CmcClient("campaign-key", transport)
    for _ in range(4):
        with pytest.raises(QuoteUnavailable):
            client.latest_usd_quote("BTC")


def test_from_env_requires_the_campaign_key(monkeypatch):
    monkeypatch.delenv("CMC_API_KEY", raising=False)
    with pytest.raises(MissingApiKey):
        from_env(ScriptedTransport([]))
