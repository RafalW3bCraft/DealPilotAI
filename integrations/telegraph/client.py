"""HTTP client for Telegraph discovery and the Engine ask API.

Discovery is unpaid. An ask without a payment header is expected to return
HTTP 402 on the public dev node. This client never invents a paid result.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

import requests

from .errors import InvalidResponse, ProviderTimeout, TelegraphError
from .schemas import Offering, PaymentOption

ALLOWED_HOSTS = {"devnode.telegraphprotocol.com"}


class HttpResponse:
    def __init__(self, status: int, headers: dict, body: bytes):
        self.status = status
        self.headers = {str(key).lower(): value for key, value in headers.items()}
        self.body = body

    def json(self):
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidResponse("provider response is not JSON") from exc


class Transport(Protocol):
    def request(self, method: str, url: str, headers: dict, body: bytes | None, timeout: float) -> HttpResponse:
        """Perform one HTTP call."""


@dataclass
class RequestsTransport:
    def request(self, method: str, url: str, headers: dict, body: bytes | None, timeout: float) -> HttpResponse:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise TelegraphError("Telegraph URL is not the official dev node")
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=body,
                timeout=timeout,
            )
        except requests.Timeout as exc:
            raise ProviderTimeout("Telegraph request timed out") from exc
        except requests.RequestException as exc:
            raise ProviderTimeout("Telegraph request failed before a response") from exc
        return HttpResponse(response.status_code, dict(response.headers), response.content)


def parse_offerings(payload: object) -> list[Offering]:
    rows = payload
    if isinstance(payload, dict):
        rows = payload.get("miners") or payload.get("data") or []
    if not isinstance(rows, list):
        raise InvalidResponse("miner catalog is not a list")
    offerings: list[Offering] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        intents = tuple(str(item) for item in (row.get("supported_intents") or []) if isinstance(item, str))
        try:
            price = int(row.get("min_price_usdc") or 0)
        except (TypeError, ValueError):
            price = 0
        offerings.append(
            Offering(
                miner_id=str(row.get("id") or ""),
                name=str(row.get("name") or ""),
                slug=str(row.get("slug") or ""),
                intents=intents,
                min_price_atomic=price,
            )
        )
    return offerings


def parse_payment_options(payload: object) -> list[PaymentOption]:
    if not isinstance(payload, dict):
        raise InvalidResponse("payment challenge is not a JSON object")
    accepts = payload.get("accepts")
    if not isinstance(accepts, list) or not accepts:
        raise InvalidResponse("payment challenge has no accepts")
    options: list[PaymentOption] = []
    for item in accepts:
        if not isinstance(item, dict):
            continue
        amount = item.get("amount")
        try:
            atomic = int(str(amount))
        except (TypeError, ValueError):
            continue
        options.append(
            PaymentOption(
                scheme=str(item.get("scheme") or ""),
                network=str(item.get("network") or ""),
                amount_atomic=atomic,
                asset=str(item.get("asset") or ""),
                pay_to=str(item.get("payTo") or item.get("pay_to") or ""),
                max_timeout_seconds=int(item.get("maxTimeoutSeconds") or 60),
            )
        )
    return options


class TelegraphClient:
    def __init__(self, base_url: str, transport: Transport, timeout: float = 20):
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.timeout = timeout

    def _request(self, method: str, url: str, headers: dict, body: bytes | None) -> HttpResponse:
        try:
            return self.transport.request(method, url, headers, body, self.timeout)
        except ProviderTimeout:
            raise
        except TimeoutError as exc:
            raise ProviderTimeout("Telegraph request timed out") from exc

    def discover(self, intent: str | None = None, limit: int = 20) -> list[Offering]:
        url = f"{self.base_url}/api/miners?limit={int(limit)}"
        if intent:
            url += f"&intent={intent}"
        response = self._request(
            "GET",
            url,
            {"Accept": "application/json", "User-Agent": "DealPilotAI"},
            None,
        )
        if response.status != 200:
            raise InvalidResponse(f"miner discovery returned HTTP {response.status}")
        return parse_offerings(response.json())

    def ask(self, intent: str, params: dict, payment_signature: str | None = None) -> HttpResponse:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "DealPilotAI",
        }
        if payment_signature:
            headers["PAYMENT-SIGNATURE"] = payment_signature
        body = json.dumps({"intent": intent, "params": params}, separators=(",", ":")).encode()
        return self._request(
            "POST",
            f"{self.base_url}/engine/v1/ask",
            headers,
            body,
        )
