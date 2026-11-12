"""Regression contracts for release audit findings; all gateways are local fakes."""

import pytest

from tests.commerce.test_checkout_service import BUYER, env, make_quote
from tests.commerce.test_web_routes import _make_app, _csrf


def test_paid_checkout_replay_after_expiry_returns_same_attempt(env):
    quote = make_quote(env)
    first = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    env.checkout.capture_after_approval('actor-1', first['attempt_id'], BUYER)
    env.clock.advance(hours=2)
    replay = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    assert replay['status'] == 'PAID'
    assert replay['attempt_id'] == first['attempt_id']
    assert len(env.gateway.create_calls) == 1


def test_reconcile_terminal_conflict_reports_persisted_state(env):
    quote = make_quote(env)
    started = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    env.gateway.capture_order(started['paypal_order_id'], 'remote-capture')
    env.storage.set_attempt_status(started['attempt_id'], 'CANCELED')
    result = env.checkout.reconcile(started['attempt_id'])
    assert result['status'] == 'CANCELED'
    assert result['requires_review'] is True
    assert env.storage.get_quote(quote.quote_id).status != 'PAID'
    assert env.storage.get_capture(attempt_id=started['attempt_id']) is not None


def test_create_order_contains_configured_callbacks(env):
    env.checkout.config.APP_BASE_URL = 'https://shop.example.com'
    quote = make_quote(env)
    env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    context = env.gateway.create_calls[0]['experience_context']
    assert context['return_url'] == 'https://shop.example.com/paypal/return'
    assert context['cancel_url'] == 'https://shop.example.com/paypal/cancel'


@pytest.mark.parametrize('quantity', [0, -1, 11, True, 1.5])
def test_bad_cart_quantities_are_client_errors(monkeypatch, tmp_path, quantity):
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    response = client.post('/cart/quote', json={'items': [{'sku': 'DP-LAMP-001', 'quantity': quantity}]}, headers={'X-CSRF-Token': _csrf(client)})
    assert response.status_code == 400


def test_disabled_checkout_is_unavailable_even_when_credentials_exist(monkeypatch, tmp_path):
    app = _make_app(monkeypatch, tmp_path, DEMO_MODE='false', FLASK_SECRET_KEY='release-test-secret-012345', ENABLE_MERCHANT_CHECKOUT='false', ENABLE_EXTERNAL_AFFILIATE='true', PAYPAL_CLIENT_ID='test-id', PAYPAL_CLIENT_SECRET='test-secret')
    client = app.test_client()
    response = client.post('/checkout/start', json={'quote_id': 'anything'}, headers={'X-CSRF-Token': _csrf(client)})
    assert response.status_code == 503
    assert app.extensions['dealpilot']['checkout_service'] is None


def test_checkout_json_array_is_client_error(monkeypatch, tmp_path):
    app = _make_app(monkeypatch, tmp_path, PAYPAL_CLIENT_ID='test-id', PAYPAL_CLIENT_SECRET='test-secret')
    client = app.test_client()
    response = client.post('/checkout/start', json=['invalid'], headers={'X-CSRF-Token': _csrf(client)})
    assert response.status_code == 400


def test_demo_with_merchant_token_can_reach_login(monkeypatch, tmp_path):
    app = _make_app(monkeypatch, tmp_path, DASHBOARD_TOKEN='test-token')
    response = app.test_client().get('/merchant/login', follow_redirects=True)
    assert response.status_code == 200
    assert 'merchant-token' in response.get_data(as_text=True)


@pytest.mark.parametrize('base', ['http://example.com', 'https://user:pass@example.com', 'https://example.com?x=1', 'javascript:alert(1)'])
def test_callback_base_url_rejects_unsafe_values(monkeypatch, base):
    monkeypatch.setenv('PYTHON_DOTENV_DISABLED', '1')
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setenv('AI_PROVIDER', '')
    monkeypatch.setenv('APP_BASE_URL', base)
    from config import Config
    with pytest.raises(RuntimeError, match='APP_BASE_URL'):
        Config()


