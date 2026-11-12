"""Live release gates must reject plausible but empty or irrelevant output."""
from decimal import Decimal
from types import SimpleNamespace

from ai.schemas import AIRecommendation, CartProposalItem, RecommendationItem
from commerce.catalog import Catalog
from scripts.ai_release_smoke import CATALOG_PATH, _run_case


def run_result(result, **kwargs):
    service = SimpleNamespace(recommend=lambda *args, **call_kwargs: result)
    return _run_case('test', service, Catalog(CATALOG_PATH), 'lamp', **kwargs)


def item(sku, price):
    return RecommendationItem(sku=sku, price=price, currency='USD', reason='Catalog verified')


def test_live_smoke_rejects_empty_success_response():
    result = AIRecommendation(intent_summary='Fine', fallback=False)
    assert 'no recommendations' in ' '.join(run_result(result)['failures'])


def test_live_smoke_rejects_irrelevant_valid_sku():
    result = AIRecommendation(intent_summary='Fine', items=[item('DP-PLANT-008', '9.99')])
    assert run_result(result, expected_skus={'DP-LAMP-001'})['failures']


def test_live_smoke_hindi_requires_requested_product_and_localized_output():
    result = AIRecommendation(intent_summary='Fine', items=[item('DP-LAMP-001', '24.99')])
    assert run_result(result, expected_skus={'DP-LAMP-001'}, locale='hi')['failures']


def test_live_smoke_budget_checks_total_not_only_units():
    result = AIRecommendation(intent_summary='Fine', items=[item('DP-LAMP-001', '24.99')],
                              cart_proposal=[CartProposalItem(sku='DP-LAMP-001', quantity=2)])
    assert run_result(result, max_total=Decimal('30'))['failures']


def test_live_smoke_unsupported_requires_empty_with_clarification():
    result = AIRecommendation(intent_summary='Fine', missing_info=['No matches'])
    assert run_result(result, expect_no_matches=True)['failures'] == []
    result.items = [item('DP-LAMP-001', '24.99')]
    assert run_result(result, expect_no_matches=True)['failures']
