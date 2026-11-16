"""Match a BCH transaction document to a merchant cashaddr and an amount.

The transaction id is only a lookup key. The document must name that same id
and include an output. This module has no signing path.
"""

from __future__ import annotations

from .errors import PaymentUnverified

CASHADDR_CHARSET = set("qpzry9x8gf2tvdw0s3jn54khce6mua7l")
PREFIXES = {"mainnet": "bitcoincash:", "chipnet": "bchtest:"}


class BchObserver:
    def __init__(self, merchant: str, network: str = "mainnet", min_confirmations: int = 1):
        if network not in PREFIXES:
            raise ValueError("network must be mainnet or chipnet")
        if isinstance(min_confirmations, bool) or not isinstance(min_confirmations, int) or min_confirmations < 1:
            raise ValueError("min_confirmations must be a positive integer")
        self.merchant = _cashaddr(merchant, PREFIXES[network])
        self.network = network
        self.min_confirmations = min_confirmations

    def observe(self, txid: str, expected_sats: int, document: dict) -> dict:
        normalized = _txid(txid)
        if isinstance(expected_sats, bool) or not isinstance(expected_sats, int) or expected_sats <= 0:
            raise PaymentUnverified("expected amount must be a positive integer of satoshis")
        if not isinstance(document, dict) or str(document.get("txid", "")).lower() != normalized:
            raise PaymentUnverified("chain document is for a different transaction")
        confirmations = document.get("confirmations")
        if isinstance(confirmations, bool) or not isinstance(confirmations, int) or confirmations < 0:
            raise PaymentUnverified("chain document has no confirmation count")
        outputs = document.get("outputs")
        if not isinstance(outputs, list):
            raise PaymentUnverified("chain document has no outputs")
        paid_to_merchant = _merchant_total(outputs, self.merchant)
        status = "awaiting_payment"
        if confirmations >= self.min_confirmations and paid_to_merchant == expected_sats:
            status = "matched"
        elif confirmations >= self.min_confirmations and paid_to_merchant > expected_sats:
            status = "requires_review"
        return {
            "network": self.network,
            "txid": normalized,
            "merchant": self.merchant,
            "expected_sats": expected_sats,
            "observed_sats": paid_to_merchant,
            "confirmations": confirmations,
            "status": status,
            "checkout_complete": False,
            "funds_moved": False,
        }


def from_blockchair(payload: dict, txid: str) -> dict:
    """Normalize a Blockchair dashboard payload. A missing output stays unverified."""
    normalized = _txid(txid)
    if not isinstance(payload, dict):
        raise PaymentUnverified("chain document is for a different transaction")
    data = payload.get("data")
    entry = data.get(normalized) if isinstance(data, dict) else None
    if not isinstance(entry, dict):
        raise PaymentUnverified("chain document is for a different transaction")
    transaction = entry.get("transaction")
    if not isinstance(transaction, dict) or str(transaction.get("hash", "")).lower() != normalized:
        raise PaymentUnverified("chain document is for a different transaction")
    block_id = transaction.get("block_id")
    state = payload.get("context", {}).get("state") if isinstance(payload.get("context"), dict) else None
    if isinstance(block_id, bool) or not isinstance(block_id, int) or block_id <= 0:
        confirmations = 0
    elif isinstance(state, bool) or not isinstance(state, int) or state < block_id:
        raise PaymentUnverified("chain document has no confirmation count")
    else:
        confirmations = state - block_id + 1
    raw_outputs = entry.get("outputs")
    if not isinstance(raw_outputs, list):
        raise PaymentUnverified("chain document has no outputs")
    outputs = []
    for output in raw_outputs:
        if not isinstance(output, dict):
            continue
        value = output.get("value")
        if isinstance(value, bool) or not isinstance(value, int):
            raise PaymentUnverified("chain document has no outputs")
        outputs.append({"address": str(output.get("recipient", "")).lower(), "value_sats": value})
    return {"txid": normalized, "confirmations": confirmations, "outputs": outputs}


def _cashaddr(address: str, prefix: str) -> str:
    text = address.strip().lower()
    if not text.startswith(prefix):
        raise ValueError("merchant must be a cashaddr for the selected network")
    body = text[len(prefix):]
    if not body or any(char not in CASHADDR_CHARSET for char in body):
        raise ValueError("merchant must be a cashaddr for the selected network")
    return text


def _txid(txid: str) -> str:
    text = txid.strip().lower()
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise PaymentUnverified("transaction id must be 32 bytes of hex")
    return text


def _merchant_total(outputs: list, merchant: str) -> int:
    total = 0
    for output in outputs:
        if not isinstance(output, dict):
            continue
        if str(output.get("address", "")).lower() != merchant:
            continue
        value = output.get("value_sats")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PaymentUnverified("chain document has no outputs")
        total += value
    return total
