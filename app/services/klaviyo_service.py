"""
Klaviyo API v3 service — subscriber capture and sync.

Handles:
  - Creating / updating profiles in Klaviyo
  - Subscribing and unsubscribing profiles to a list
  - Storing the resulting klaviyo_profile_id on the Subscriber row
"""
import os
import logging
from typing import Optional
import requests

log = logging.getLogger(__name__)

KLAVIYO_BASE = 'https://a.klaviyo.com/api'
KLAVIYO_REVISION = '2024-02-15'


def _headers():
    api_key = os.environ.get('KLAVIYO_PRIVATE_KEY', '')
    if not api_key:
        return None
    return {
        'Authorization': f'Klaviyo-API-Key {api_key}',
        'Content-Type': 'application/json',
        'revision': KLAVIYO_REVISION,
    }


def upsert_profile(email: str, name: str = None) -> 'Optional[str]':
    """
    Create or update a Klaviyo profile.
    Returns the Klaviyo profile ID on success, None on failure / missing config.
    """
    headers = _headers()
    if not headers:
        return None

    attributes = {'email': email}
    if name:
        parts = name.strip().split(None, 1)
        attributes['first_name'] = parts[0]
        if len(parts) > 1:
            attributes['last_name'] = parts[1]

    payload = {
        'data': {
            'type': 'profile',
            'attributes': attributes,
        }
    }

    try:
        resp = requests.post(
            f'{KLAVIYO_BASE}/profiles/',
            headers=headers,
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get('data', {}).get('id')
        # 409 = profile already exists — extract id from response
        if resp.status_code == 409:
            return resp.json().get('errors', [{}])[0].get(
                'meta', {}
            ).get('duplicate_profile_id')
    except Exception:
        log.exception('Klaviyo upsert_profile failed for %s', email)
    return None


def subscribe_to_list(profile_id: str) -> bool:
    """Add a profile to the configured Klaviyo list."""
    headers = _headers()
    list_id = os.environ.get('KLAVIYO_LIST_ID', '')
    if not headers or not list_id or not profile_id:
        return False

    payload = {
        'data': [{'type': 'profile', 'id': profile_id}]
    }

    try:
        resp = requests.post(
            f'{KLAVIYO_BASE}/lists/{list_id}/relationships/profiles/',
            headers=headers,
            json=payload,
            timeout=10,
        )
        return resp.status_code in (200, 204)
    except Exception:
        log.exception('Klaviyo subscribe_to_list failed for profile %s', profile_id)
    return False


def unsubscribe_from_list(profile_id: str) -> bool:
    """Remove a profile from the configured Klaviyo list."""
    headers = _headers()
    list_id = os.environ.get('KLAVIYO_LIST_ID', '')
    if not headers or not list_id or not profile_id:
        return False

    payload = {
        'data': [{'type': 'profile', 'id': profile_id}]
    }

    try:
        resp = requests.delete(
            f'{KLAVIYO_BASE}/lists/{list_id}/relationships/profiles/',
            headers=headers,
            json=payload,
            timeout=10,
        )
        return resp.status_code in (200, 204)
    except Exception:
        log.exception('Klaviyo unsubscribe_from_list failed for profile %s', profile_id)
    return False


def sync_subscriber(subscriber) -> None:
    """
    Full sync: upsert profile then add/remove from the list based on is_subscribed.
    Updates subscriber.klaviyo_profile_id in-place (caller must commit).
    """
    profile_id = subscriber.klaviyo_profile_id or upsert_profile(subscriber.email, subscriber.name)
    if not profile_id:
        return

    subscriber.klaviyo_profile_id = profile_id
    if subscriber.is_subscribed:
        subscribe_to_list(profile_id)
    else:
        unsubscribe_from_list(profile_id)
