"""Aevum invoice settlement against a scripted RPC. No network and no signing."""

from pathlib import Path

import pytest

from integrations.aevum.config import AEVUM_CHAIN_HEX, TRANSFER_TOPIC, TUSD8
from integrations.aevum.errors import ChainMismatch, DuplicatePayment, PaymentUnverified
from integrations.aevum.invoices import InvoiceStore, atomic_from_units
from integrations.aevum.verification import InvoiceSettler


MERCHANT = "0x1111111111111111111111111111111111111111"
OTHER = "0x2222222222222222222222222222222222222222"
TX = "0x" + "ab" * 32


class ScriptedRpc:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        item = self.results.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _topic(address: str) -> str:
    return "0x" + address.lower().removeprefix("0x").rjust(64, "0")


def _receipt(to: str, amount: int, status: str = "0x1", token: str = TUSD8):
    return {
        "status": status,
        "logs": [
            {
                "address": token,
                "topics": [TRANSFER_TOPIC, _topic(OTHER), _topic(to)],
                "data": hex(amount),
            }
        ],
    }


def _settler(tmp_path: Path, results) -> tuple[InvoiceSettler, InvoiceStore, ScriptedRpc]:
    store = InvoiceStore(tmp_path / "invoices.sqlite")
    rpc = ScriptedRpc(results)
    return InvoiceSettler(rpc, store), store, rpc


def test_atomic_units_reject_floats_and_extra_precision():
    assert atomic_from_units("1") == 1_000_000
    assert atomic_from_units("0.000001") == 1
    assert atomic_from_units("1.50") == 1_500_000
    with pytest.raises(ValueError):
        atomic_from_units("1.1234567")
    with pytest.raises(ValueError):
        atomic_from_units("0")


def test_exact_transfer_marks_paid_and_restart_is_idempotent(tmp_path):
    settler, store, rpc = _settler(
        tmp_path,
        [AEVUM_CHAIN_HEX, _receipt(MERCHANT, 1_500_000)],
    )
    invoice = store.create(MERCHANT, 1_500_000)
    paid = settler.settle(invoice.invoice_id, TX)
    assert paid.status == "paid"
    assert paid.tx_hash == TX
    again = settler.settle(invoice.invoice_id, TX)
    assert again.status == "paid"
    assert rpc.calls[0][0] == "eth_chainId"
    reopened = InvoiceSettler(ScriptedRpc([]), InvoiceStore(tmp_path / "invoices.sqlite"))
    assert reopened.settle(invoice.invoice_id, TX).status == "paid"


def test_wrong_chain_does_not_mark_paid(tmp_path):
    settler, store, _rpc = _settler(tmp_path, ["0x1"])
    invoice = store.create(MERCHANT, 1)
    with pytest.raises(ChainMismatch):
        settler.settle(invoice.invoice_id, TX)
    assert store.get(invoice.invoice_id).status == "awaiting_payment"


def test_underpayment_and_wrong_token_are_not_paid(tmp_path):
    settler, store, _rpc = _settler(
        tmp_path,
        [
            AEVUM_CHAIN_HEX,
            _receipt(MERCHANT, 10),
            AEVUM_CHAIN_HEX,
            _receipt(MERCHANT, 1_000_000, token="0x0000000000000000000000000000000000000001"),
        ],
    )
    invoice = store.create(MERCHANT, 1_000_000)
    failed = settler.settle(invoice.invoice_id, TX)
    assert failed.status == "failed"
    assert failed.tx_hash is None
    other = "0x" + "cd" * 32
    still = settler.settle(invoice.invoice_id, other)
    assert still.status == "failed"


def test_overpayment_requires_review_and_cannot_pay_another_invoice(tmp_path):
    settler, store, _rpc = _settler(
        tmp_path,
        [AEVUM_CHAIN_HEX, _receipt(MERCHANT, 2_000_000)],
    )
    invoice = store.create(MERCHANT, 1_000_000)
    reviewed = settler.settle(invoice.invoice_id, TX)
    assert reviewed.status == "requires_review"
    second = store.create(MERCHANT, 2_000_000)
    with pytest.raises(DuplicatePayment):
        settler.settle(second.invoice_id, TX)
    assert store.get(second.invoice_id).status == "awaiting_payment"


def test_missing_receipt_is_not_success(tmp_path):
    settler, store, _rpc = _settler(tmp_path, [AEVUM_CHAIN_HEX, None])
    invoice = store.create(MERCHANT, 1)
    with pytest.raises(PaymentUnverified):
        settler.settle(invoice.invoice_id, TX)
    assert store.get(invoice.invoice_id).status == "awaiting_payment"


def test_paid_invoice_rejects_a_second_transaction(tmp_path):
    settler, store, rpc = _settler(
        tmp_path,
        [AEVUM_CHAIN_HEX, _receipt(MERCHANT, 1)],
    )
    invoice = store.create(MERCHANT, 1)
    assert settler.settle(invoice.invoice_id, TX).status == "paid"
    other = "0x" + "11" * 32
    with pytest.raises(DuplicatePayment):
        settler.settle(invoice.invoice_id, other)
    assert store.get(invoice.invoice_id).tx_hash == TX
    assert rpc.calls == [("eth_chainId", []), ("eth_getTransactionReceipt", [TX])]


def test_rpc_transport_errors_are_not_a_payment(monkeypatch):
    from urllib.error import URLError

    from integrations.aevum.rpc import JsonRpc

    def broken(*_args, **_kwargs):
        raise URLError("down")

    monkeypatch.setattr("integrations.aevum.rpc.urlopen", broken)
    with pytest.raises(PaymentUnverified):
        JsonRpc("https://rpc-test.qday.info").call("eth_chainId", [])

    class ErrorBody:
        status = 200

        def read(self):
            return b'{"jsonrpc":"2.0","id":1,"error":{"code":-32000,"message":"no"}}'

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr("integrations.aevum.rpc.urlopen", lambda *_args, **_kwargs: ErrorBody())
    with pytest.raises(PaymentUnverified):
        JsonRpc("https://rpc-test.qday.info").call("eth_chainId", [])


def test_failed_transaction_status_is_not_paid(tmp_path):
    settler, store, _rpc = _settler(
        tmp_path,
        [AEVUM_CHAIN_HEX, _receipt(MERCHANT, 1, status="0x0")],
    )
    invoice = store.create(MERCHANT, 1)
    failed = settler.settle(invoice.invoice_id, TX)
    assert failed.status == "failed"
    assert failed.tx_hash is None
