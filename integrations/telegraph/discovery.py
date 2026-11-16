"""Choose a discovered miner that actually advertises the intent."""

from __future__ import annotations

from .errors import UnsupportedIntent
from .schemas import Offering


def select_offering(offerings: list[Offering], intent: str) -> Offering:
    matches = [item for item in offerings if intent in item.intents and item.miner_id]
    if not matches:
        raise UnsupportedIntent(f"no discovered miner supports {intent}")
    return sorted(matches, key=lambda item: (item.min_price_atomic, item.miner_id))[0]
