"""In-memory origin event, reactive request, and destination callback.

Constants match the Reactive Network docs fetched on 2026-11-16 and the
published ``REACTIVE_IGNORE`` value. The simulator rewrites the callback's
first address the way the network does, then stops. It never assigns a
transaction hash.
"""

from __future__ import annotations

from dataclasses import dataclass

REACTIVE_IGNORE = 0xA65F96FC951C35EAD38878E0F0B7A3C744A6F5CCC1476B313353CE31712313AD
SYSTEM = "0x8888888888888888888888888888888888888888"
BASE_SEPOLIA = 84532
BASE_SEPOLIA_CALLBACK_PROXY = "0x476F44b11F5C942c58f4c8E3d0300E5710743585"
UNICHAIN_SEPOLIA = 1301
UNICHAIN_SEPOLIA_CALLBACK_PROXY = "0x775c9B990ADe401060B78D0e98684eEf8d2466C1"
PRICE_GUARD_TOPIC0 = 0x63C45AB0050E310C5FF9373FD4EE963E486A3AE15A7708707BEB3BA7FC39EDC3
ZERO_ADDRESS = "0x" + "0" * 40
CALLBACK_GAS_LIMIT = 1_000_000


class NotAuthorized(Exception):
    """react() or the callback was not called by the system or the proxy."""


class CallbackNotAuthorized(Exception):
    """The injected reactive sender is not the authorized contract."""


@dataclass(frozen=True)
class LogRecord:
    chain_id: int
    contract: str
    topic0: int
    topic1: int
    data: tuple[int, int]
    topic2: int = 0
    topic3: int = 0
    op_code: int = 2


@dataclass(frozen=True)
class PriceGuardReactive:
    address: str
    origin_chain_id: int
    origin_contract: str
    destination_chain_id: int
    recipient: str

    def subscription(self) -> tuple:
        return (
            self.origin_chain_id,
            self.origin_contract.lower(),
            PRICE_GUARD_TOPIC0,
            REACTIVE_IGNORE,
            REACTIVE_IGNORE,
            REACTIVE_IGNORE,
        )

    def react(self, log: LogRecord, caller: str) -> dict | None:
        if caller.lower() != SYSTEM:
            raise NotAuthorized("react() accepts only the system contract")
        chain_id, contract, topic0, _topic1, _topic2, _topic3 = self.subscription()
        if log.chain_id != chain_id or log.contract.lower() != contract or log.topic0 != topic0:
            return None
        if log.op_code != 2 or len(log.data) != 2:
            return None
        reference_cents, observed_cents = log.data
        if observed_cents <= reference_cents:
            return None
        return {
            "chain_id": self.destination_chain_id,
            "recipient": self.recipient.lower(),
            "gas_limit": CALLBACK_GAS_LIMIT,
            "payload": {
                "signature": "onPriceGuard(address,bytes32,uint256,uint256)",
                "reactive_sender": ZERO_ADDRESS,
                "sku": log.topic1,
                "reference_cents": reference_cents,
                "observed_cents": observed_cents,
            },
        }


class PriceGuardCallback:
    def __init__(self, callback_proxy: str, callback_sender: str):
        self.callback_proxy = callback_proxy.lower()
        self.callback_sender = callback_sender.lower()
        self.handled: list[dict] = []

    def on_price_guard(self, caller: str, reactive_sender: str, sku: int, reference_cents: int, observed_cents: int):
        if caller.lower() != self.callback_proxy:
            raise NotAuthorized("callback accepts only the destination proxy")
        if reactive_sender.lower() != self.callback_sender:
            raise CallbackNotAuthorized("callback sender was not authorized")
        record = {
            "sku": sku,
            "reference_cents": reference_cents,
            "observed_cents": observed_cents,
        }
        self.handled.append(record)
        return record


class SimulatedNetwork:
    """Deliver one log through the documented loop. No chain client is used."""

    def __init__(self, reactive: PriceGuardReactive, callback: PriceGuardCallback):
        self.reactive = reactive
        self.callback = callback

    def deliver(self, log: LogRecord) -> dict:
        request = self.reactive.react(log, SYSTEM)
        result = {
            "simulated": True,
            "handled": False,
            "observed_testnet_hash": None,
            "cross_chain_settled": False,
            "funds_moved": False,
            "origin_chain_id": log.chain_id,
            "destination_chain_id": self.reactive.destination_chain_id,
        }
        if request is None:
            return result
        payload = request["payload"]
        if payload["reactive_sender"] != ZERO_ADDRESS:
            raise CallbackNotAuthorized("callback placeholder must be the zero address")
        delivered = self.callback.on_price_guard(
            self.callback.callback_proxy,
            self.reactive.address,
            payload["sku"],
            payload["reference_cents"],
            payload["observed_cents"],
        )
        result["handled"] = delivered is not None
        result["callback_request"] = {
            "chain_id": request["chain_id"],
            "recipient": request["recipient"],
            "gas_limit": request["gas_limit"],
            "placeholder": ZERO_ADDRESS,
        }
        return result
