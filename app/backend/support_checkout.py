"""Optional Stripe-hosted Checkout for supporting the Paint Lab project.

Payments go to the platform account; this is not artist-payout functionality.
No payment credentials, user-provided amounts or redirects are accepted from JS.
"""
from __future__ import annotations

import hashlib, hmac, json, os, time, urllib.error, urllib.parse, urllib.request

SUPPORT_AMOUNTS_GBP = (300, 500, 1000)
STRIPE_ENDPOINT = 'https://api.stripe.com/v1/checkout/sessions'


def configured() -> bool:
    return bool(os.environ.get('PAINT_LAB_STRIPE_SECRET_KEY', '').startswith(('sk_live_', 'sk_test_')))


def checkout_form(token: str, amount: int, base_url: str) -> dict[str, str]:
    if type(amount) is not int or amount not in SUPPORT_AMOUNTS_GBP:
        raise ValueError('Choose an available support amount')
    if not token or not token.replace('_', '').replace('-', '').isalnum():
        raise ValueError('Invalid artwork identifier')
    base = base_url.rstrip('/')
    return {
        'mode': 'payment',
        'payment_method_types[0]': 'card',
        'line_items[0][price_data][currency]': 'gbp',
        'line_items[0][price_data][unit_amount]': str(amount),
        'line_items[0][price_data][product_data][name]': 'Support the Paint Lab project',
        'line_items[0][price_data][product_data][description]': 'Voluntary project support; not a payment to the artist',
        'line_items[0][quantity]': '1',
        'metadata[publication_token]': token,
        'metadata[purpose]': 'paint_lab_project_support',
        'payment_intent_data[metadata][publication_token]': token,
        'success_url': base + '/p/' + token + '?support=returned',
        'cancel_url': base + '/p/' + token,
    }


def create_session(token: str, amount: int, base_url: str) -> str:
    secret = os.environ.get('PAINT_LAB_STRIPE_SECRET_KEY', '')
    if not configured():
        raise RuntimeError('Project support is not enabled')
    form = checkout_form(token, amount, base_url)
    req = urllib.request.Request(STRIPE_ENDPOINT,
        data=urllib.parse.urlencode(form).encode('ascii'),
        headers={'Authorization': 'Bearer ' + secret,
                 'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.load(resp)
    url = data.get('url', '')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != 'checkout.stripe.com':
        raise RuntimeError('Stripe Checkout returned an invalid URL')
    return url


def signed_event(raw: bytes, signature: str, secret: str, now: float | None = None):
    """Verify Stripe's timestamped v1 HMAC before trusting event payload."""
    if not secret or len(raw) > 100_000:
        raise ValueError('Webhook unavailable')
    parts = [part.strip().split('=', 1) for part in signature.split(',') if '=' in part]
    timestamps = [v for k, v in parts if k == 't']
    signatures = [v for k, v in parts if k == 'v1']
    if len(timestamps) != 1 or not signatures:
        raise ValueError('Missing Stripe signature')
    try: t = int(timestamps[0])
    except ValueError: raise ValueError('Invalid Stripe timestamp')
    if abs((time.time() if now is None else now) - t) > 300:
        raise ValueError('Expired Stripe signature')
    digest = hmac.new(secret.encode(), str(t).encode() + b'.' + raw, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(digest, candidate) for candidate in signatures):
        raise ValueError('Invalid Stripe signature')
    event = json.loads(raw)
    if not isinstance(event, dict) or not isinstance(event.get('data'), dict):
        raise ValueError('Invalid Stripe event')
    return event
