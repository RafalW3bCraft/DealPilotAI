"""Explicit execution policy for the optional Amazon referral lane."""
import os
from urllib.parse import urlsplit

AMAZON_DOMAINS = {'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr',
                  'amazon.ca', 'amazon.com.au', 'amazon.co.jp', 'amazon.in'}


def scraping_allowed(config=None):
    def flag(name, default):
        if config is not None:
            return bool(getattr(config, name, default))
        return os.getenv(name, str(default)).lower() in {'true', '1', 'yes'}
    return flag('ENABLE_EXTERNAL_AFFILIATE', False) and not flag('DISABLE_UNVERIFIED_AMAZON_SCRAPING', True)


def amazon_url_allowed(url):
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or '').lower()
        return (parsed.scheme == 'https' and not parsed.username and not parsed.password
                and parsed.port in (None, 443)
                and any(host == domain or host.endswith('.' + domain) for domain in AMAZON_DOMAINS))
    except (ValueError, TypeError):
        return False
