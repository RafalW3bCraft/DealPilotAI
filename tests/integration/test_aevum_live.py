"""Opt-in probe of the published Aevum RPC. It does not send a transaction."""

import json
import os
from pathlib import Path

import pytest

from integrations.aevum.config import AEVUM_CHAIN_HEX
from integrations.aevum.rpc import JsonRpc, require_aevum_chain


pytestmark = pytest.mark.skipif(os.getenv("AEVUM_LIVE") != "1", reason="set AEVUM_LIVE=1")


def test_aevum_chain_id_is_44005():
    chain_id = require_aevum_chain(JsonRpc(os.getenv("AEVUM_RPC_URL", "https://rpc-test.qday.info")))
    assert chain_id == AEVUM_CHAIN_HEX
    evidence = Path("docs/hackathon-mania/evidence")
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "aevum_chain.json").write_text(
        json.dumps(
            {
                "rpc": os.getenv("AEVUM_RPC_URL", "https://rpc-test.qday.info"),
                "chain_id": chain_id,
                "decimal": int(chain_id, 16),
                "paid": False,
            },
            indent=2,
        )
        + "\n"
    )
