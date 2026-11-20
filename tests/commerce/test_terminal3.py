"""Local Terminal 3 delegation decisions. The ADK is not imported or called."""

from integrations.terminal3.policy import SDK_NAME, DelegationBoundary, MemberGrant, OrgGrant

CONTRACT = "z:dealpilot:catalog"
AGENT = "did:t3n:agent-under-test"
NOW = 1_763_000_000


def _boundary(hosts=("pro-api.coinmarketcap.com",), until=None, member=True, org=True):
    member_grants = []
    org_grants = []
    if member:
        member_grants.append(
            MemberGrant(AGENT, CONTRACT, "search-catalog", ("search-catalog",), hosts, valid_until_secs=until)
        )
    if org:
        org_grants.append(OrgGrant(AGENT, CONTRACT, "search-catalog", ("search-catalog",)))
    return DelegationBoundary(member_grants, org_grants)


def test_both_edges_allow_a_scoped_read_and_record_an_audit():
    decision = _boundary().decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host="pro-api.coinmarketcap.com",
        now=NOW,
    )
    assert decision["allowed"] is True
    assert decision["reason"] == "granted"
    assert decision["sdk_called"] is False
    assert decision["traction"] is None
    assert decision["payment"] is False
    assert decision["operator_cap_known"] is False
    assert _boundary().audit == []
    boundary = _boundary()
    boundary.decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert boundary.audit[0]["allowed"] is True
    assert SDK_NAME == "@terminal3/t3n-sdk"
    assert boundary.sdk_called is False


def test_authentication_alone_and_one_missing_edge_are_denied():
    boundary = _boundary()
    anonymous = boundary.decide(
        grantee="",
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert anonymous["reason"] == "unauthenticated"
    member_only = _boundary(org=False).decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert member_only["reason"] == "org_delegation_not_found"
    org_only = _boundary(member=False).decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert org_only["reason"] == "member_delegation_not_found"


def test_egress_window_and_payment_functions_stay_blocked():
    wrong_host = _boundary().decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host="https://pro-api.coinmarketcap.com/v3",
        now=NOW,
    )
    assert wrong_host["reason"] == "host/http.egress_denied"
    unlisted = _boundary(hosts=()).decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host="pro-api.coinmarketcap.com",
        now=NOW,
    )
    assert unlisted["reason"] == "host/http.egress_denied"
    early = _boundary(until=NOW + 10).decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW - 5,
    )
    # valid_from is unset, so an earlier now is still inside an open start.
    assert early["allowed"] is True
    expired = _boundary(until=NOW).decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert expired["reason"] == "member_delegation_expired"
    payment = _boundary().decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="capture-payment",
        scope_path="capture-payment",
        host=None,
        now=NOW,
    )
    assert payment["allowed"] is False
    assert payment["reason"] == "payment_function_refused"
    assert payment["payment"] is False


def test_wildcard_grant_does_not_authorize_the_tenant_contract():
    boundary = DelegationBoundary(
        [MemberGrant(AGENT, "*", "*", ("search-catalog",))],
        [OrgGrant(AGENT, CONTRACT, "search-catalog", ("search-catalog",))],
    )
    decision = boundary.decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert decision["reason"] == "member_delegation_not_found"


def test_not_yet_valid_window_is_denied():
    grant = MemberGrant(
        AGENT,
        CONTRACT,
        "search-catalog",
        ("search-catalog",),
        (),
        valid_from_secs=NOW + 10,
        valid_until_secs=NOW + 20,
    )
    decision = DelegationBoundary(
        [grant],
        [OrgGrant(AGENT, CONTRACT, "search-catalog", ("search-catalog",))],
    ).decide(
        grantee=AGENT,
        contract_id=CONTRACT,
        function="search-catalog",
        scope_path="search-catalog",
        host=None,
        now=NOW,
    )
    assert decision["reason"] == "member_delegation_not_yet_valid"
