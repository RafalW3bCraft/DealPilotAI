"""Validate a purchased intelligence body before the app uses it."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .errors import InvalidResponse
from .schemas import Intelligence


_PRICE_KEYS = ("price_usd", "usd_price", "price")
_NESTED = ("output", "result", "data", "signal", "answer")


def _as_decimal(value) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if not isinstance(value, (int, float, str, Decimal)):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    return parsed


def _price_candidates(body: dict) -> list[Decimal]:
    found: list[Decimal] = []
    containers = [body]
    containers.extend(body[key] for key in _NESTED if isinstance(body.get(key), dict))
    for container in containers:
        for key in _PRICE_KEYS:
            parsed = _as_decimal(container.get(key))
            if parsed is not None:
                found.append(parsed)
    unique = []
    for price in found:
        if all(price != existing for existing in unique):
            unique.append(price)
    return unique


def _provenance(body: dict) -> str:
    for key in ("signal_hash", "request_id", "job_id"):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def verify_price_intelligence(body: object, *, intent: str, params: dict, miner_id: str) -> Intelligence:
    """Accept one positive USD price and a provider provenance identifier."""
    if not isinstance(body, dict):
        raise InvalidResponse("provider response is not a JSON object")
    prices = _price_candidates(body)
    if len(prices) != 1:
        raise InvalidResponse("provider response does not contain one positive USD price")
    provenance = _provenance(body)
    if not provenance:
        raise InvalidResponse("provider response has no provenance identifier")
    echoed = body.get("input")
    if isinstance(echoed, dict) and echoed.get("symbol") not in (None, params.get("symbol")):
        raise InvalidResponse("provider response symbol does not match the request")
    return Intelligence(
        intent=intent,
        params=dict(params),
        price_usd=prices[0],
        signal_hash=provenance,
        miner_id=miner_id,
        raw=body,
    )
