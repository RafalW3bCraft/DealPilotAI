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
