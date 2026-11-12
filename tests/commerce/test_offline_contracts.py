"""Offline profile contracts: truthful browsing and quotes, with no payments."""
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from web.catalog_data import (
    DeterministicAI, InMemoryCommerceStorage, QuoteExpired, QuoteNotFound,
    QuoteStale, SimpleCartService, SimpleCatalog,
)


@pytest.fixture
def offline(tmp_path):
    rows = [dict(sku=sku, title=title, description=title, category='desk',
                 price=price, stock=5, currency='USD', version=1, active=True,
                 source='MERCHANT') for sku, title, price in [
        ('LAMP', 'LED Lamp', '24.99'), ('TRAY', 'Desk Organizer', '18.50'),
        ('CABLE', 'Cable Management', '12.99'),
    ]]
    path = tmp_path / 'catalog.json'
    path.write_text(json.dumps({'products': rows}))
    catalog = SimpleCatalog(path)
    storage = InMemoryCommerceStorage()
    config = SimpleNamespace(PAYPAL_CURRENCY='USD', MAX_CART_TOTAL='50.00',
                             CART_QUOTE_TTL_MINUTES=30)
    return SimpleNamespace(path=path, rows=rows, catalog=catalog, storage=storage,
                           config=config, cart=SimpleCartService(catalog, storage, config))


def test_offline_catalog_accepts_documented_array_root(offline):
    offline.path.write_text(json.dumps(offline.rows))
    assert len(SimpleCatalog(offline.path).list_products()) == 3


@pytest.mark.parametrize('bad', [dict(price='NaN'), dict(price='-1'), dict(stock=-1),
                                  dict(currency='usd'), dict(source='AMAZON'),
                                  dict(sku='B012345678')])
def test_offline_catalog_excludes_unquotable_or_affiliate_entries(offline, bad):
    offline.rows[0].update(bad)
    offline.path.write_text(json.dumps({'products': offline.rows}))
    assert len(SimpleCatalog(offline.path).list_products()) == 2


def test_offline_quote_ignores_client_price_and_snapshots_catalog(offline):
    quote = offline.cart.create_quote('alice', [dict(sku='LAMP', quantity=2, price='0.01')])
    assert quote['total'] == Decimal('49.98')
    assert quote['items'][0]['unit_price'] == Decimal('24.99')
    quote['items'][0]['unit_price'] = Decimal('0.01')
    read = offline.storage.get_quote(quote['quote_id'])
    assert read['items'][0]['unit_price'] == Decimal('24.99')
    read['items'][0]['quantity'] = 10
    assert offline.storage.get_quote(quote['quote_id'])['items'][0]['quantity'] == 2


@pytest.mark.parametrize('quantity', ['bad', 1.5, True, '2', 0, 11])
def test_offline_service_rejects_malformed_quantities(offline, quantity):
    with pytest.raises(ValueError, match='quantity'):
        offline.cart.create_quote('alice', [dict(sku='LAMP', quantity=quantity)])
    assert not offline.storage.quotes


def test_offline_quote_rejects_duplicates_currency_stock_and_total(offline):
    for items in ([dict(sku='TRAY', quantity=1)] * 2,
                  [dict(sku='LAMP', quantity=3)],
                  [dict(sku='LAMP', quantity=6)],
                  [dict(sku='missing', quantity=1)]):
        with pytest.raises(ValueError):
            offline.cart.create_quote('alice', items)
    offline.catalog.get_product('LAMP').currency = 'EUR'
    with pytest.raises(ValueError, match='currency'):
        offline.cart.create_quote('alice', [dict(sku='LAMP', quantity=1)])
    assert not offline.storage.quotes


def test_offline_quote_enforces_line_limit_before_storage(offline):
    with pytest.raises(ValueError, match='10'):
        offline.cart.create_quote('alice', [dict(sku='LAMP', quantity=1)] * 11)
    assert not offline.storage.quotes


def test_offline_quote_hides_owner_and_expires(offline):
    quote = offline.cart.create_quote('alice', [dict(sku='LAMP', quantity=1)])
    with pytest.raises(QuoteNotFound):
        offline.cart.validate_quote(quote['quote_id'], actor_id='bob')
    offline.storage.quotes[quote['quote_id']]['expires_at'] = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(QuoteExpired):
        offline.cart.validate_quote(quote['quote_id'], actor_id='alice')
    assert offline.storage.get_quote(quote['quote_id'])['status'] == 'EXPIRED'