def test_paypal_client_transmits_callback_context():
    import json
    from tests.commerce.test_paypal_client import make_client, json_route, ORDER_BODY
    sent = []
    client = make_client({'/v2/checkout/orders': json_route(ORDER_BODY, 201, record=sent)})
    context = {'return_url': 'https://shop.example/paypal/return', 'cancel_url': 'https://shop.example/paypal/cancel'}
    client.create_order(purchase_units=[], experience_context=context)
    assert json.loads(sent[0].content)['payment_source']['paypal']['experience_context'] == context
    client.close()


def test_disabled_scraper_never_initializes_session(monkeypatch):
    import asyncio
    from scraper import DealScraper
    monkeypatch.setenv('ENABLE_EXTERNAL_AFFILIATE', 'false')
    monkeypatch.setenv('DISABLE_UNVERIFIED_AMAZON_SCRAPING', 'false')
    scraper = DealScraper()
    assert asyncio.run(scraper.scrape_real_amazon_deals()) == []
    assert asyncio.run(scraper.search_products_by_keyword('lamp')) == []
    assert asyncio.run(scraper.scrape_specific_deal('https://www.amazon.com/dp/B012345678')) is None
    assert scraper.session is None


@pytest.mark.parametrize('url', ['https://amazon.com.attacker.test/product', 'https://attacker.test/?amazon.com', 'https://user:pass@amazon.com/', 'http://amazon.com/'])
def test_affiliate_url_rejects_spoofing(url):
    from core.affiliate_policy import amazon_url_allowed
    assert not amazon_url_allowed(url)


def test_capture_transaction_rolls_back_all_local_changes(env):
    from sqlalchemy import event
    quote = make_quote(env)
    started = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    def fail_quote_update(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('UPDATE CART_QUOTES'):
            raise RuntimeError('simulated database outage')
    event.listen(env.storage.engine, 'before_cursor_execute', fail_quote_update)
    try:
        with pytest.raises(RuntimeError):
            env.checkout.capture_after_approval('actor-1', started['attempt_id'], BUYER)
    finally:
        event.remove(env.storage.engine, 'before_cursor_execute', fail_quote_update)
    assert env.storage.get_capture(attempt_id=started['attempt_id']) is None
    assert env.storage.get_attempt(attempt_id=started['attempt_id']).status == 'CAPTURE_PENDING'
    assert env.storage.get_quote(quote.quote_id).status == 'OPEN'
    assert env.checkout.reconcile(started['attempt_id'])['status'] == 'PAID'


def uncertain_order(env):
    quote = make_quote(env)
    attempt = env.storage.create_checkout_attempt(env.storage.get_quote(quote.quote_id).id, BUYER, 'uncertain-create', 'REQUIRES_REVIEW')
    remote = env.gateway.create_order('CAPTURE', [{'amount': {'value': str(quote.total), 'currency_code': quote.currency}}], 'uncertain-create')
    remote['purchase_units'][0].update(custom_id=str(attempt.id), reference_id=quote.quote_id)
    return attempt, remote


def test_uncertain_creation_recovery_verifies_original_references(env):
    attempt, remote = uncertain_order(env)
    result = env.checkout.recover_created_order(attempt.id, remote['id'])
    assert result['status'] == 'AWAITING_BUYER_APPROVAL'
    assert env.storage.get_attempt(attempt_id=attempt.id).paypal_order_id == remote['id']


def test_uncertain_creation_recovery_rejects_unrelated_remote_order(env):
    from commerce.exceptions import CheckoutError
    attempt, remote = uncertain_order(env)
    remote['purchase_units'][0]['custom_id'] = 'different-attempt'
    with pytest.raises(CheckoutError, match='does not match'):
        env.checkout.recover_created_order(attempt.id, remote['id'])
    assert env.storage.get_attempt(attempt_id=attempt.id).paypal_order_id is None


def test_paid_replay_still_checks_quote_ownership(env):
    from commerce.exceptions import QuoteNotFound
    quote = make_quote(env)
    result = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    env.checkout.capture_after_approval('actor-1', result['attempt_id'], BUYER)
    with pytest.raises(QuoteNotFound):
        env.checkout.start_checkout('stranger', quote.quote_id, BUYER)


def test_parallel_capture_invokes_gateway_once(env):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    quote = make_quote(env)
    started = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    barrier = Barrier(2)
    original = env.gateway.get_order
    def synchronized_get(order_id):
        barrier.wait(timeout=5)
        return original(order_id)
    env.gateway.get_order = synchronized_get
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: env.checkout.capture_after_approval('actor-1', started['attempt_id'], BUYER), range(2)))
    assert len(env.gateway.capture_calls) == 1
    assert any(result['status'] == 'PAID' for result in results)
    assert env.storage.get_attempt(attempt_id=started['attempt_id']).status == 'PAID'


