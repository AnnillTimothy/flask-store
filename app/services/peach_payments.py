"""
Peach Payments — Hosted Checkout integration.

Handles payment initiation and result verification for South African
payments via the Peach Payments REST Checkout API.

Docs: https://developer.peachpayments.com/docs/checkout-api

Required .env variables:
  PEACH_ENTITY_ID      — your entity/channel ID from the Peach dashboard
  PEACH_AUTH_TOKEN     — the Bearer token / API key from the Peach dashboard
  PEACH_SANDBOX        — 'True' for sandbox, 'False' for live (default: True)
"""
import hashlib
import hmac
import logging
import uuid

import requests
from flask import current_app

log = logging.getLogger(__name__)

SANDBOX_BASE = 'https://testsecure.peachpayments.com'
LIVE_BASE = 'https://secure.peachpayments.com'


def _base_url():
    if current_app.config.get('PEACH_SANDBOX', True):
        return SANDBOX_BASE
    return LIVE_BASE


def _headers():
    token = current_app.config.get('PEACH_AUTH_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def create_checkout(order, return_url, cancel_url, notify_url,
                    customer_email='', customer_name=''):
    """
    Create a Peach Payments hosted checkout session.

    Returns (checkout_url, checkout_id) on success, or (None, None) on failure.
    The caller should redirect the user to checkout_url.
    """
    entity_id = current_app.config.get('PEACH_ENTITY_ID', '')
    if not entity_id or not current_app.config.get('PEACH_AUTH_TOKEN', ''):
        log.error('Peach Payments entity ID or auth token not configured.')
        return None, None

    nonce = uuid.uuid4().hex

    payload = {
        'authentication': {
            'entityId': entity_id,
        },
        'amount': f'{float(order.total_amount):.2f}',
        'currency': 'ZAR',
        'paymentType': 'DB',
        'nonce': nonce,
        'shopperResultUrl': return_url,
        'cancelUrl': cancel_url,
        'notificationUrl': notify_url,
        'merchantTransactionId': order.order_number,
        'descriptor': f'Order {order.order_number}',
    }

    if customer_email:
        name_parts = customer_name.split() if customer_name else []
        payload['customer'] = {
            'email': customer_email,
            'givenName': name_parts[0] if name_parts else '',
            'surname': ' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
        }

    try:
        resp = requests.post(
            f'{_base_url()}/v1/checkouts',
            headers=_headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        result_code = data.get('result', {}).get('code', '')
        if not result_code.startswith('000.'):
            log.error('Peach Payments checkout creation failed: %s', data)
            return None, None

        checkout_id = data.get('id')
        if not checkout_id:
            log.error('Peach Payments: no checkout id in response: %s', data)
            return None, None

        checkout_url = f'{_base_url()}/v1/checkouts/{checkout_id}/payment'
        return checkout_url, checkout_id

    except requests.RequestException as exc:
        log.error('Peach Payments request error: %s', exc)
        return None, None


def verify_payment(resource_path):
    """
    Verify a payment result by fetching the transaction from Peach Payments.

    resource_path is the value from the webhook/redirect params.
    Returns a dict with keys: success (bool), result_code, order_number, amount.
    """
    entity_id = current_app.config.get('PEACH_ENTITY_ID', '')
    try:
        resp = requests.get(
            f'{_base_url()}{resource_path}',
            params={'authentication.entityId': entity_id},
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        result_code = data.get('result', {}).get('code', '')
        # Approved codes start with 000.000, 000.100, 800.400 (manual review) etc.
        success = result_code.startswith('000.000') or result_code.startswith('000.100')
        return {
            'success': success,
            'result_code': result_code,
            'order_number': data.get('merchantTransactionId'),
            'amount': data.get('amount'),
            'payment_id': data.get('id'),
        }
    except requests.RequestException as exc:
        log.error('Peach Payments verify_payment error: %s', exc)
        return {'success': False, 'result_code': 'error', 'order_number': None,
                'amount': None, 'payment_id': None}
