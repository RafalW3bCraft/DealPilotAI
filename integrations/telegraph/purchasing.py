"""Authorized Telegraph purchase. A 402 without a signature is not success."""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from collections.abc import Callable

from .client import TelegraphClient, parse_payment_options
from .discovery import select_offering
from .errors import (
    InvalidQuote,
    PaymentRejected,
    PaymentRequired,
    ProviderTimeout,
)
from .policy import assert_within_budget, atomic_from_usdc, require_authorization, select_payment_option
from .receipts import ReceiptStore
from .schemas import Receipt
from .verification import verify_price_intelligence

Signer = Callable[[dict], str]


def _idempotency_key(actor_id: str, intent: str, params: dict) -> str:
    payload = json.dumps(
        {"actor_id": actor_id, "intent": intent, "params": params},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _challenge_document(response) -> dict:
    header = response.headers.get("payment-required")
    if header:
        padded = header + "=" * (-len(header) % 4)
        try:
            decoded = json.loads(base64.b64decode(padded))
        except (ValueError, json.JSONDecodeError) as exc:
            raise InvalidQuote("PAYMENT-REQUIRED header is not base64 JSON") from exc
        if isinstance(decoded, dict):
            return decoded
    body = response.json()
    if isinstance(body, dict):
        return body
    raise InvalidQuote("payment challenge is unreadable")


class IntelligencePurchaser:
    def __init__(
        self,
        client: TelegraphClient,
        store: ReceiptStore,
        *,
        preferred_network: str,
        allowed_networks: tuple[str, ...],
        max_spend_usdc: str,
        signer: Signer | None = None,
    ):
        self.client = client
        self.store = store
        self.preferred_network = preferred_network
        self.allowed_networks = allowed_networks
        self.max_spend_atomic = atomic_from_usdc(max_spend_usdc)
        self.signer = signer

    def purchase(
        self,
        *,
        actor_id: str,
        intent: str,
        params: dict,
        budget_usdc: str,
        buyer_authorized: bool,
    ) -> Receipt:
        require_authorization(buyer_authorized)
        key = _idempotency_key(actor_id, intent, params)
        existing = self.store.get(key)
        if existing is not None and existing.paid:
            return existing
        budget_atomic = atomic_from_usdc(budget_usdc)
        try:
            offerings = self.client.discover(intent=intent)
        except ProviderTimeout:
            raise
        offering = select_offering(offerings, intent)
        assert_within_budget(offering.min_price_atomic, budget_atomic, self.max_spend_atomic)
        try:
            challenge_response = self.client.ask(intent, params)
        except ProviderTimeout:
            raise
        if challenge_response.status != 402:
            raise PaymentRejected(
                f"expected HTTP 402 before payment, got HTTP {challenge_response.status}"
            )
        challenge = _challenge_document(challenge_response)
        option = select_payment_option(
            parse_payment_options(challenge),
            preferred_network=self.preferred_network,
            allowed_networks=self.allowed_networks,
        )
        assert_within_budget(option.amount_atomic, budget_atomic, self.max_spend_atomic)
        if self.signer is None:
            raise PaymentRequired("payment signer is not configured", challenge)
        try:
            signature = self.signer(challenge)
        except PaymentRequired:
            raise
        except Exception as exc:
            raise PaymentRejected("payment signature was not created") from exc
        if not isinstance(signature, str) or not signature:
            raise PaymentRejected("payment signature was empty")
        try:
            paid_response = self.client.ask(intent, params, payment_signature=signature)
        except ProviderTimeout:
            raise
        if paid_response.status == 402:
            raise PaymentRejected("signed payment was not accepted")
        if paid_response.status != 200:
            raise PaymentRejected(f"paid ask returned HTTP {paid_response.status}")
        intelligence = verify_price_intelligence(
            paid_response.json(),
            intent=intent,
            params=params,
            miner_id=offering.miner_id,
        )
        receipt = Receipt(
            idempotency_key=key,
            workflow_id=str(uuid.uuid4()),
            intent=intent,
            params=dict(params),
            amount_atomic=option.amount_atomic,
            network=option.network,
            asset=option.asset,
            pay_to=option.pay_to,
            miner_id=offering.miner_id,
            signal_hash=intelligence.signal_hash,
            price_usd=str(intelligence.price_usd),
            paid=True,
        )
        return self.store.save(receipt)
