"""Browser checkout journey using real app services and a fake PayPal boundary.

This test is not evidence of a live PayPal transaction or genuine AI inference.
"""

from __future__ import annotations

import copy
import threading

from flask import abort, redirect, request, url_for
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright


class FakePayPalGateway:
    def __init__(self) -> None:
        self.order: dict | None = None
        self.approve_url = ""

    def create_order(self, intent="CAPTURE", purchase_units=None, request_id=None):
        assert intent == "CAPTURE"
        self.order = {
            "id": "MOCK-ORDER-E2E",
            "status": "CREATED",
            "purchase_units": copy.deepcopy(purchase_units or []),
            "links": [{"rel": "approve", "href": self.approve_url}],
        }
        return copy.deepcopy(self.order)

    def get_order(self, order_id):
        if self.order is None or order_id != self.order["id"]:
            raise AssertionError("unexpected fake PayPal order lookup")
        return copy.deepcopy(self.order)

    def approve(self, order_id):
        if self.order is None or order_id != self.order["id"]:
            return False
        self.order["status"] = "APPROVED"
        return True

    def capture_order(self, order_id, request_id=None):
        if self.order is None or order_id != self.order["id"]:
            raise AssertionError("unexpected fake PayPal capture")
        amount = self.order["purchase_units"][0]["amount"]
        return {
            "id": order_id,
            "status": "COMPLETED",
            "purchase_units": [
                {
                    "amount": copy.deepcopy(amount),
                    "payments": {
                        "captures": [
                            {
                                "id": "MOCK-CAPTURE-E2E",
                                "status": "COMPLETED",
                                "amount": copy.deepcopy(amount),
                            }
                        ]
                    },
                }
            ],
        }


def test_browser_mocked_checkout_desktop_and_mobile(monkeypatch, tmp_path):
    from config import Config
    from web_dashboard_clean import create_app
    import web.commerce_routes as commerce_routes

    values = {
        "DEMO_MODE": "false",
        "FLASK_SECRET_KEY": "browser-test-session-secret-0123456789",
        "ENABLE_MERCHANT_CHECKOUT": "true",
        "ENABLE_EXTERNAL_AFFILIATE": "false",
        "COMMERCE_DATABASE_URL": f"sqlite:///{tmp_path / 'commerce-e2e.db'}",
        "DATABASE_URL": "",
        "PAYPAL_ENVIRONMENT": "sandbox",
        "PAYPAL_CLIENT_ID": "browser-test-client-id",
        "PAYPAL_CLIENT_SECRET": "browser-test-client-secret",
        "PAYPAL_WEBHOOK_ID": "",
        "DASHBOARD_TOKEN": "browser-test-dashboard-token",
        "AI_PROVIDER": "",
        "AI_MODEL": "",
        "OPENAI_API_KEY": "",
        "FEATHERLESS_API_KEY": "",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    config = Config()
    app = create_app(config)
    gateway = FakePayPalGateway()
    with app.test_request_context("/"):
        services = commerce_routes._build_services(config)
        checkout = services["checkout_service"]
        assert checkout is not None
        checkout.gateway = gateway
        monkeypatch.setattr(
            type(checkout),
            "_trusted_paypal_approval_url",
            staticmethod(lambda href: bool(href and href.startswith("http://127.0.0.1:"))),
        )

    @app.get("/__test_paypal/approve")
    def mock_paypal_approve():
        order_id = request.args.get("token", "")
        if not gateway.approve(order_id):
            abort(404)
        return redirect(url_for("commerce.paypal_return", token=order_id))

    server = make_server("127.0.0.1", 0, app, threaded=True)
    gateway.approve_url = (
        f"http://127.0.0.1:{server.server_port}/__test_paypal/approve"
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(
                extra_http_headers={
                    "Authorization": "Bearer browser-test-dashboard-token"
                }
            )
            page = context.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(f"{base_url}/shop", wait_until="networkidle")
            assert page.locator("#dp-ai-form").is_visible()

            page.locator("#dp-ai-query").fill("desk lamp under $30")
            page.locator("#dp-ai-form button[type=submit]").click()
            page.locator("#dp-ai-results .dp-ai-card").first.wait_for()
            assert "deterministic ranking, not AI" in page.locator(
                "#dp-ai-results"
            ).inner_text()

            page.locator(
                'input[name="sel"][data-sku="DP-LAMP-001"]'
            ).check()
            page.locator('input[name="qty_DP-LAMP-001"]').fill("2")
            page.locator("#dp-quote-form button[type=submit]").click()
            page.wait_for_url("**/cart?quote_id=*")
            assert "49.98 USD" in page.locator("main").inner_text()

            page.locator("#dp-checkout-btn").click()
            page.wait_for_url("**/orders/*?receipt=1")
            assert "Receipt" in page.locator("main").inner_text()
            assert "MOCK-CAPTURE-E2E" in page.locator("main").inner_text()
            assert "49.98 USD" in page.locator("main").inner_text()

            page.goto(f"{base_url}/merchant", wait_until="networkidle")
            merchant_text = page.locator("main").inner_text()
            assert "Merchant dashboard" in merchant_text
            assert "MOCK-CAPTURE-E2E" in merchant_text

            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(f"{base_url}/shop", wait_until="networkidle")
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            assert page.locator("#dp-quote-form").is_visible()
            context.close()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        data_manager = getattr(app, "data_manager", None)
        if data_manager is not None:
            data_manager.stop()
        storage = services.get("storage")
        engine = getattr(storage, "engine", None)
        if engine is not None:
            engine.dispose()
