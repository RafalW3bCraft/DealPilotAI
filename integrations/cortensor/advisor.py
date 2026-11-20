"""Catalog-grounded shopping advice through the OpenMinion SDK.

The SDK may phrase a choice. Prices, SKUs, and quotes come from the catalog.
An echo-provider turn is a runtime check, not a model-backed recommendation.
"""

from __future__ import annotations

import json
import os
import uuid
from decimal import Decimal

from ai.tools import CatalogTools


class OpenMinionRunner:
    """One isolated OpenMinion turn. Imported only when a run is requested."""

    def __init__(self, config_path: str):
        self.config_path = config_path

    def __call__(self, query: str, rows: list[dict]) -> str:
        from openminion import Agent, tool

        approved = json.dumps(rows)

        @tool
        def lookup_catalog(request: str) -> str:
            """Return the approved catalog rows for this request."""
            return approved

        with Agent(
            instructions=(
                "Recommend only SKUs from lookup_catalog. "
                "Do not invent products, prices, discounts, or stock."
            ),
            tools=[lookup_catalog],
            forced_tools=["lookup_catalog"],
            config_path=self.config_path,
            session_id=str(uuid.uuid4()),
        ) as agent:
            result = agent.run(
                f"Choose one approved SKU for: {query}",
                timeout_seconds=45,
            )
        return result.text or ""


class ProcurementAdvisor:
    def __init__(self, catalog, runner=None, provider: str = "deterministic"):
        self.tools = CatalogTools(catalog)
        self.runner = runner
        self.provider = provider or "deterministic"

    def advise(self, query: str, budget: str | None = None) -> dict:
        limit = None if budget is None else Decimal(budget)
        rows = self.tools.catalog_search(query=query, budget_max=limit, limit=4)
        if not rows:
            return _result(query, [], None, self.provider, False, "no catalog match")
        model_text = ""
        note = "catalog ranking"
        if self.runner is not None and self.provider != "deterministic":
            try:
                model_text = self.runner(query, rows)
                note = "openminion turn completed"
            except Exception as exc:
                note = f"openminion failed: {type(exc).__name__}"
        selected = rows[0]
        model_backed = False
        if self.provider not in {"deterministic", "echo"} and model_text:
            chosen = _grounded_choice(model_text, rows)
            if chosen is not None:
                selected = chosen
                model_backed = True
            else:
                note = "model output was not a catalog SKU"
        quote = self.tools.calculate_quote([{"sku": selected["sku"], "quantity": 1}])
        result = _result(query, rows, selected, self.provider, model_backed, note)
        result["quote"] = quote
        result["sdk_text"] = model_text
        return result


def advisor_from_env(catalog) -> ProcurementAdvisor:
    provider = os.getenv("CORTENSOR_PROVIDER", "").strip().lower()
    config_path = os.getenv("CORTENSOR_CONFIG", "").strip()
    if not provider or not config_path:
        return ProcurementAdvisor(catalog)
    return ProcurementAdvisor(
        catalog,
        runner=OpenMinionRunner(config_path),
        provider=provider,
    )


def _grounded_choice(text: str, rows: list[dict]) -> dict | None:
    lowered = text.lower()
    for row in rows:
        if row["sku"].lower() in lowered:
            return row
    return None


def _result(query, rows, selected, provider, model_backed, note) -> dict:
    return {
        "query": query,
        "products": rows,
        "selected": selected,
        "quote": None,
        "provider": provider,
        "model_backed": model_backed,
        "runtime_note": note,
        "sdk_text": "",
        "prices_from_catalog": True,
    }
