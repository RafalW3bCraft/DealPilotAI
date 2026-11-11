"""Regression contracts for release audit findings; all gateways are local fakes."""
from datetime import timedelta

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
