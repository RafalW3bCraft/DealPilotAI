"""Failures for an Aevum invoice. None of these mean the invoice was paid."""


class AevumError(Exception):
    """Base error. Subclasses are not settled payments."""


class ChainMismatch(AevumError):
    """The configured RPC did not report Aevum chain id 44005."""


class InvoiceNotFound(AevumError):
    """No invoice exists for the given id."""


class PaymentUnverified(AevumError):
    """The supplied transaction does not settle this invoice."""


class DuplicatePayment(AevumError):
    """This transaction is already bound to an invoice."""
