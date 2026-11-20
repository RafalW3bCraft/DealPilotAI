"""Minimal JSON-RPC client. A missing or wrong chain id is not a payment."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AEVUM_CHAIN_HEX
from .errors import ChainMismatch, PaymentUnverified


class JsonRpc:
    def __init__(self, url: str, timeout: float = 20):
        self.url = url
        self.timeout = timeout

    def call(self, method: str, params: list) -> object:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        request = Request(
            self.url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "DealPilotAI/aevum",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise PaymentUnverified("Aevum RPC did not return a readable result") from exc
        if not isinstance(payload, dict) or payload.get("error"):
            raise PaymentUnverified("Aevum RPC returned an error")
        return payload.get("result")


def require_aevum_chain(rpc: JsonRpc) -> str:
    chain_id = rpc.call("eth_chainId", [])
    if not isinstance(chain_id, str) or chain_id.lower() != AEVUM_CHAIN_HEX:
        raise ChainMismatch(f"expected {AEVUM_CHAIN_HEX}")
    return chain_id.lower()
