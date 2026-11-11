import os
import sys
from pathlib import Path

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["DEMO_MODE"] = "true"
for key in (
    "AI_PROVIDER",
    "OPENAI_API_KEY",
    "FEATHERLESS_API_KEY",
    "PAYPAL_CLIENT_ID",
    "PAYPAL_CLIENT_SECRET",
    "PAYPAL_WEBHOOK_ID",
    "TELEGRAM_BOT_TOKEN",
    "DASHBOARD_TOKEN",
    "FLASK_SECRET_KEY",
    "DATABASE_URL",
    "COMMERCE_DATABASE_URL",
    "PGHOST",
    "PGUSER",
    "PGPASSWORD",
    "PGDATABASE",
):
    os.environ.pop(key, None)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest


@pytest.fixture(autouse=True)
def close_test_resources(monkeypatch):
    """Close real engines and app threads after each isolated test."""
    import commerce.storage as storage
    from web_dashboard_clean import AsyncDataManager
    engines, managers = [], []
    create_engine = storage.create_engine
    start = AsyncDataManager.start

    def tracked_engine(*args, **kwargs):
        engine = create_engine(*args, **kwargs)
        engines.append(engine)
        return engine

    def tracked_start(manager):
        managers.append(manager)
        return start(manager)

    monkeypatch.setattr(storage, 'create_engine', tracked_engine)
    monkeypatch.setattr(AsyncDataManager, 'start', tracked_start)
    yield
    for manager in managers:
        manager.stop()
    for engine in engines:
        engine.dispose()
