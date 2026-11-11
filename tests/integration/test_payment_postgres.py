"""Real PostgreSQL contention tests; provisioned locally or by the CI service."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from commerce.storage import CommerceStorage
from commerce.cart_service import CartService
from commerce.catalog import Catalog
from commerce.schemas import CartItem
from commerce.exceptions import DuplicateRequest
from tests.commerce.test_checkout_service import FakeConfig


@pytest.fixture
def pg_storage():
    url = os.getenv('TEST_POSTGRES_URL')
    if not url:
        pytest.skip('TEST_POSTGRES_URL is required for real PostgreSQL tests')
    # This URL must identify an ephemeral test database, never user payment data.
    assert make_url(url).database == 'dealpilot_test'
    storage = CommerceStorage(url)
    with storage.engine.begin() as connection:
        connection.execute(text('TRUNCATE audit_actions, payment_events, payment_captures, checkout_attempts, cart_quotes, merchant_products, agent_sessions RESTART IDENTITY CASCADE'))
    yield storage
    storage.engine.dispose()


def new_quote(storage):
    catalog = Catalog(Path(__file__).resolve().parents[2] / 'config/merchant_catalog.json')
    return CartService(catalog, storage, FakeConfig()).create_quote('buyer', [CartItem(sku='DP-LAMP-001', quantity=1)])


def test_concurrent_checkout_unique_key_has_one_winner(pg_storage):
    quote = new_quote(pg_storage)
    row = pg_storage.get_quote(quote.quote_id)
    barrier = Barrier(2)
    def create():
        barrier.wait(timeout=5)
        try:
            return pg_storage.create_checkout_attempt(row.id, 'buyer', 'same-request', 'ORDER_CREATED').id
        except DuplicateRequest:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert len(pg_storage.list_orders()) == 1


def test_invalid_quote_id_is_not_a_database_error(pg_storage):
    assert pg_storage.get_quote('not-a-uuid') is None


def test_concurrent_capture_claim_and_finalize_are_atomic(pg_storage):
    quote = new_quote(pg_storage)
    attempt = pg_storage.create_checkout_attempt(pg_storage.get_quote(quote.quote_id).id, 'buyer', 'capture-request', 'AWAITING_BUYER_APPROVAL')
    barrier = Barrier(2)
    def claim():
        barrier.wait(timeout=5)
        return pg_storage.set_attempt_status(attempt.id, 'CAPTURE_PENDING', ('AWAITING_BUYER_APPROVAL',), capture_request_id='stable-capture-key')
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: claim(), range(2))) == [False, True]
    def finalize(_):
        return pg_storage.finalize_capture(attempt.id, 'VERIFIED-CAPTURE', quote.total, quote.currency, datetime.now(UTC))
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(finalize, range(2)))
    assert all(result['status'] == 'PAID' for result in outcomes)
    assert pg_storage.get_quote(quote.quote_id).status == 'PAID'
    with pg_storage.engine.connect() as connection:
        assert connection.scalar(text('SELECT count(*) FROM payment_captures')) == 1
