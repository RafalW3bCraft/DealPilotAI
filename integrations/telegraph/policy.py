"""Spend and authorization checks. These run before any signed payment."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .errors import AuthorizationDenied, BudgetExceeded, InvalidQuote
from .schemas import PaymentOption, USDC_ATOMIC


def atomic_from_usdc(amount: Decimal | str | int) -> int:
    """Convert a USDC decimal into 6-decimal atomic units."""
    try:
        value = Decimal(str(amount))
    except InvalidOperation as exc:
        raise InvalidQuote("amount is not a decimal") from exc
    if not value.is_finite() or value < 0:
        raise InvalidQuote("amount must be a nonnegative finite decimal")
    scaled = value * USDC_ATOMIC
    if scaled != scaled.to_integral_value():
        raise InvalidQuote("amount has more than 6 decimal places")
    return int(scaled)


def require_authorization(buyer_authorized: bool) -> None:
    if buyer_authorized is not True:
        raise AuthorizationDenied("buyer authorization is required before a Telegraph purchase")


def assert_within_budget(quoted_atomic: int, budget_atomic: int, ceiling_atomic: int) -> None:
    if quoted_atomic < 0:
        raise InvalidQuote("quoted amount is negative")
    limit = min(budget_atomic, ceiling_atomic)
    if quoted_atomic > limit:
        raise BudgetExceeded(
            f"quoted {quoted_atomic} atomic units exceeds the authorized limit of {limit}"
        )


def select_payment_option(
    options: list[PaymentOption],
    *,
    preferred_network: str,
    allowed_networks: tuple[str, ...],
) -> PaymentOption:
    """Prefer an exact-scheme option on the configured test network."""
    exact = [
        option for option in options
        if option.scheme == "exact" and option.network in allowed_networks and option.amount_atomic > 0
    ]
    if not exact:
        raise InvalidQuote("no exact payment option on an allowed network")
    for option in exact:
        if option.network == preferred_network:
            return option
    return exact[0]
