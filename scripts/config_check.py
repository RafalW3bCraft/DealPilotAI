#!/usr/bin/env python3
"""DealPilotAI configuration validator.

The checks are split into five categories so the output reflects the real
startup state instead of treating any PayPal OAuth success as a complete pass.

1. Configuration syntax
2. Credential presence
3. External auth success
4. Supported functionality
5. Deployment readiness

No secret values are printed. Optional --online performs read-only auth probes.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROBLEMS = []
WARNINGS = []


def _get(name, default=''):
    return os.getenv(name, default).strip()


def _add(category, msg):
    if category == 'syntax':
        PROBLEMS.append(f'[syntax] {msg}')
    elif category == 'creds':
        PROBLEMS.append(f'[creds] {msg}')
    elif category == 'auth':
        PROBLEMS.append(f'[auth] {msg}')
    elif category == 'feature':
        PROBLEMS.append(f'[feature] {msg}')
    elif category == 'readiness':
        PROBLEMS.append(f'[readiness] {msg}')
    else:
        PROBLEMS.append(f'[unknown] {msg}')


def _warn(msg):
    WARNINGS.append(msg)


def _readable_bool(value):
    return value.lower() in {'1', 'true', 'yes', 'on'}


def main():
    online = '--online' in sys.argv
    demo_mode = _readable_bool(_get('DEMO_MODE', 'false'))
    provider = _get('AI_PROVIDER', '').lower()
    ai_key_present = bool(_get('OPENAI_API_KEY') or _get('FEATHERLESS_API_KEY'))
    cid = _get('PAYPAL_CLIENT_ID')
    csec = _get('PAYPAL_CLIENT_SECRET')
    cdb = _get('COMMERCE_DATABASE_URL', '').strip()

    if provider and provider not in {'openai', 'featherless'}:
        _add('syntax', "AI_PROVIDER must be 'openai' or 'featherless'")
    if provider == 'openai' and not _get('OPENAI_API_KEY'):
        _add('creds', 'AI_PROVIDER=openai requires OPENAI_API_KEY')
    if provider == 'featherless' and not _get('FEATHERLESS_API_KEY'):
        _add('creds', 'AI_PROVIDER=featherless requires FEATHERLESS_API_KEY')
    if not provider and not ai_key_present:
        _warn('No AI provider credentials configured: the app will run in deterministic fallback mode without real inference.')

    if not demo_mode and not _get('FLASK_SECRET_KEY'):
        _add('creds', 'FLASK_SECRET_KEY is missing in non-demo mode')
    if not demo_mode and _get('FLASK_SECRET_KEY') and len(_get('FLASK_SECRET_KEY')) < 16:
        _add('syntax', 'FLASK_SECRET_KEY is shorter than 16 characters')

    env = _get('PAYPAL_ENVIRONMENT', 'sandbox')
    if env != 'sandbox':
        _add('syntax', "PAYPAL_ENVIRONMENT must be 'sandbox'; live PayPal is refused")
    if bool(cid) != bool(csec):
        _add('creds', 'PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET must be set together')
    if cid and len(cid) < 20:
        _warn('PAYPAL_CLIENT_ID looks unexpectedly short; verify the sandbox client ID')
    if _get('ENABLE_MERCHANT_CHECKOUT', 'true').lower() in {'1', 'true', 'yes'} and not cdb:
        _add('readiness', 'Enable merchant checkout without a durable COMMERCE_DATABASE_URL')
    if cdb and cdb.lower() in {'memory', 'none'}:
        _add('feature', 'COMMERCE_DATABASE_URL must not point to in-memory storage for checkout')
    elif cdb and not (cdb.startswith('postgresql://') or cdb.startswith('sqlite:///')):
        _add('feature', 'COMMERCE_DATABASE_URL must use postgresql:// or sqlite:///')

    if _readable_bool(_get('ENABLE_EXTERNAL_AFFILIATE', 'false')) and not _get('AMAZON_AFFILIATE_ID'):
        _add('feature', 'ENABLE_EXTERNAL_AFFILIATE=true requires AMAZON_AFFILIATE_ID')
    if _get('AMAZON_AFFILIATE_ID') and not re.match(r'^[A-Za-z0-9-]{10,20}$', _get('AMAZON_AFFILIATE_ID')):
        _warn('AMAZON_AFFILIATE_ID format looks unusual; verify it is a valid Associates tag')

    if _get('TELEGRAM_BOT_TOKEN') and not re.match(r'^\d{6,}:[A-Za-z0-9_-]{30,}$', _get('TELEGRAM_BOT_TOKEN')):
        _warn('TELEGRAM_BOT_TOKEN format looks invalid; verify token format with getMe')

    if _get('BOT_TOKEN') and _get('TELEGRAM_BOT_TOKEN') and _get('BOT_TOKEN') != _get('TELEGRAM_BOT_TOKEN'):
        _add('syntax', 'BOT_TOKEN and TELEGRAM_BOT_TOKEN conflict; remove the legacy alias')
    if _get('TELEGRAM_CHENNAL') and _get('TELEGRAM_CHANNEL') and _get('TELEGRAM_CHENNAL') != _get('TELEGRAM_CHANNEL'):
        _add('syntax', 'TELEGRAM_CHENNAL conflicts with TELEGRAM_CHANNEL; remove the typo variable')

    if _get('PAYPAL_WEBHOOK_ID') == '':
        _warn('PAYPAL_WEBHOOK_ID unset: webhook verification will refuse inbound messages until configured')

    if _get('DASHBOARD_TOKEN') == '' and not demo_mode:
        _warn('DASHBOARD_TOKEN unset: merchant dashboard/API routes will remain fail-closed in non-demo mode')

    status = 'PASS'
    if PROBLEMS:
        status = 'FAIL'

    print('=== DealPilotAI config report ===')
    print(f'  profile: {"offline-demo" if demo_mode else "sandbox-ready"}')
    print(f'  AI_PROVIDER: {provider or "(unset)"}')
    for w in WARNINGS:
        print(f'  WARN  {w}')
    for p in PROBLEMS:
        print(f'  FAIL  {p}')

    if online and cid and csec and not demo_mode:
        print('--- online read-only probes ---')
        try:
            from paypal_checkout.client import get_bearer_token
            get_bearer_token(cid, csec)
            print('  PayPal sandbox OAuth: OK')
        except Exception as exc:
            print(f'  PayPal sandbox OAuth: FAIL ({type(exc).__name__})')
            _add('auth', 'sandbox OAuth probe failed; verify PayPal sandbox credentials and permissions')
            status = 'FAIL'

    print(f'=== {status} ({len(PROBLEMS)} problems, {len(WARNINGS)} warnings) ===')
    return 1 if PROBLEMS else 0


if __name__ == '__main__':
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    sys.exit(main())