def test_payer_action_required_replay_and_cancel(env):
    quote = make_quote(env)
    env.gateway.order_status = 'PAYER_ACTION_REQUIRED'
    started = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    replay = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    assert replay['approve_url'] == started['approve_url']
    assert env.checkout.cancel_before_capture(BUYER, started['attempt_id'], started['paypal_order_id'])
    assert env.storage.get_attempt(attempt_id=started['attempt_id']).status == 'CANCELED'


def test_demo_merchant_auth_refuses_public_session_key(monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setenv('FLASK_SECRET_KEY', '')
    monkeypatch.setenv('DASHBOARD_TOKEN', 'protected-test-token')
    from config import Config
    with pytest.raises(RuntimeError, match='FLASK_SECRET_KEY'):
        Config()


def test_forged_demo_cookie_cannot_authenticate_merchant(monkeypatch, tmp_path):
    from flask import Flask
    from flask.sessions import SecureCookieSessionInterface
    import time
    app = _make_app(monkeypatch, tmp_path, DASHBOARD_TOKEN='protected-token')
    attacker = Flask('attacker')
    attacker.secret_key = 'demo-only-insecure-secret'
    cookie = SecureCookieSessionInterface().get_signing_serializer(attacker).dumps({'merchant_authenticated_until': int(time.time()) + 900})
    client = app.test_client()
    client.set_cookie('session', cookie)
    assert client.get('/merchant', headers={'Accept': 'application/json'}).status_code == 401


@pytest.mark.parametrize('change', [{'active': False}, {'price': '9.99'}, {'currency': 'EUR'}])
def test_new_checkout_rejects_drift_without_version_bump(env, change):
    from decimal import Decimal
    from commerce.exceptions import QuoteStale
    quote = make_quote(env)
    if 'price' in change:
        change['price'] = Decimal(change['price'])
    sku = quote.items[0].sku
    env.catalog._products[sku] = env.catalog.get_product(sku).model_copy(update=change)
    with pytest.raises(QuoteStale):
        env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    assert not env.gateway.create_calls


def test_capture_keys_do_not_collide_across_fresh_databases(env, tmp_path):
    import tests.commerce.test_checkout_service as fixtures
    other_path = tmp_path / 'separate-install'
    other_path.mkdir()
    other = fixtures.env.__wrapped__(other_path)
    keys = []
    for context in (env, other):
        quote = make_quote(context)
        attempt = context.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
        context.checkout.capture_after_approval('actor-1', attempt['attempt_id'], BUYER)
        keys.append(context.gateway.capture_calls[0]['request_id'])
    other.storage.engine.dispose()
    assert keys[0] != keys[1]


def test_a_second_capture_identity_requires_review_without_double_counting(env):
    quote = make_quote(env)
    started = env.checkout.start_checkout('actor-1', quote.quote_id, BUYER)
    env.checkout.capture_after_approval('actor-1', started['attempt_id'], BUYER)
    result = env.storage.finalize_capture(started['attempt_id'], 'OTHER-CAPTURE', quote.total, quote.currency, env.clock())
    assert result['requires_review'] is True
    assert env.storage.get_capture(capture_id='OTHER-CAPTURE') is None
    assert env.storage.has_payment_conflict(started['attempt_id'])
