"""Offline browser regressions for legacy rendering and aggregate contracts."""
from __future__ import annotations

import json
from pathlib import Path
import threading

import pytest
from flask import Flask, render_template
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server


@pytest.fixture
def legacy_browser():
    root = Path(__file__).resolve().parents[2]
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))

    @app.get("/<view>")
    def legacy_page(view):
        return render_template(f"{view}.html")

    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        # No external network or chart library is needed to exercise real page scripts.
        page.route("https://**/*", lambda route: route.abort())
        page.add_init_script("""
            window.__charts = [];
            window.Chart = class {
                constructor(canvas, options) { window.__charts.push({id:canvas.id, options}); }
                destroy() {} resize() {}
            };
        """)
        yield page, f"http://127.0.0.1:{server.server_port}"
        browser.close()
    server.shutdown()
    thread.join(timeout=5)


def fulfill_json(route, data):
    route.fulfill(status=200, content_type="application/json", body=json.dumps(data))


def test_scraped_deals_are_text_and_links_are_validated(legacy_browser):
    page, base = legacy_browser
    attack = '<img src=x onerror="window.__injected=true">'
    deals = []
    for index, link in enumerate([
        "javascript:window.__injected=true",
        "https://amazon.com.evil.example/dp/B000000001",
        "https://evil@amazon.com/dp/B000000001",
        "http://amazon.com/dp/B000000001",
        "https://www.amazon.com/dp/B000000001?tag=test-20",
        "https://www.amazon.co.uk/dp/B000000001?tag=test-21",
    ]):
        deals.append({"id": "');window.__injected=true;//", "title": attack,
                      "category": attack, "price": attack, "discount": attack,
                      "clicks": 2, "conversions": 1, "earnings": "3.50",
                      "posted_at": "2099-01-01T00:00:00Z", "affiliate_link": link})
    page.route("**/api/deals?*", lambda route: fulfill_json(route, deals))
    page.goto(base + "/deals", wait_until="networkidle")
    page.wait_for_function("document.querySelector('#deals-count').textContent === '6 DEALS'")
    body = page.locator("#deals-table-body")
    assert attack in body.inner_text()
    assert body.locator("img, [onclick]").count() == 0
    assert page.evaluate("window.__injected || false") is False
    assert body.get_by_role("button", name="Copy affiliate link").count() == 6
    assert body.get_by_role("button", name="Copy affiliate link").all()[0].is_disabled()
    assert body.get_by_role("button", name="Copy affiliate link").all()[1].is_disabled()
    assert body.get_by_role("button", name="Copy affiliate link").all()[2].is_disabled()
    assert body.get_by_role("button", name="Copy affiliate link").all()[3].is_disabled()
    assert body.get_by_role("button", name="Copy affiliate link").all()[4].is_enabled()
    assert body.get_by_role("button", name="Copy affiliate link").all()[5].is_enabled()


def test_users_render_only_real_aggregate_data(legacy_browser):
    page, base = legacy_browser
    attack = '<img src=x onerror="window.__injected=true">'
    payload = {"active_users": 8, "regions": {"US": 5, attack: 3},
               "categories": {"electronics": 6, "home": 2}, "window_days": 30}
    page.route("**/api/users?*", lambda route: fulfill_json(route, payload))
    page.goto(base + "/users", wait_until="networkidle")
    page.wait_for_function("document.querySelector('#active-user-count').textContent === '8'")
    assert attack in page.locator("#region-summary").inner_text()
    assert page.locator("#region-summary img").count() == 0
    assert "Individual profiles and daily activity are not collected" in page.locator("main, .cyber-container").inner_text()
    charts = page.evaluate("window.__charts")
    assert sorted(chart["id"] for chart in charts) == ["categoryUserChart", "regionChart"]
    assert page.evaluate("window.__injected || false") is False


def test_dashboard_loads_once_and_renders_first_chart_data(legacy_browser):
    page, base = legacy_browser
    requests = []
    stats = {"total_deals": 1, "active_users": 2, "total_clicks": 3,
             "total_conversions": 1, "total_earnings": 4.5,
             "conversion_rate": 33.3, "avg_earnings_per_deal": 4.5,
             "category_stats": {"home": 1}}
    attack = '<img src=x onerror="window.__injected=true">'
    deal = {"title": attack, "price": "$4.50", "category": attack,
            "earnings": 4.5, "posted_at": "2099-01-01T00:00:00Z"}

    def stats_response(route):
        requests.append(route.request.url)
        fulfill_json(route, stats)

    page.route("**/api/stats", stats_response)
    page.route("**/api/deals?*", lambda route: fulfill_json(route, [deal]))
    page.goto(base + "/dashboard", wait_until="networkidle")
    page.wait_for_function("window.__charts.length === 2")
    assert len(requests) == 1
    assert attack in page.locator("#deals-table").inner_text()
    assert page.locator("#deals-table img").count() == 0
    assert page.evaluate("window.__charts[0].options.data.labels") == ["home"]
    assert page.evaluate("window.__injected || false") is False
