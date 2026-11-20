"""Typed records for Telegraph discovery, payment, and receipts."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


USDC_ATOMIC = Decimal(1_000_000)
ALLOWED_SYMBOLS = ("BTC", "ETH", "SOL", "BCH")


@dataclass(frozen=True)
class Offering:
    miner_id: str
    name: str
    intents: tuple[str, ...]
    min_price_atomic: int
    slug: str = ""


@dataclass(frozen=True)
class PaymentOption:
    scheme: str
    network: str
    amount_atomic: int
    asset: str
    pay_to: str
    max_timeout_seconds: int = 60

    @property
    def amount_usdc(self) -> Decimal:
        return (Decimal(self.amount_atomic) / USDC_ATOMIC).quantize(Decimal("0.000001"))


@dataclass(frozen=True)
class Intelligence:
    intent: str
    params: dict
    price_usd: Decimal
    signal_hash: str
    miner_id: str
    raw: dict = field(repr=False)


@dataclass(frozen=True)
class Receipt:
    idempotency_key: str
    workflow_id: str
    intent: str
    params: dict
    amount_atomic: int
    network: str
    asset: str
    pay_to: str
    miner_id: str
    signal_hash: str
    price_usd: str
    paid: bool

    @property
    def cost_usdc(self) -> str:
        return str((Decimal(self.amount_atomic) / USDC_ATOMIC).quantize(Decimal("0.000001")))
