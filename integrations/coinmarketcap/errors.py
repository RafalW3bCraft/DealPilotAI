"""CoinMarketCap client failures. None of these invent a price."""


class CmcError(Exception):
    """Base error. Instances do not carry a substitute price."""


class MissingApiKey(CmcError):
    """CMC_API_KEY is absent. The keyless public path is not a campaign key."""


class RateLimited(CmcError):
    """The API returned a documented throttle. No cached or invented price is used."""

    def __init__(self, error_code: int | None, message: str):
        super().__init__(message)
        self.error_code = error_code


class QuoteUnavailable(CmcError):
    """The response did not contain one exact positive USD price for the symbol."""
