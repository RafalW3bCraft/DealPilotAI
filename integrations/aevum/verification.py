"""Settle an invoice only from an observed tUSD8 Transfer on Aevum."""

from __future__ import annotations

from .config import TRANSFER_TOPIC, TUSD8
from .errors import DuplicatePayment, PaymentUnverified
from .invoices import Invoice, InvoiceStore
from .rpc import JsonRpc, require_aevum_chain


class InvoiceSettler:
    def __init__(self, rpc: JsonRpc, store: InvoiceStore):
        self.rpc = rpc
        self.store = store

    def settle(self, invoice_id: str, tx_hash: str) -> Invoice:
        invoice = self.store.get(invoice_id)
        normalized = _tx_hash(tx_hash)
        if invoice.tx_hash:
            if invoice.tx_hash == normalized and invoice.status in {"paid", "requires_review"}:
                return invoice
            raise DuplicatePayment("invoice is already bound to a transaction")
        existing = self.store.find_by_tx(normalized)
        if existing is not None and existing.invoice_id != invoice.invoice_id:
            raise DuplicatePayment("transaction is already bound to another invoice")
        require_aevum_chain(self.rpc)
        receipt = self.rpc.call("eth_getTransactionReceipt", [normalized])
        if not isinstance(receipt, dict):
            raise PaymentUnverified("transaction receipt was not found")
        if str(receipt.get("status", "")).lower() != "0x1":
            return self.store.mark(invoice.invoice_id, "failed", None)
        transfer = _matching_transfer(receipt, invoice.merchant, invoice.amount_atomic)
        if transfer == "exact":
            return self.store.mark(invoice.invoice_id, "paid", normalized)
        if transfer == "over":
            return self.store.mark(invoice.invoice_id, "requires_review", normalized)
        return self.store.mark(invoice.invoice_id, "failed", None)


def _tx_hash(value: str) -> str:
    text = value.strip().lower()
    if not text.startswith("0x") or len(text) != 66:
        raise PaymentUnverified("transaction hash is not 32 bytes")
    try:
        int(text[2:], 16)
    except ValueError as exc:
        raise PaymentUnverified("transaction hash is not 32 bytes") from exc
    return text


def _matching_transfer(receipt: dict, merchant: str, amount: int) -> str:
    logs = receipt.get("logs")
    if not isinstance(logs, list):
        raise PaymentUnverified("receipt has no logs")
    token = TUSD8.lower()
    expected_to = _topic_address(merchant)
    outcome = "none"
    for log in logs:
        if not isinstance(log, dict):
            continue
        if str(log.get("address", "")).lower() != token:
            continue
        topics = log.get("topics")
        if not isinstance(topics, list) or len(topics) < 3:
            continue
        if str(topics[0]).lower() != TRANSFER_TOPIC:
            continue
        if str(topics[2]).lower() != expected_to:
            continue
        moved = _data_amount(log.get("data"))
        if moved == amount:
            return "exact"
        if moved > amount:
            outcome = "over"
    return outcome


def _topic_address(address: str) -> str:
    return "0x" + address.lower().removeprefix("0x").rjust(64, "0")


def _data_amount(data: object) -> int:
    if not isinstance(data, str) or not data.startswith("0x"):
        raise PaymentUnverified("transfer amount is unreadable")
    try:
        return int(data, 16)
    except ValueError as exc:
        raise PaymentUnverified("transfer amount is unreadable") from exc
