"""Opt-in Bitcoin Cash chain-tip probe. It does not look up or send a payment."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

pytestmark = pytest.mark.skipif(os.getenv("BCH_LIVE") != "1", reason="set BCH_LIVE=1")


def test_bch_chain_tip_is_readable_and_no_payment_is_complete():
    request = Request(
        "https://api.blockchair.com/bitcoin-cash/stats",
        headers={"Accept": "application/json", "User-Agent": "DealPilotAI/bch"},
    )
    with urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode())
    data = body.get("data") if isinstance(body, dict) else None
    height = data.get("best_block_height") if isinstance(data, dict) else None
    assert isinstance(height, int) and height > 0
    evidence = {
        "endpoint": "https://api.blockchair.com/bitcoin-cash/stats",
        "best_block_height": height,
        "transaction_requested": False,
        "checkout_complete": False,
        "funds_moved": False,
    }
    path = Path("docs/hackathon-mania/evidence")
    path.mkdir(parents=True, exist_ok=True)
    (path / "bch_chain.json").write_text(json.dumps(evidence, indent=2) + "\n")
