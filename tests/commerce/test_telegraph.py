"""Telegraph purchase policy, with a scripted HTTP transport and no network."""

import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

from integrations.telegraph.client import HttpResponse, TelegraphClient
from integrations.telegraph.errors import (
    AuthorizationDenied,
    BudgetExceeded,
    InvalidQuote,
    InvalidResponse,
    PaymentRejected,
    PaymentRequired,
    ProviderTimeout,
    UnsupportedIntent,
)
from integrations.telegraph.purchasing import IntelligencePurchaser
from integrations.telegraph.receipts import ReceiptStore
from integrations.telegraph.workflow import CommerceIntelligence, requested_symbol


CHALLENGE = {
    "x402Version": 2,
    "accepts": [
        {
            "scheme": "exact",
            "network": "eip155:11155111",
            "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
            "amount": "10000",
            "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b",
            "maxTimeoutSeconds": 60,
        }
    ],
}


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body))
        if not self.responses:
            raise AssertionError("unexpected HTTP call")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _json_response(status, payload, headers=None):
    return HttpResponse(status, headers or {}, json.dumps(payload).encode())


def _miner(intent="CRYPTO_PRICE_USD", price=10000):
    return {
        "id": "9002",
        "name": "TxLens",
        "slug": "txlens",
        "supported_intents": [intent],
        "min_price_usdc": price,
    }


def _paid_body():
    return {
        "input": {"symbol": "BTC"},
        "price_usd": "100000.00",
        "signal_hash": "0xabc",
    }


def _purchaser(transport, store, signer=None, ceiling="0.05"):
    client = TelegraphClient("https://devnode.telegraphprotocol.com", transport, timeout=5)
    return IntelligencePurchaser(
        client,
        store,
        preferred_network="eip155:11155111",
        allowed_networks=("eip155:11155111", "eip155:84532"),
        max_spend_usdc=ceiling,
        signer=signer,
    )


def _buy(purchaser, **overrides):
    payload = {
        "actor_id": "buyer-1",
        "intent": "CRYPTO_PRICE_USD",
        "params": {"symbol": "BTC"},
        "budget_usdc": "0.02",
        "buyer_authorized": True,
    }
    payload.update(overrides)
    return purchaser.purchase(**payload)


def test_provider_discovery_selects_advertised_intent(tmp_path):
    transport = ScriptedTransport([
        _json_response(200, [_miner(), _miner("WEATHER_CHECK_TEMPERATURE")]),
        _json_response(402, CHALLENGE),
        _json_response(200, _paid_body()),
    ])
    receipt = _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite"), signer=lambda _c: "sig"))
    assert receipt.miner_id == "9002"
    assert receipt.paid is True
    assert transport.calls[0][0] == "GET"


def test_unsupported_intent_does_not_ask(tmp_path):
    transport = ScriptedTransport([_json_response(200, [_miner("WEATHER_CHECK_TEMPERATURE")])])
    with pytest.raises(UnsupportedIntent):
        _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite")))
    assert all(call[0] == "GET" for call in transport.calls)


def test_invalid_quote_is_rejected(tmp_path):
    broken = {"accepts": [{"scheme": "exact", "network": "eip155:11155111", "amount": "nope"}]}
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, broken),
    ])
    with pytest.raises(InvalidQuote):
        _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite"), signer=lambda _c: "sig"))


def test_budget_exceeded_before_signature(tmp_path):
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
    ])
    signed = []
    with pytest.raises(BudgetExceeded):
        _buy(
            _purchaser(transport, ReceiptStore(tmp_path / "r.sqlite"), signer=lambda _c: signed.append("x") or "sig"),
            budget_usdc="0.001",
        )
    assert signed == []


def test_authorization_denied_before_network(tmp_path):
    transport = ScriptedTransport([])
    with pytest.raises(AuthorizationDenied):
        _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite")), buyer_authorized=False)
    assert transport.calls == []


def test_purchase_success_records_paid_receipt(tmp_path):
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
        _json_response(200, _paid_body()),
    ])
    receipt = _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite"), signer=lambda _c: "sig"))
    assert receipt.paid is True
    assert receipt.price_usd == "100000.00"
    assert receipt.amount_atomic == 10000
    assert receipt.network == "eip155:11155111"
    assert "PAYMENT-SIGNATURE" in transport.calls[2][2]


def test_missing_signer_is_payment_required_not_success(tmp_path):
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
    ])
    with pytest.raises(PaymentRequired) as caught:
        _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite")))
    assert caught.value.challenge["x402Version"] == 2
    assert ReceiptStore(tmp_path / "r.sqlite").get(caught.value.challenge.get("idempotency", "")) is None


def test_provider_timeout(tmp_path):
    transport = ScriptedTransport([TimeoutError("slow")])
    with pytest.raises(ProviderTimeout):
        _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite")))


def test_invalid_response_is_not_stored(tmp_path):
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
        _json_response(200, {"price_usd": "1", "input": {"symbol": "ETH"}}),
    ])
    store = ReceiptStore(tmp_path / "r.sqlite")
    with pytest.raises(InvalidResponse):
        _buy(_purchaser(transport, store, signer=lambda _c: "sig"))
    assert store.get("missing") is None


