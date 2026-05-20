"""
Yoco — Online Checkout integration.

Handles payment initiation and result verification for South African
payments via the Yoco v2 REST Checkout API.

Docs: https://developer.yoco.com/online/

Required .env variables:
  YOCO_SECRET_KEY      — your secret key from the Yoco business portal
                         (sk_test_xxx for sandbox, sk_live_xxx for live)
  YOCO_WEBHOOK_SECRET  — webhook signing secret from the Yoco dashboard
                         (used to verify server-to-server notifications)
"""
import hashlib
import hmac
import logging
import requests
from flask import current_app

log = logging.getLogger(__name__)

API_BASE = 'https://payments.yoco.com/api'


def _headers():
    secret_key = current_app.config.get('YOCO_SECRET_KEY', '')
    return {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json',
    }


def create_checkout(order, success_url, cancel_url, failure_url, notify_url):
    """
    Create a Yoco hosted checkout session.

    Returns (redirect_url, checkout_id) on success, or (None, None) on failure.
    The caller should redirect the user to redirect_url.
    """
    secret_key = current_app.config.get('YOCO_SECRET_KEY', '')
    if not secret_key:
        log.error('Yoco secret key not configured.')
        return None, None

    # Yoco amounts are in cents (integer)
    amount_cents = int(round(float(order.total_amount) * 100))

    payload = {
        'amount': amount_cents,
        'currency': 'ZAR',
        'cancelUrl': cancel_url,
        'successUrl': success_url,
        'failureUrl': failure_url,
        'metadata': {
            'orderId': str(order.id),
            'orderNumber': order.order_number,
        },
    }

    if notify_url:
        payload['notificationUrl'] = notify_url

    try:
        resp = requests.post(
            f'{API_BASE}/checkouts',
            headers=_headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        redirect_url = data.get('redirectUrl')
        checkout_id = data.get('id')

        if not redirect_url or not checkout_id:
            log.error('Yoco: unexpected response: %s', data)
            return None, None

        return redirect_url, checkout_id

    except requests.RequestException as exc:
        log.error('Yoco request error: %s', exc)
        return None, None


def retrieve_checkout(checkout_id):
    """
    Retrieve a checkout by ID to verify its status.

    Returns a dict with:
      success (bool), status (str), order_id, order_number, amount, payment_id
    """
    try:
        resp = requests.get(
            f'{API_BASE}/checkouts/{checkout_id}',
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        status = data.get('status', '').lower()
        metadata = data.get('metadata', {})
        return {
            'success': status == 'succeeded',
            'status': status,
            'order_id': metadata.get('orderId'),
            'order_number': metadata.get('orderNumber'),
            'amount': data.get('amount'),
            'payment_id': data.get('id'),
        }
    except requests.RequestException as exc:
        log.error('Yoco retrieve_checkout error: %s', exc)
        return {
            'success': False, 'status': 'error',
            'order_id': None, 'order_number': None,
            'amount': None, 'payment_id': None,
        }


def verify_webhook_signature(payload_bytes, received_signature):
    """
    Verify a Yoco webhook notification using HMAC-SHA256.

    payload_bytes: raw request body bytes
    received_signature: value of the X-Yoco-Signature header

    Returns True if signature is valid.
    """
    webhook_secret = current_app.config.get('YOCO_WEBHOOK_SECRET', '')
    if not webhook_secret:
        log.warning('YOCO_WEBHOOK_SECRET not configured; skipping signature check.')
        return True

    expected = hmac.new(
        webhook_secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()  # type: ignore[attr-defined]
    return hmac.compare_digest(expected, received_signature or '')
