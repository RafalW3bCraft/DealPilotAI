#!/usr/bin/env python3
"""Retry durable, verified PayPal webhook events that need reconciliation.

Run once or schedule periodically with the application's sandbox environment.
No webhook payloads or credentials are printed.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import Config
from web.commerce_routes import _build_services, process_pending_webhook_events
from web_dashboard_clean import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true', help='Process batches repeatedly until interrupted')
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    if args.interval < 10 or not 1 <= args.limit <= 100:
        parser.error('interval must be at least 10 seconds; limit must be 1..100')
    stopped = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stopped.set())
    config = Config()
    app = create_app(config)
    try:
        with app.app_context():
            services = _build_services(config)
            storage = services.get("storage")
            checkout = services.get("checkout_service")
            if storage is None or checkout is None:
                print("WEBHOOK_RETRY=BLOCKED; configure durable storage and sandbox checkout")
                return 2
            while not stopped.is_set():
                try:
                    processed = process_pending_webhook_events(storage, checkout, limit=args.limit)
                    remaining = len(storage.list_retryable_events())
                    print(f"WEBHOOK_RETRY=COMPLETE processed={processed} remaining={remaining}", flush=True)
                except Exception as exc:
                    print(f"WEBHOOK_RETRY=RETRYABLE category={type(exc).__name__}", flush=True)
                    remaining = 1
                if not args.watch:
                    return 1 if remaining else 0
                stopped.wait(args.interval)
            return 0
    finally:
        app.data_manager.stop()
        services = app.extensions.get('dealpilot', {})
        if services.get('paypal_client'):
            services['paypal_client'].close()
        if services.get('storage') and hasattr(services['storage'], 'engine'):
            services['storage'].engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())