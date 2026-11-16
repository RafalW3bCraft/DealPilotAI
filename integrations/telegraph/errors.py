"""Failures for a Telegraph intelligence purchase. None of these mean paid."""


class TelegraphError(Exception):
    """Base error. Subclasses are not successful purchases."""


class UnsupportedIntent(TelegraphError):
    """No discovered provider advertises the requested intent."""


class InvalidQuote(TelegraphError):
    """The payment challenge is missing a usable exact amount."""


class BudgetExceeded(TelegraphError):
    """The quoted price is above the authorized spend."""


class AuthorizationDenied(TelegraphError):
    """The buyer did not authorize this intelligence purchase."""


class ProviderTimeout(TelegraphError):
    """The provider did not answer inside the configured timeout."""


class InvalidResponse(TelegraphError):
    """The provider body is not usable verified intelligence."""


class PaymentRequired(TelegraphError):
    """The node returned HTTP 402 and no signer was authorized to pay it."""

    def __init__(self, message: str, challenge: dict):
        super().__init__(message)
        self.challenge = challenge


class PaymentRejected(TelegraphError):
    """A signed payment was not accepted. Do not treat the ask as paid."""
