"""BCH observation failures. A failure leaves the payment incomplete."""


class BchError(Exception):
    """Base error. It does not mean a checkout completed."""


class PaymentUnverified(BchError):
    """The chain document does not prove this payment."""
