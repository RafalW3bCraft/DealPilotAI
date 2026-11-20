"""Procurement advice stays on catalog prices, with or without OpenMinion."""

from decimal import Decimal
from types import SimpleNamespace

from integrations.cortensor.advisor import ProcurementAdvisor


def _product(sku, title, price):
    return SimpleNamespace(
        sku=sku,
        title=title,
        description=title,
        price=Decimal(price),
        currency="USD",
        stock=4,
        category="audio",
        active=True,
    )


class Catalog:
    def __init__(self, products):
        self.products = products

    def search_products(self, query, category=None, budget_max=None, limit=8):
        found = []
        for product in self.products:
            if budget_max is not None and product.price > budget_max:
                continue
            haystack = f"{product.title} {product.sku}".lower()
            if query and query.lower() not in haystack:
                continue
            found.append(product)
        return found[:limit]

    def get_product(self, sku):
        return next((product for product in self.products if product.sku == sku), None)


def _catalog():
    return Catalog(
        [
            _product("HP-1", "Studio headphones", "40.00"),
            _product("HP-2", "Travel headphones", "25.00"),
        ]
    )


def test_deterministic_advice_copies_catalog_price():
    advice = ProcurementAdvisor(_catalog()).advise("headphones", budget="30")
    assert advice["selected"]["sku"] == "HP-2"
    assert advice["selected"]["price"] == "25.00"
    assert advice["quote"]["total"] == "25.00"
    assert advice["model_backed"] is False


def test_echo_provider_cannot_choose_a_product():
    def echo(query, rows):
        return "openminion: " + rows[0]["sku"]

    advice = ProcurementAdvisor(_catalog(), runner=echo, provider="echo").advise("headphones")
    assert advice["model_backed"] is False
    assert advice["selected"]["price"] == "25.00"


def test_model_choice_must_be_a_catalog_sku_and_keeps_catalog_price():
    def choose(_query, _rows):
        return "Use HP-1 at $1.00 because it is better."

    advice = ProcurementAdvisor(_catalog(), runner=choose, provider="openai").advise("headphones")
    assert advice["model_backed"] is True
    assert advice["selected"]["sku"] == "HP-1"
    assert advice["selected"]["price"] == "40.00"
    assert advice["quote"]["total"] == "40.00"


def test_invented_sku_falls_back_to_catalog_ranking():
    advice = ProcurementAdvisor(
        _catalog(),
        runner=lambda _query, _rows: "Buy SKU-DOES-NOT-EXIST for $9",
        provider="openai",
    ).advise("headphones")
    assert advice["model_backed"] is False
    assert advice["selected"]["sku"] == "HP-2"
    assert advice["selected"]["price"] == "25.00"
