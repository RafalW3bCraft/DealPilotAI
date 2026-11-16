"""Isolated Bitcoin Cash payment observation for BCH BLAZE.

The adapter reads a transaction from a caller-supplied chain document. It does
not store a seed, sign, or broadcast, and it does not complete a PayPal checkout.
"""

from .verify import BchObserver

__all__ = ["BchObserver"]
