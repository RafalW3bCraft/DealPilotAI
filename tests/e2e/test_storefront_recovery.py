"""Buyer recovery and feature states with fake provider boundaries only."""
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse
from decimal import Decimal

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.test_browser_checkout import storefront_server  # noqa: F401


def _quote_lamp(page, base_url):
    page.goto(base_url + "/shop", wait_until="networkidle")
    page.locator('input[name="sel"][data-sku="DP-LAMP-001"]').check()
    page.locator("#dp-quote-form button[type=submit]").click()
    page.wait_for_url("**/cart?quote_id=*")
    return page.url


def test_pending_order_survives_revisit_and_manual_network_recovery(storefront_server):
    gateway = storefront_server["gateway"]
    gateway.pending_capture = True
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        _quote_lamp(page, storefront_server["url"])
        page.locator("#dp-checkout-btn").click()
        page.wait_for_url("**/orders/*")
        order_url = page.url
        expect(page.locator(".dp-status .dp-badge")).to_have_text("Capture pending")
        assert gateway.capture_calls == 1
        assert gateway.create_calls == 1
        page.goto(order_url, wait_until="networkidle")
        page.route("**/status.json", lambda route: route.abort())
        page.locator("#dp-order-refresh").click()
        expect(page.locator("#dp-order-message")).to_contain_text("Could not check your order")
        expect(page.locator("#dp-order-refresh")).to_be_enabled()
        page.unroute("**/status.json")
        gateway.complete_pending()
        page.locator("#dp-order-refresh").click()
        expect(page.locator(".dp-status .dp-badge")).to_have_text("Paid")
        assert "MOCK-CAPTURE-E2E" in page.locator("main").inner_text()
        assert page.url == order_url
        assert gateway.capture_calls == 1
        assert gateway.create_calls == 1
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser.close()


def test_pending_automatic_checks_are_bounded_and_manual_refresh_remains(storefront_server):
    storefront_server["gateway"].pending_capture = True
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.clock.install()
        _quote_lamp(page, storefront_server["url"])
        page.locator("#dp-checkout-btn").click()
        page.wait_for_url("**/orders/*")
        requests = []
        page.on("request", lambda request: requests.append(request.url) if request.url.endswith("/status.json") else None)
        for _ in range(8):
            with page.expect_response("**/status.json"):
                page.clock.run_for(5000)
            # Ensure JS has processed the response and scheduled its next check.
            expect(page.locator("#dp-order-refresh")).to_be_enabled()
        expect(page.locator("#dp-order-message")).to_contain_text("Automatic checks have paused")
        assert len(requests) == 8
        page.clock.run_for(60000)
        assert len(requests) == 8
        with page.expect_response("**/status.json"):
            page.locator("#dp-order-refresh").click()
        assert len(requests) == 9
        browser.close()


