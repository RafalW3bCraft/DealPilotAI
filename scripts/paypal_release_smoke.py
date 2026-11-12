#!/usr/bin/env python3
"""Sanitized sandbox verification with a separate, human approval step.

--prepare creates one sandbox order. --attempt ID only reads its state unless
--capture-approved is supplied; PayPal must independently report APPROVED.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import Config
from commerce.cart_service import CartService
from commerce.catalog import Catalog
from commerce.checkout_service import CheckoutService
from commerce.schemas import CartItem
from commerce.storage import CommerceStorage
from paypal_checkout.client import PayPalClient

EVIDENCE = ROOT / 'docs/evidence/paypal_final.json'
ACTOR = 'release-verification'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--attempt', type=int)
    parser.add_argument('--capture-approved', action='store_true')
    args = parser.parse_args()
    config = Config()
    if not config.paypal_configured:
        print('PAYPAL_RELEASE=BLOCKED: configure sandbox credentials privately')
        return 2
    storage = CommerceStorage(config.COMMERCE_DATABASE_URL)
    gateway = PayPalClient(config.PAYPAL_CLIENT_ID, config.PAYPAL_CLIENT_SECRET)
    catalog = Catalog(ROOT / 'config/merchant_catalog.json')
    service = CheckoutService(storage, CartService(catalog, storage, config), gateway, config)
    evidence = {
        'timestamp_utc': datetime.now(UTC).isoformat(), 'environment': 'sandbox',
        'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'tracked_diff_sha256': hashlib.sha256(subprocess.check_output(['git', 'diff', 'HEAD'], cwd=ROOT)).hexdigest(),
    }
    if args.attempt and EVIDENCE.exists():
        prior = json.loads(EVIDENCE.read_text())
        if prior.get('attempt_id') == args.attempt:
            evidence = {**prior, **evidence}
    try:
        if args.prepare:
            quote = service.cart_service.create_quote(ACTOR, [CartItem(sku='DP-LAMP-001', quantity=1)])
            result = service.start_checkout(ACTOR, quote.quote_id, ACTOR)
            evidence.update({'attempt_id': result['attempt_id'], 'order_id': result['paypal_order_id'],
                             'status': result['status'], 'amount': str(quote.total), 'currency': quote.currency,
                             'gate': 'BLOCKED', 'reason': 'human sandbox buyer approval required'})
            print('approval_url=' + str(result.get('approve_url') or 'unavailable'))
        else:
            attempt = storage.get_attempt(attempt_id=args.attempt)
            if attempt is None or attempt.buyer_id != ACTOR:
                raise ValueError('attempt is not owned by this verification profile')
            remote = gateway.get_order(attempt.paypal_order_id)
            evidence.update({'attempt_id': attempt.id, 'order_id': attempt.paypal_order_id, 'approval_state': remote.get('status')})
            if not args.capture_approved:
                evidence.update({'gate': 'BLOCKED', 'reason': 'capture not requested'})
            elif remote.get('status') not in {'APPROVED', 'COMPLETED'}:
                evidence.update({'gate': 'BLOCKED', 'reason': 'buyer has not approved the sandbox order'})
            else:
                calls = []
                original = gateway.capture_order
                def counted_capture(*a, **kw):
                    calls.append(1)
                    return original(*a, **kw)
                gateway.capture_order = counted_capture
                result = service.reconcile(attempt.id) if remote.get('status') == 'COMPLETED' else service.capture_after_approval(ACTOR, attempt.id, ACTOR)
                service.capture_after_approval(ACTOR, attempt.id, ACTOR)
                capture = storage.get_capture(attempt_id=attempt.id)
                storage.engine.dispose()
                reopened = CommerceStorage(config.COMMERCE_DATABASE_URL)
                durable = reopened.get_attempt(attempt_id=attempt.id)
                persisted_capture = reopened.get_capture(attempt_id=attempt.id)
                passed = (result['status'] == 'PAID' and durable.status == 'PAID'
                          and capture is not None and persisted_capture is not None
                          and capture.paypal_capture_id == persisted_capture.paypal_capture_id and len(calls) <= 1)
                evidence.update({'gate': 'PASS' if passed else 'FAIL', 'status': durable.status,
                    'capture_id': capture.paypal_capture_id if capture else None,
                    'capture_status': capture.status if capture else None,
                    'amount': str(capture.amount) if capture else None, 'currency': capture.currency if capture else None,
                    'survived_storage_reopen': passed, 'capture_requests_including_repeat': len(calls)})
                reopened.engine.dispose()
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps(evidence, indent=2))
        return 0 if evidence['gate'] == 'PASS' else 2
    except Exception as exc:
        evidence.update({'gate': 'FAIL', 'error_category': type(exc).__name__,
                         'http_status': getattr(exc, 'status_code', None),
                         'paypal_debug_id': getattr(exc, 'debug_id', None)})
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps(evidence, indent=2))
        return 1
    finally:
        gateway.close()
        storage.engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
