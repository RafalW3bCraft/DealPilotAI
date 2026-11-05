"""Authentication and CSRF helpers for the DealPilot web layer."""

import functools
import hmac
import logging
import secrets
import time
import uuid

from flask import abort, current_app, jsonify, redirect, request, session, url_for

logger = logging.getLogger(__name__)

CSRF_SESSION_KEY = 'csrf_token'
ACTOR_SESSION_KEY = 'actor_id'
MERCHANT_SESSION_KEY = 'merchant_authenticated_until'
MERCHANT_SESSION_TTL_SECONDS = 30 * 60


def current_actor_id():
    """Return the session buyer/actor id, creating one lazily."""
    actor = session.get(ACTOR_SESSION_KEY)
    if not actor:
        actor = uuid.uuid4().hex
        session[ACTOR_SESSION_KEY] = actor
    return actor


def ensure_actor():
    """Ensure an actor id exists. Returns it."""
    return current_actor_id()


def apply_security(app):
    """Apply browser session-cookie protections."""
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    scheme = app.config.get('PREFERRED_URL_SCHEME', 'http')
    app.config['SESSION_COOKIE_SECURE'] = scheme == 'https'


def csrf_token():
    """Return a per-session CSRF token, creating one on demand."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def verify_csrf():
    """Check a CSRF token from the request against the session."""
    expected = session.get(CSRF_SESSION_KEY)
    if not expected:
        return False
    payload = request.get_json(silent=True)
    provided = (
        request.headers.get('X-CSRF-Token')
        or request.form.get('csrf_token')
        or (payload.get('csrf_token') if isinstance(payload, dict) else '')
        or ''
    )
    return bool(provided) and hmac.compare_digest(str(provided), expected)


def require_csrf(view):
    """Return 403 for write requests without a valid CSRF token."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if not verify_csrf():
            return jsonify({'error': 'invalid or missing CSRF token'}), 403
        return view(*args, **kwargs)
    return wrapper


def _merchant_token_valid(config):
    token = getattr(config, 'DASHBOARD_TOKEN', '') or ''
    if not token:
        return None
    provided = request.headers.get('Authorization', '')
    if not provided.startswith('Bearer '):
        return False
    return bool(provided[7:]) and hmac.compare_digest(provided[7:], token)


def _merchant_session_valid():
    try:
        expires_at = int(session.get(MERCHANT_SESSION_KEY, 0))
    except (TypeError, ValueError):
        expires_at = 0
    if expires_at > int(time.time()):
        return True
    session.pop(MERCHANT_SESSION_KEY, None)
    return False


def is_merchant(config):
    """True for a valid bearer request or a non-expired merchant session."""
    return _merchant_token_valid(config) is True or _merchant_session_valid()


def require_merchant(view):
    """Require merchant auth, except for the explicitly labeled offline demo."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        config = current_app.extensions['dealpilot']['config']
        token_valid = _merchant_token_valid(config)
        if token_valid is True or _merchant_session_valid():
            return view(*args, **kwargs)
        if token_valid is None and getattr(config, 'DEMO_MODE', False):
            return view(*args, **kwargs)
        if request.method == 'GET' and request.accept_mimetypes.accept_html:
            return redirect(url_for('commerce.merchant_login'))
        if token_valid is None:
            abort(404)
        return jsonify({'error': 'authentication required'}), 401
    return wrapper