def test_duplicate_purchase_does_not_call_the_network_again(tmp_path):
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
        _json_response(200, _paid_body()),
    ])
    store = ReceiptStore(tmp_path / "r.sqlite")
    purchaser = _purchaser(transport, store, signer=lambda _c: "sig")
    first = _buy(purchaser)
    second = _buy(purchaser)
    assert second.idempotency_key == first.idempotency_key
    assert second.signal_hash == first.signal_hash
    assert len(transport.calls) == 3


def test_receipt_survives_a_new_store(tmp_path):
    path = tmp_path / "r.sqlite"
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
        _json_response(200, _paid_body()),
    ])
    first = _buy(_purchaser(transport, ReceiptStore(path), signer=lambda _c: "sig"))
    reopened = ReceiptStore(path).get(first.idempotency_key)
    assert reopened is not None
    assert reopened.paid is True
    assert reopened.signal_hash == "0xabc"


def test_conflicting_prices_fail_verification(tmp_path):
    body = {"price_usd": "1", "output": {"price_usd": "2"}, "signal_hash": "0xabc"}
    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
        _json_response(200, body),
    ])
    with pytest.raises(InvalidResponse):
        _buy(_purchaser(transport, ReceiptStore(tmp_path / "r.sqlite"), signer=lambda _c: "sig"))


def test_downstream_reference_does_not_change_catalog_price(tmp_path):
    product = SimpleNamespace(sku="DP-LAMP-001", title="Lamp", price=Decimal("24.99"), currency="USD")

    class Catalog:
        def search_products(self, query, limit=4):
            return [product]

    transport = ScriptedTransport([
        _json_response(200, [_miner()]),
        _json_response(402, CHALLENGE),
        _json_response(200, _paid_body()),
    ])
    workflow = CommerceIntelligence(
        _purchaser(transport, ReceiptStore(tmp_path / "r.sqlite"), signer=lambda _c: "sig"),
        Catalog(),
    )
    advice = workflow.advise(
        "desk lamp and current bitcoin price",
        actor_id="buyer-1",
        budget_usdc="0.02",
        buyer_authorized=True,
    )
    assert advice["products"][0]["price"] == "24.99"
    assert advice["catalog_prices_unchanged"] is True
    assert advice["intelligence"]["paid"] is True
    assert advice["intelligence"]["budget_context"][0]["reference_asset_amount"] == "0.00024990"
    assert requested_symbol("bitcoin cash checkout") == "BCH"


def test_route_requires_authorization_and_can_return_paid_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-private-session-key-0123456789")
    monkeypatch.setenv("ENABLE_MERCHANT_CHECKOUT", "true")
    monkeypatch.setenv("COMMERCE_DATABASE_URL", f"sqlite:///{tmp_path}/commerce.db")
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "")
    monkeypatch.setenv("DASHBOARD_TOKEN", "")
    monkeypatch.setenv("AI_PROVIDER", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("FEATHERLESS_API_KEY", "")
    monkeypatch.setenv("DATABASE_URL", "")
    from config import Config
    from web_dashboard_clean import create_app
    import web.commerce_routes as routes

    app = create_app(Config())
    with app.test_request_context("/"):
        routes._build_services(Config())
    client = app.test_client()
    token = client.get("/api/csrf").get_json()["csrf_token"]
    denied = client.post(
        "/api/intelligence/telegraph",
        json={"query": "lamp", "buyer_authorized": False, "budget_usdc": "0.02", "csrf_token": token},
    )
    assert denied.status_code == 403
    assert "authorization" in denied.get_json()["error"]

    class FakeWorkflow:
        def advise(self, query, **kwargs):
            return {
                "products": [{"sku": "DP-LAMP-001", "price": "24.99", "currency": "USD"}],
                "catalog_prices_unchanged": True,
                "intelligence": {"paid": True, "price_usd": "100000.00", "signal_hash": "0xabc"},
                "missing_info": [],
            }

    monkeypatch.setattr("integrations.telegraph.workflow.build_workflow", lambda *args, **kwargs: FakeWorkflow())
    token = client.get("/api/csrf").get_json()["csrf_token"]
    accepted = client.post(
        "/api/intelligence/telegraph",
        json={"query": "desk lamp bitcoin", "buyer_authorized": True, "budget_usdc": "0.02", "csrf_token": token},
    )
    assert accepted.status_code == 200
    body = accepted.get_json()
    assert body["intelligence"]["paid"] is True
    assert body["products"][0]["price"] == "24.99"


def test_signer_refuses_to_mark_paid_when_x402_is_missing(monkeypatch):
    import builtins

    from integrations.telegraph.signing import X402ExactSigner

    real_import = builtins.__import__

    def hiding_x402(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "x402" or name.startswith("x402."):
            raise ImportError(name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", hiding_x402)
    signer = X402ExactSigner("0x" + "11" * 32, "eip155:11155111")
    with pytest.raises(PaymentRejected):
        signer({"x402Version": 2, "accepts": []})
