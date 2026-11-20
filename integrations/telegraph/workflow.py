"""Bind a verified Telegraph price to merchant catalog totals.

The external price is evidence. It does not replace the catalog price and it
does not authorize a customer payment.
"""

from __future__ import annotations

import re
from decimal import Decimal

from .client import RequestsTransport, TelegraphClient
from .purchasing import IntelligencePurchaser
from .receipts import ReceiptStore
from .schemas import ALLOWED_SYMBOLS
from .signing import X402ExactSigner

_SYMBOL_PATTERNS = (
    ("BCH", re.compile(r"\b(?:bitcoin\s+cash|bch)\b", re.IGNORECASE)),
    ("BTC", re.compile(r"\b(?:bitcoin|btc)\b", re.IGNORECASE)),
    ("ETH", re.compile(r"\b(?:ethereum|eth)\b", re.IGNORECASE)),
    ("SOL", re.compile(r"\b(?:solana|sol)\b", re.IGNORECASE)),
)


def requested_symbol(query: str, explicit: str | None = None) -> str | None:
    if explicit:
        symbol = explicit.strip().upper()
        if symbol not in ALLOWED_SYMBOLS:
            raise ValueError("symbol is not a supported reference asset")
        return symbol
    text = query or ""
    bch = _SYMBOL_PATTERNS[0][1]
    if bch.search(text):
        remainder = bch.sub(" ", text)
        others = [symbol for symbol, pattern in _SYMBOL_PATTERNS[1:] if pattern.search(remainder)]
        if others:
            raise ValueError("query names more than one reference asset")
        return "BCH"
    found = [symbol for symbol, pattern in _SYMBOL_PATTERNS[1:] if pattern.search(text)]
    if len(found) > 1:
        raise ValueError("query names more than one reference asset")
    return found[0] if found else None


class CommerceIntelligence:
    def __init__(self, purchaser: IntelligencePurchaser, catalog):
        self.purchaser = purchaser
        self.catalog = catalog

    def advise(
        self,
        query: str,
        *,
        actor_id: str,
        budget_usdc: str,
        buyer_authorized: bool,
        symbol: str | None = None,
    ) -> dict:
        products = self.catalog.search_products(query, limit=4)
        chosen = requested_symbol(query, symbol)
        product_rows = [
            {
                "sku": product.sku,
                "title": product.title,
                "price": str(product.price),
                "currency": product.currency,
            }
            for product in products
        ]
        if chosen is None:
            return {
                "products": product_rows,
                "intelligence": None,
                "missing_info": ["No external market reference was requested."],
                "catalog_prices_unchanged": True,
            }
        receipt = self.purchaser.purchase(
            actor_id=actor_id,
            intent="CRYPTO_PRICE_USD",
            params={"symbol": chosen},
            budget_usdc=budget_usdc,
            buyer_authorized=buyer_authorized,
        )
        reference = Decimal(receipt.price_usd)
        comparisons = []
        for product in products:
            if product.currency != "USD":
                continue
            asset_amount = (product.price / reference).quantize(Decimal("0.00000001"))
            comparisons.append(
                {
                    "sku": product.sku,
                    "usd": str(product.price),
                    "reference_asset": chosen,
                    "reference_asset_amount": str(asset_amount),
                }
            )
        return {
            "products": product_rows,
            "missing_info": [],
            "catalog_prices_unchanged": True,
            "intelligence": {
                "paid": receipt.paid,
                "intent": receipt.intent,
                "symbol": chosen,
                "price_usd": receipt.price_usd,
                "cost_usdc": receipt.cost_usdc,
                "network": receipt.network,
                "asset": receipt.asset,
                "pay_to": receipt.pay_to,
                "miner_id": receipt.miner_id,
                "signal_hash": receipt.signal_hash,
                "workflow_id": receipt.workflow_id,
                "budget_context": comparisons,
            },
        }


def build_workflow(config, catalog, transport=None, signer=None):
    client = TelegraphClient(
        config.TELEGRAPH_BASE_URL,
        transport or RequestsTransport(),
        timeout=config.TELEGRAPH_TIMEOUT_SECONDS,
    )
    if signer is None and config.TELEGRAPH_PRIVATE_KEY:
        signer = X402ExactSigner(config.TELEGRAPH_PRIVATE_KEY, config.TELEGRAPH_NETWORK)
    purchaser = IntelligencePurchaser(
        client,
        ReceiptStore(config.TELEGRAPH_RECEIPT_DB),
        preferred_network=config.TELEGRAPH_NETWORK,
        allowed_networks=config.TELEGRAPH_ALLOWED_NETWORKS,
        max_spend_usdc=config.TELEGRAPH_MAX_SPEND_USDC,
        signer=signer,
    )
    return CommerceIntelligence(purchaser, catalog)