@pytest.mark.parametrize('change', [dict(active=False), dict(stock=0), dict(price=Decimal('0.01')),
                                     dict(currency='EUR'), dict(version=2)])
def test_offline_quote_detects_catalog_drift(offline, change):
    quote = offline.cart.create_quote('alice', [dict(sku='LAMP', quantity=1)])
    for key, value in change.items():
        setattr(offline.catalog.get_product('LAMP'), key, value)
    with pytest.raises(QuoteStale):
        offline.cart.refresh_check(quote['quote_id'], actor_id='alice')


def test_offline_ai_discloses_fallback_and_limits_whole_cart(offline):
    service = DeterministicAI(offline.config, offline.catalog)
    result = service.recommend('desk under $30')
    assert result['fallback'] is True
    assert result['provider'] == 'deterministic-fallback'
    assert result['items']
    total = sum(offline.catalog.get_product(i['sku']).price * i['quantity']
                for i in result['cart_proposal'])
    assert total <= Decimal('30')
    zero = service.recommend('lamp', budget_hint='0')
    assert zero['items'] == [] and zero['cart_proposal'] == []
    unknown = service.recommend('teleportation portal')
    assert unknown['items'] == [] and unknown['missing_info']


def test_offline_ai_hindi_intent_is_relevant_and_localized(offline):
    result = DeterministicAI(offline.config, offline.catalog).recommend('लैंप दिखाओ', locale='hi')
    assert [i['sku'] for i in result['items']] == ['LAMP']
    assert 'कैटलॉग' in result['items'][0]['reason']


def test_real_cart_works_with_offline_storage_and_ownership(offline):
    from commerce.cart_service import CartService
    from commerce.exceptions import QuoteExpired as RealQuoteExpired, QuoteNotFound as RealQuoteNotFound
    from commerce.schemas import CartItem
    service = CartService(offline.catalog, offline.storage, offline.config)
    quote = service.create_quote('alice', [CartItem(sku='LAMP', quantity=1)])
    assert service.validate_quote(quote.quote_id, actor_id='alice').total == Decimal('24.99')
    with pytest.raises(RealQuoteNotFound):
        service.validate_quote(quote.quote_id, actor_id='bob')
    offline.storage.quotes[quote.quote_id]['expires_at'] = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(RealQuoteExpired):
        service.validate_quote(quote.quote_id, actor_id='alice')


def test_web_offline_storage_keeps_browsing_quotes_and_disables_payments(monkeypatch, tmp_path):
    from commerce.storage import CommerceStorage
    from tests.commerce.test_web_routes import _csrf, _make_app
    def unavailable(*args, **kwargs):
        raise RuntimeError('offline database')
    monkeypatch.setattr(CommerceStorage, '__init__', unavailable)
    app = _make_app(monkeypatch, tmp_path)
    extension = app.extensions['dealpilot']
    assert isinstance(extension['storage'], InMemoryCommerceStorage)
    assert extension['storage_durable'] is False
    assert extension['checkout_service'] is None
    owner = app.test_client()
    assert owner.get('/shop').status_code == 200
    csrf = {'X-CSRF-Token': _csrf(owner)}
    quote_response = owner.post('/cart/quote', json={'items': [{'sku': 'DP-LAMP-001', 'quantity': 1}]}, headers=csrf)
    assert quote_response.status_code == 200
    quote_id = quote_response.get_json()['quote_id']
    assert '24.99' in owner.get('/cart', query_string={'quote_id': quote_id}).text
    assert 'Quote not found.' in app.test_client().get('/cart', query_string={'quote_id': quote_id}).text
    extension['storage'].quotes[quote_id]['expires_at'] = datetime.now(UTC) - timedelta(seconds=1)
    expired_page = owner.get('/cart', query_string={'quote_id': quote_id}).text
    assert 'Merchant checkout is currently unavailable' in expired_page
    assert extension['storage'].get_quote(quote_id)['status'] == 'EXPIRED'
    ai = owner.post('/api/ai/recommend', json={'query': 'lamp'}, headers=csrf).get_json()
    assert ai['fallback'] is True
    checkout = owner.post('/checkout/start', json={'quote_id': quote_id}, headers=csrf)
    assert checkout.status_code == 503
    assert not extension['storage'].attempts
