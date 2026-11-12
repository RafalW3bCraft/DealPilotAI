#!/usr/bin/env python3
"""Start the storefront without starting Telegram or the deal scheduler."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Ignore dotenv and disable all external integrations')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    if args.offline:
        values = {'PYTHON_DOTENV_DISABLED': '1', 'DEMO_MODE': 'true',
            'DATABASE_URL': '', 'COMMERCE_DATABASE_URL': 'sqlite:///' + str(ROOT / 'commerce-offline.db'),
            'OPENAI_API_KEY': '', 'FEATHERLESS_API_KEY': '', 'AI_PROVIDER': '',
            'PAYPAL_CLIENT_ID': '', 'PAYPAL_CLIENT_SECRET': '', 'PAYPAL_WEBHOOK_ID': '',
            'DASHBOARD_TOKEN': '', 'ENABLE_MERCHANT_CHECKOUT': 'true', 'ENABLE_EXTERNAL_AFFILIATE': 'false',
            'DISABLE_UNVERIFIED_AMAZON_SCRAPING': 'true', 'PREFERRED_URL_SCHEME': 'http',
            'APP_BASE_URL': f'http://127.0.0.1:{args.port}'}
        os.environ.update(values)
    from config import Config
    from web_dashboard_clean import create_app
    app = create_app(Config())
    print('PROFILE=' + ('offline-local' if args.offline else 'configured-sandbox'))
    try:
        app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False)
    finally:
        app.data_manager.stop()
        services = app.extensions.get('dealpilot', {})
        if services.get('paypal_client'):
            services['paypal_client'].close()
        if services.get('storage') and hasattr(services['storage'], 'engine'):
            services['storage'].engine.dispose()


if __name__ == '__main__':
    main()
