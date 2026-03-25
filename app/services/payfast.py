import hashlib
import urllib.parse
import requests
from flask import current_app


SANDBOX_URL = 'https://sandbox.payfast.co.za/eng/process'
LIVE_URL = 'https://www.payfast.co.za/eng/process'


def _build_signature(data, passphrase=''):
    """Generate the MD5 signature for PayFast."""
    # Sort keys and build query string (exclude 'signature')
    items = [(k, v) for k, v in data.items() if k != 'signature' and v != '']
    items.sort(key=lambda x: x[0])
    query = urllib.parse.urlencode(items)
    if passphrase:
        query += f'&passphrase={urllib.parse.quote(passphrase)}'
    return hashlib.md5(query.encode('utf-8')).hexdigest()


def get_payment_url():
    if current_app.config['PAYFAST_SANDBOX']:
        return SANDBOX_URL
    return LIVE_URL


def build_payment_data(order, return_url, cancel_url, notify_url):
    """Build the dict of POST data to submit to PayFast."""
    merchant_id = current_app.config['PAYFAST_MERCHANT_ID']
    merchant_key = current_app.config['PAYFAST_MERCHANT_KEY']
    passphrase = current_app.config['PAYFAST_PASSPHRASE']

    data = {
        'merchant_id': str(merchant_id),
        'merchant_key': str(merchant_key),
        'return_url': return_url,
        'cancel_url': cancel_url,
        'notify_url': notify_url,
        'name_first': order.customer_name.split()[0] if order.customer_name else '',
        'name_last': ' '.join(order.customer_name.split()[1:]) if order.customer_name and len(order.customer_name.split()) > 1 else '',
        'email_address': order.customer_email or '',
        'amount': f'{order.total_amount:.2f}',
        'item_name': f'Order #{order.id}',
        'item_description': f'Flask Store Order #{order.id}',
        'm_payment_id': str(order.id),
    }

    # Remove empty string values before signing
    data = {k: v for k, v in data.items() if v != ''}

    data['signature'] = _build_signature(data, passphrase)
    return data


def validate_itn(itn_data):
    """
    Validate a PayFast ITN (Instant Transaction Notification).
    Returns True if valid, False otherwise.
    """
    passphrase = current_app.config['PAYFAST_PASSPHRASE']
    expected_sig = _build_signature(itn_data, passphrase)
    received_sig = itn_data.get('signature', '')

    if expected_sig != received_sig:
        current_app.logger.warning('PayFast ITN: signature mismatch')
        return False

    # Validate against PayFast servers
    sandbox = current_app.config['PAYFAST_SANDBOX']
    validate_url = (
        'https://sandbox.payfast.co.za/eng/query/validate'
        if sandbox else
        'https://www.payfast.co.za/eng/query/validate'
    )
    try:
        response = requests.post(validate_url, data=itn_data, timeout=10)
        if response.text.strip().upper() == 'VALID':
            return True
        current_app.logger.warning(f'PayFast ITN validation response: {response.text}')
    except requests.RequestException as exc:
        current_app.logger.error(f'PayFast ITN validation error: {exc}')
    return False