@pytest.mark.parametrize("terminal", ["PAID", "FAILED", "CANCELED", "REQUIRES_REVIEW", "CAPTURE_PENDING"])
def test_checkout_replay_opens_existing_order_reference(storefront_server, terminal):
    gateway = storefront_server["gateway"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        cart_url = _quote_lamp(page, storefront_server["url"])
        gateway.pending_capture = True
        page.locator("#dp-checkout-btn").click()
        page.wait_for_url("**/orders/*")
        order_url = page.url
        page.goto(cart_url, wait_until="networkidle")
        page.route("**/checkout/start", lambda route: route.fulfill(
            status=200 if terminal == "PAID" else 202 if terminal == "CAPTURE_PENDING" else 409,
            json={"status": terminal, "order_url": order_url, "error": "Keep this order reference."},
        ))
        page.locator("#dp-checkout-btn").click()
        page.wait_for_url(order_url)
        assert gateway.create_calls == 1
        assert gateway.capture_calls == 1
        browser.close()


def test_terminal_payment_conflict_displays_merchant_review_warning(storefront_server):
    gateway = storefront_server["gateway"]
    gateway.pending_capture = True
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        _quote_lamp(page, storefront_server["url"])
        page.locator("#dp-checkout-btn").click()
        page.wait_for_url("**/orders/*")
        attempt_id = int(page.url.rsplit("/", 1)[-1].split("?", 1)[0])
        storage = storefront_server["services"]["storage"]
        storage.set_attempt_status(attempt_id, "CANCELED", ("CAPTURE_PENDING",))
        storage.finalize_capture(attempt_id, "MOCK-CAPTURE-E2E", Decimal("24.99"), "USD", datetime.now(UTC))
        page.goto(page.url + "?receipt=1", wait_until="networkidle")
        expect(page.locator(".dp-status .dp-badge")).to_have_text("Canceled")
        expect(page.get_by_role("alert")).to_contain_text("needs merchant review")
        assert "Thank you for your order" not in page.locator("main").inner_text()
        expect(page.locator("#dp-order-refresh")).to_be_enabled()
        browser.close()


@pytest.mark.parametrize("storefront_server", [{"ENABLE_MERCHANT_CHECKOUT": "false", "ENABLE_EXTERNAL_AFFILIATE": "true"}], indirect=True)
def test_disabled_checkout_is_explained_and_controls_are_disabled(storefront_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(storefront_server["url"] + "/shop", wait_until="networkidle")
        expect(page.get_by_role("status").filter(has_text="Merchant checkout is currently unavailable")).to_be_visible()
        expect(page.locator("#dp-quote-form button[type=submit]")).to_be_disabled()
        assert page.locator('input[name="sel"]:enabled').count() == 0
        page.goto(storefront_server["url"] + "/checkout?quote_id=missing", wait_until="networkidle")
        assert page.locator("#dp-checkout-btn").count() == 0
        assert "Merchant checkout is currently unavailable" in page.locator("main").inner_text()
        browser.close()


def test_empty_selection_keyboard_focus_and_ai_network_error(storefront_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(storefront_server["url"] + "/shop", wait_until="networkidle")
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
        page.locator("#dp-quote-form button[type=submit]").click()
        expect(page.locator("#dp-quote-msg")).to_contain_text("Choose at least one product")
        expect(page.locator('input[name="sel"]').first).to_be_focused()
        assert page.locator('input[name="sel"]').first.evaluate("element => getComputedStyle(element).outlineWidth") == "3px"
        page.route("**/api/ai/recommend", lambda route: route.fulfill(status=503, json={"error": "Recommendations are unavailable. Try the catalog below."}))
        page.locator("#dp-ai-query").fill("desk lamp")
        page.locator("#dp-ai-form button[type=submit]").click()
        expect(page.locator("#dp-ai-results")).to_contain_text("Recommendations are unavailable")
        expect(page.locator("#dp-ai-form button[type=submit]")).to_be_enabled()
        assert page.locator("#dp-ai-results").get_attribute("aria-live") == "polite"
        browser.close()


def test_expired_cart_can_be_requoted_without_losing_items(storefront_server):
    from sqlalchemy import update
    from commerce.storage import CartQuote

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        cart_url = _quote_lamp(page, storefront_server["url"])
        quote_id = parse_qs(urlparse(cart_url).query)["quote_id"][0]
        storage = storefront_server["services"]["storage"]
        with storage._session_factory.begin() as session:
            session.execute(update(CartQuote).where(CartQuote.quote_id == quote_id).values(expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)))
        page.reload(wait_until="networkidle")
        expect(page.get_by_role("alert")).to_contain_text("This quote expired")
        assert page.locator("#dp-checkout-btn").count() == 0
        expect(page.locator('input[name="qty_DP-LAMP-001"]')).to_have_value("1")
        page.locator("#dp-quote-form button[type=submit]").click()
        page.wait_for_url(lambda url: "/cart?quote_id=" in url and url != cart_url)
        expect(page.locator("#dp-checkout-btn")).to_be_enabled()
        assert "24.99 USD" in page.locator(".dp-summary-total").inner_text()
        assert storefront_server["gateway"].create_calls == 0
        browser.close()
