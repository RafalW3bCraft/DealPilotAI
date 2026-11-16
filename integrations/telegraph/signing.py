"""Optional x402 signer. Imported only when a purchase is authorized."""

from __future__ import annotations

from .errors import PaymentRejected


class X402ExactSigner:
    """Sign one exact-scheme EVM payment with the official x402 client."""

    def __init__(self, private_key: str, network: str):
        self._private_key = private_key
        self.network = network

    def __call__(self, challenge: dict) -> str:
        try:
            from eth_account import Account
            from x402 import parse_payment_required, prefer_network, prefer_scheme, x402ClientSync
            from x402.http import encode_payment_signature_header
            from x402.mechanisms.evm.exact import ExactEvmScheme
        except ImportError as exc:
            raise PaymentRejected(
                "x402[evm] is not installed; refusing to mark the ask as paid"
            ) from exc
        account = Account.from_key(self._private_key)
        client = x402ClientSync()
        client.register("eip155:*", ExactEvmScheme(account))
        client.register_policy(prefer_scheme("exact"))
        client.register_policy(prefer_network(self.network))
        try:
            payload = client.create_payment_payload(parse_payment_required(challenge))
        except Exception as exc:
            raise PaymentRejected("x402 could not sign the payment challenge") from exc
        return encode_payment_signature_header(payload)
