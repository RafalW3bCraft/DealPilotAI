"""Reactive price-guard loop against an in-memory chain. No transaction hash is created."""

from pathlib import Path

import pytest

from integrations.reactive.loop import (
    BASE_SEPOLIA,
    BASE_SEPOLIA_CALLBACK_PROXY,
    PRICE_GUARD_TOPIC0,
    REACTIVE_IGNORE,
    SYSTEM,
    UNICHAIN_SEPOLIA,
    UNICHAIN_SEPOLIA_CALLBACK_PROXY,
    ZERO_ADDRESS,
    CallbackNotAuthorized,
    LogRecord,
    NotAuthorized,
    PriceGuardCallback,
    PriceGuardReactive,
    SimulatedNetwork,
)

REACTIVE = "0x1111111111111111111111111111111111111111"
ORIGIN = "0x2222222222222222222222222222222222222222"
CALLBACK = "0x3333333333333333333333333333333333333333"
SKU = 0xA11CE


def _network():
    reactive = PriceGuardReactive(
        REACTIVE,
        BASE_SEPOLIA,
        ORIGIN,
        UNICHAIN_SEPOLIA,
        CALLBACK,
    )
    callback = PriceGuardCallback(UNICHAIN_SEPOLIA_CALLBACK_PROXY, REACTIVE)
    return SimulatedNetwork(reactive, callback), reactive, callback


def _log(observed=150, reference=100, topic0=PRICE_GUARD_TOPIC0):
    return LogRecord(BASE_SEPOLIA, ORIGIN, topic0, SKU, (reference, observed))


def test_matching_event_requests_a_callback_without_a_transaction_hash():
    network, _reactive, callback = _network()
    result = network.deliver(_log())
    assert result["handled"] is True
    assert result["simulated"] is True
    assert result["observed_testnet_hash"] is None
    assert result["cross_chain_settled"] is False
    assert result["funds_moved"] is False
    assert result["origin_chain_id"] == BASE_SEPOLIA
    assert result["destination_chain_id"] == UNICHAIN_SEPOLIA
    assert result["callback_request"]["placeholder"] == ZERO_ADDRESS
    assert callback.handled == [{"sku": SKU, "reference_cents": 100, "observed_cents": 150}]


def test_unauthorized_callers_and_unmatched_logs_do_not_settle():
    network, reactive, callback = _network()
    with pytest.raises(NotAuthorized):
        reactive.react(_log(), "0x9999999999999999999999999999999999999999")
    assert network.deliver(_log(topic0=REACTIVE_IGNORE))["handled"] is False
    assert network.deliver(_log(observed=100, reference=100))["handled"] is False
    with pytest.raises(NotAuthorized):
        callback.on_price_guard(BASE_SEPOLIA_CALLBACK_PROXY, REACTIVE, SKU, 100, 150)
    with pytest.raises(CallbackNotAuthorized):
        callback.on_price_guard(UNICHAIN_SEPOLIA_CALLBACK_PROXY, ORIGIN, SKU, 100, 150)
    direct = reactive.react(_log(), SYSTEM)
    assert direct["payload"]["reactive_sender"] == ZERO_ADDRESS
    assert callback.handled == []


def test_contract_source_names_the_documented_reactive_pattern():
    root = Path("integrations/reactive/contracts")
    origin = (root / "PriceGuardOrigin.sol").read_text()
    reactive = (root / "PriceGuardReactive.sol").read_text()
    callback = (root / "PriceGuardCallback.sol").read_text()
    assert "event PriceGuardTripped" in origin
    assert SYSTEM in reactive
    assert f"{REACTIVE_IGNORE:x}" in reactive
    assert "requestCallbackV_1_0" in reactive
    assert "address(0)" in reactive
    assert "onlyServiceProvider" in callback
    assert "onlyCallbackSender" in callback
    assert "Not deployed" in origin or "not deployed" in reactive.lower()
