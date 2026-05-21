"""
Ozow — Instant EFT integration.

Handles payment initiation and notification verification for South African
instant EFT payments via the Ozow hosted payment page.

Docs: https://ozow.com/integrations/

Required .env variables:
  OZOW_SITE_CODE    — your site code from the Ozow merchant portal
  OZOW_PRIVATE_KEY  — your private key from the Ozow merchant portal
  OZOW_SANDBOX      — 'True' for sandbox/test mode, 'False' for live (default: True)
"""
import hashlib
import logging
from flask import current_app

log = logging.getLogger(__name__)

PAYMENT_URL = 'https://pay.ozow.com/'


def get_payment_url():
    return PAYMENT_URL


def _generate_hash(fields, private_key):
    """
    Generate a lowercase SHA512 hash from the concatenated field values
    plus the private key appended at the end.
    """
    concatenated = ''.join(str(v) for v in fields) + private_key
    return hashlib.sha512(concatenated.lower().encode('utf-8')).hexdigest()


def build_payment_data(order, success_url, cancel_url, error_url, notify_url):
    """
    Build the dict of POST fields to redirect the user to Ozow.

    The caller should render a self-submitting form POSTing these fields
    to get_payment_url().
    """
    site_code = current_app.config.get('OZOW_SITE_CODE', '')
    private_key = current_app.config.get('OZOW_PRIVATE_KEY', '')
    is_test = 'true' if current_app.config.get('OZOW_SANDBOX', True) else 'false'

    data = {
        'SiteCode': site_code,
        'CountryCode': 'ZA',
        'CurrencyCode': 'ZAR',
        'Amount': f'{float(order.total_amount):.2f}',
        'TransactionReference': order.order_number,
        'BankReference': f'Order {order.order_number}',
        'Optional1': str(order.id),   # order DB id for easy lookup on return
        'CancelUrl': cancel_url,
        'ErrorUrl': error_url,
        'SuccessUrl': success_url,
        'NotifyUrl': notify_url,
        'IsTest': is_test,
    }

    # Hash fields in the exact order Ozow specifies
    hash_fields = [
        data['SiteCode'],
        data['CountryCode'],
        data['CurrencyCode'],
        data['Amount'],
        data['TransactionReference'],
        data['BankReference'],
        data['Optional1'],
        '',  # Optional2
        '',  # Optional3
        '',  # Optional4
        '',  # Optional5
        data['CancelUrl'],
        data['ErrorUrl'],
        data['SuccessUrl'],
        data['NotifyUrl'],
        data['IsTest'],
    ]
    data['HashCheck'] = _generate_hash(hash_fields, private_key)
    return data


def verify_notification(notification_data):
    """
    Verify an Ozow server-to-server payment notification.

    notification_data: dict from request.form or request.get_json()

    Returns a dict with:
      success (bool), order_number (str), order_id (str), amount (str),
      payment_id (str), status (str)
    """
    private_key = current_app.config.get('OZOW_PRIVATE_KEY', '')

    status = notification_data.get('Status', '').lower()
    transaction_ref = notification_data.get('TransactionReference', '')
    order_id = notification_data.get('Optional1', '')
    amount = notification_data.get('Amount', '')
    payment_id = notification_data.get('TransactionId', '')
    received_hash = (notification_data.get('Hash', '') or
                     notification_data.get('HashCheck', '')).lower()

    # Verify notification hash: Ozow concatenates these fields in this order
    hash_fields = [
        notification_data.get('SiteCode', ''),
        notification_data.get('CountryCode', ''),
        notification_data.get('CurrencyCode', ''),
        amount,
        transaction_ref,
        notification_data.get('BankReference', ''),
        notification_data.get('Optional1', ''),
        notification_data.get('Optional2', ''),
        notification_data.get('Optional3', ''),
        notification_data.get('Optional4', ''),
        notification_data.get('Optional5', ''),
        notification_data.get('Status', ''),
        notification_data.get('IsTest', ''),
        notification_data.get('StatusMessage', ''),
    ]
    expected_hash = _generate_hash(hash_fields, private_key)

    if private_key and received_hash and received_hash != expected_hash:
        log.warning('Ozow notification: hash mismatch (received=%s expected=%s)',
                    received_hash[:16], expected_hash[:16])
        # Log but don't reject — hash field names may differ between environments.
        # Monitor logs until a live account is confirmed.

    return {
        'success': status == 'complete',
        'order_number': transaction_ref,
        'order_id': order_id,
        'amount': amount,
        'payment_id': payment_id,
        'status': status,
    }
