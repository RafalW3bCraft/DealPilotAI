"""Local Reactive Omni price-guard loop.

The origin event, reactive callback request, and destination checks follow the
published Reactive Network pattern. Running this package does not submit a
transaction and does not record a testnet hash.
"""

from .loop import CallbackNotAuthorized, NotAuthorized, SimulatedNetwork

__all__ = ["CallbackNotAuthorized", "NotAuthorized", "SimulatedNetwork"]
