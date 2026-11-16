"""Live Telegraph dev-node checks.

These hit the public dev node and are skipped unless TELEGRAPH_LIVE=1.
An unpaid ask must stay unpaid. This file does not claim a completed purchase.
"""

import json
import os
from pathlib import Path

import pytest

from integrations.telegraph.client import RequestsTransport, TelegraphClient
from integrations.telegraph.errors import PaymentRequired
from integrations.telegraph.purchasing import IntelligencePurchaser
from integrations.telegraph.receipts import ReceiptStore

pytestmark = pytest.mark.skipif(
    os.getenv("TELEGRAPH_LIVE") != "1",
    reason="set TELEGRAPH_LIVE=1 to contact the Telegraph dev node",
)


def test_live_discovery_and_unpaid_ask_returns_402(tmp_path):
    client = TelegraphClient("https://devnode.telegraphprotocol.com", RequestsTransport(), timeout=30)
    offerings = client.discover(intent="CRYPTO_PRICE_USD", limit=5)
    assert any("CRYPTO_PRICE_USD" in item.intents for item in offerings)
    purchaser = IntelligencePurchaser(
        client,
        ReceiptStore(tmp_path / "live.sqlite"),
        preferred_network="eip155:11155111",
        allowed_networks=("eip155:11155111", "eip155:84532"),
        max_spend_usdc="0.05",
        signer=None,
    )
    with pytest.raises(PaymentRequired) as caught:
        purchaser.purchase(
            actor_id="live-probe",
            intent="CRYPTO_PRICE_USD",
            params={"symbol": "BTC"},
            budget_usdc="0.05",
            buyer_authorized=True,
        )
    networks = sorted({item.get("network") for item in caught.value.challenge.get("accepts", [])})
    assert "eip155:11155111" in networks
    evidence = {
        "environment": "https://devnode.telegraphprotocol.com",
        "intent": "CRYPTO_PRICE_USD",
        "paid": False,
        "outcome": "HTTP 402 payment required",
        "networks": networks,
        "x402_version": caught.value.challenge.get("x402Version"),
    }
    destination = os.getenv("TELEGRAPH_EVIDENCE_PATH")
    if destination:
        Path(destination).write_text(json.dumps(evidence, indent=2), encoding="utf-8")
