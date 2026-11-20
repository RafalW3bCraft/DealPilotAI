"""Decide whether a named agent may call one contract function.

The rules follow the published member-delegation and org-delegation edges:
authentication is not authorization, one function per grant, and an omitted
host list allows no egress. Decisions are local. ``sdk_called`` stays false
because ``@terminal3/t3n-sdk`` is not invoked.
"""

from __future__ import annotations

from dataclasses import dataclass

SDK_NAME = "@terminal3/t3n-sdk"
PAYMENT_MARKERS = ("pay", "capture", "transfer", "checkout", "refund")


@dataclass(frozen=True)
class MemberGrant:
    grantee: str
    contract_id: str
    function: str
    scope_paths: tuple[str, ...]
    allowed_hosts: tuple[str, ...] = ()
    valid_from_secs: int | None = None
    valid_until_secs: int | None = None


@dataclass(frozen=True)
class OrgGrant:
    grantee: str
    contract_id: str
    function: str
    scope_paths: tuple[str, ...]


class DelegationBoundary:
    def __init__(self, member_grants: list[MemberGrant], org_grants: list[OrgGrant]):
        self.member_grants = list(member_grants)
        self.org_grants = list(org_grants)
        self.audit: list[dict] = []
        self.sdk_called = False

    def decide(
        self,
        *,
        grantee: str,
        contract_id: str,
        function: str,
        scope_path: str,
        host: str | None,
        now: int,
    ) -> dict:
        decision = {
            "allowed": False,
            "reason": _reason(
                self.member_grants,
                self.org_grants,
                grantee=grantee,
                contract_id=contract_id,
                function=function,
                scope_path=scope_path,
                host=host,
                now=now,
            ),
            "grantee": grantee,
            "contract_id": contract_id,
            "function": function,
            "host": host,
            "sdk_called": False,
            "traction": None,
            "payment": False,
            "source": "local-policy",
        }
        decision["allowed"] = decision["reason"] == "granted"
        if decision["allowed"] and _window_omitted(self.member_grants, grantee, contract_id, function):
            decision["operator_cap_known"] = False
        self.audit.append(dict(decision))
        return decision


def _reason(member_grants, org_grants, *, grantee, contract_id, function, scope_path, host, now) -> str:
    if not isinstance(grantee, str) or not grantee.strip():
        return "unauthenticated"
    if not isinstance(function, str) or any(marker in function.lower() for marker in PAYMENT_MARKERS):
        return "payment_function_refused"
    if host is not None and not _plain_host(host):
        return "host/http.egress_denied"
    member = _match(member_grants, grantee, contract_id, function)
    if member is None:
        return "member_delegation_not_found"
    if member.valid_from_secs is not None and now < member.valid_from_secs:
        return "member_delegation_not_yet_valid"
    if member.valid_until_secs is not None and now >= member.valid_until_secs:
        return "member_delegation_expired"
    if scope_path not in member.scope_paths:
        return "scope_denied"
    if host is not None and host not in member.allowed_hosts:
        return "host/http.egress_denied"
    org = _match(org_grants, grantee, contract_id, function)
    if org is None:
        return "org_delegation_not_found"
    if scope_path not in org.scope_paths:
        return "scope_denied"
    return "granted"


def _match(grants, grantee, contract_id, function):
    found = None
    for grant in grants:
        if grant.function in {"", "*"} or grant.contract_id in {"", "*"}:
            continue
        if grant.grantee == grantee and grant.contract_id == contract_id and grant.function == function:
            found = grant
    return found


def _window_omitted(grants, grantee, contract_id, function) -> bool:
    grant = _match(grants, grantee, contract_id, function)
    return grant is None or grant.valid_until_secs is None


def _plain_host(host: str) -> bool:
    if not isinstance(host, str) or host != host.lower() or not host:
        return False
    if "://" in host or "/" in host or " " in host or "@" in host:
        return False
    return True
