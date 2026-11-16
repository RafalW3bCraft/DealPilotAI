"""Opt-in Lasna chain-id probe. It does not send a transaction."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

pytestmark = pytest.mark.skipif(os.getenv("REACTIVE_LIVE") != "1", reason="set REACTIVE_LIVE=1")

LASNA_CHAIN_ID = "0x512577"


def test_lasna_chain_id_is_5318007_and_no_hash_is_observed():
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}).encode()
    request = Request(
        "https://lasna-rpc.rnk.dev/",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "DealPilotAI/reactive"},
    )
    with urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode())
    chain_id = str(body.get("result", "")).lower()
    assert chain_id == LASNA_CHAIN_ID
    evidence = {
        "rpc": "https://lasna-rpc.rnk.dev/",
        "method": "eth_chainId",
        "chain_id": chain_id,
        "decimal": int(chain_id, 16),
        "observed_testnet_hash": None,
        "cross_chain_settled": False,
        "funds_moved": False,
    }
    path = Path("docs/hackathon-mania/evidence")
    path.mkdir(parents=True, exist_ok=True)
    (path / "reactive_lasna.json").write_text(json.dumps(evidence, indent=2) + "\n")
