"""BCH observation from a chain document. No seed, no broadcast, no completed checkout."""

from pathlib import Path

import pytest

from integrations.bch.errors import PaymentUnverified
from integrations.bch.verify import BchObserver, from_blockchair

TXID = "ab" * 32
MERCHANT = "bitcoincash:qpm2qsznhks23z7629mms6s4cwef74vcwvy22gdx6a"
OTHER = "bitcoincash:qr95sy3j9xwd2ap32xkykttr4cvcu7as4y0qverfuy"


def _document(value=10_000, confirmations=1, address=MERCHANT, txid=TXID):
    return {
        "txid": txid,
        "confirmations": confirmations,
        "outputs": [
            {"address": address, "value_sats": value},
            {"address": OTHER, "value_sats": 500},
        ],
    }


def test_exact_confirmed_output_matches_and_does_not_complete_checkout():
    result = BchObserver(MERCHANT).observe(TXID.upper(), 10_000, _document())
    assert result["status"] == "matched"
    assert result["checkout_complete"] is False
    assert result["funds_moved"] is False
    assert result["network"] == "mainnet"
    assert result["txid"] == TXID


def test_hash_alone_underpayment_and_zero_confirmations_stay_unpaid():
    observer = BchObserver(MERCHANT)
    with pytest.raises(PaymentUnverified):
        observer.observe(TXID, 10_000, {"txid": TXID})
    with pytest.raises(PaymentUnverified):
        observer.observe(TXID, 10_000, {"txid": "cd" * 32, "confirmations": 1, "outputs": []})
    assert observer.observe(TXID, 10_000, _document(value=9_000))["status"] == "awaiting_payment"
    assert observer.observe(TXID, 10_000, _document(confirmations=0))["status"] == "awaiting_payment"
    review = observer.observe(TXID, 10_000, _document(value=10_001))
    assert review["status"] == "requires_review"
    assert review["checkout_complete"] is False


def test_blockchair_payload_is_checked_before_it_can_match():
    payload = {
        "data": {
            TXID: {
                "transaction": {"hash": TXID, "block_id": 100},
                "outputs": [{"recipient": MERCHANT, "value": 10_000}],
            }
        },
        "context": {"state": 100},
    }
    document = from_blockchair(payload, TXID)
    assert BchObserver(MERCHANT).observe(TXID, 10_000, document)["status"] == "matched"
    unconfirmed = {
        "data": {TXID: {"transaction": {"hash": TXID, "block_id": -1}, "outputs": []}},
        "context": {"state": 100},
    }
    assert from_blockchair(unconfirmed, TXID)["confirmations"] == 0
    with pytest.raises(PaymentUnverified):
        from_blockchair({"data": {}}, TXID)


def test_chipnet_address_is_separate_and_the_module_has_no_signing_path():
    chipnet = "bchtest:qpm2qsznhks23z7629mms6s4cwef74vcwvy22gdx6a"
    result = BchObserver(chipnet, network="chipnet").observe(TXID, 1, _document(value=1, address=chipnet))
    assert result["network"] == "chipnet"
    assert result["checkout_complete"] is False
    with pytest.raises(ValueError):
        BchObserver(MERCHANT, network="chipnet")
    source = Path("integrations/bch/verify.py").read_text().lower()
    for banned in ("seed", "mnemonic", "private_key", "wif", "paypal"):
        assert banned not in source
