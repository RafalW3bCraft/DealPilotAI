"""CoinMarketCap November 2026 Round 2 reference quotes.

This package reads a server-side campaign key and returns attributed market
references. It does not set checkout prices.
"""

from .client import CmcClient, from_env
from .errors import CmcError, MissingApiKey, QuoteUnavailable, RateLimited

__all__ = [
    "CmcClient",
    "CmcError",
    "MissingApiKey",
    "QuoteUnavailable",
    "RateLimited",
    "from_env",
]
