"""
Amazon SES transactional email service.

Handles all transactional emails:
  - Order confirmations
  - Password resets
  - Account verification
  - Shipping updates
  - Receipts
  - Contact form notifications (internal)

Uses boto3 (AWS SDK).  Requires environment variables:
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SES_REGION, SES_FROM_EMAIL
"""
import os
import logging
from typing import Optional

log = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_client():
    """Return a boto3 SES client, or None if credentials are not configured."""
    try:
        import boto3
        region = os.environ.get('AWS_SES_REGION', 'us-east-1')
        return boto3.client(
            'ses',
            region_name=region,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        )
    except Exception:
        return None


def _from_address() -> str:
    """Sender address — pulled from env, falls back to a safe default."""
    name = os.environ.get('SES_FROM_NAME', 'The Bodhi Tree')
    addr = os.environ.get('SES_FROM_EMAIL', '')
    if not addr:
        return ''
    return f'{name} <{addr}>'


def send_raw(to: str, subject: str, html_body: str, text_body: str = '') -> bool:
    """
    Send a single transactional email via SES.
    Returns True on success, False if SES is not configured or sending fails.
    """
    from_addr = _from_address()
    if not from_addr:
        log.warning('SES_FROM_EMAIL not set — email to %s skipped.', to)
        return False

    client = _get_client()
    if not client:
        log.warning('boto3 SES client unavailable — email to %s skipped.', to)
        return False

    try:
        client.send_email(
            Source=from_addr,
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                    'Text': {'Data': text_body or _strip_html(html_body), 'Charset': 'UTF-8'},
                },
            },
        )
        log.info('SES email sent to %s — %s', to, subject)
        return True
    except Exception:
        log.exception('SES send_email failed for %s', to)
        return False


def _strip_html(html: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', html).strip()


# ── Branded HTML wrapper ───────────────────────────────────────────────────

def _wrap(store_name: str, content_html: str) -> str:
    """Wrap content in a branded, responsive HTML email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{store_name}</title>
  <!--[if mso]><noscript><xml><o:OfficeDocumentSettings>
  <o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Space+Grotesk:wght@300;400;500;600&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #040404; font-family: 'Space Grotesk', Arial, sans-serif; color: #f0ece4; -webkit-font-smoothing: antialiased; }}
    .shell {{ max-width: 600px; margin: 0 auto; background: #040404; }}
    .header {{ padding: 2.5rem 2.5rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.08); text-align: center; }}
    .brand {{ font-family: 'Cormorant Garamond', Georgia, serif; font-size: 2rem; font-weight: 600; letter-spacing: 0.06em; color: #f0ece4; }}
    .brand-sub {{ font-size: 0.62rem; letter-spacing: 0.28em; text-transform: uppercase; color: rgba(240,236,228,0.3); margin-top: 0.3rem; }}
    .body {{ padding: 2.5rem; background: #0d0d0d; border: 1px solid rgba(255,255,255,0.06); margin: 0 1rem; border-top: none; border-bottom: none; }}
    h1 {{ font-family: 'Cormorant Garamond', Georgia, serif; font-size: 2rem; font-weight: 400; color: #f0ece4; margin-bottom: 1rem; }}
    h2 {{ font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.4rem; font-weight: 400; color: #f0ece4; margin: 1.5rem 0 0.75rem; }}
    p {{ color: rgba(240,236,228,0.7); font-size: 0.9rem; line-height: 1.75; margin-bottom: 1rem; }}
    .divider {{ height: 1px; background: rgba(255,255,255,0.07); margin: 1.5rem 0; }}
    .label {{ font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(240,236,228,0.3); margin-bottom: 0.3rem; }}
    .value {{ font-size: 0.95rem; color: #f0ece4; }}
    .price {{ font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.3rem; font-weight: 600; color: #c8b49a; }}
    .btn {{ display: inline-block; padding: 0.85rem 2.2rem; background: #f0ece4; color: #040404; font-family: 'Space Grotesk', Arial, sans-serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; text-decoration: none; border-radius: 3px; margin: 1.5rem 0; }}
    .status-badge {{ display: inline-block; padding: 0.3rem 0.9rem; border-radius: 2px; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; border: 1px solid rgba(200,180,154,0.4); color: #c8b49a; }}
    .order-row {{ display: flex; justify-content: space-between; padding: 0.65rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.88rem; }}
    .order-row:last-child {{ border-bottom: none; }}
    .footer {{ padding: 1.5rem 2.5rem 2.5rem; text-align: center; }}
    .footer p {{ font-size: 0.75rem; color: rgba(240,236,228,0.2); }}
    .footer a {{ color: rgba(200,180,154,0.6); text-decoration: none; }}
    @media (max-width: 480px) {{
      .body {{ margin: 0; border-left: none; border-right: none; }}
      .header, .footer {{ padding: 1.5rem; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="header">
      <div class="brand">{store_name}</div>
      <div class="brand-sub">Curated with intention</div>
    </div>
    <div class="body">
      {content_html}
    </div>
    <div class="footer">
      <p>&copy; 2025 {store_name}. All rights reserved.</p>
      <p style="margin-top:0.5rem;"><a href="#">Unsubscribe</a> &nbsp;·&nbsp; <a href="#">Privacy Policy</a></p>
    </div>
  </div>
</body>
</html>"""


# ── Template factory functions ─────────────────────────────────────────────

def _store_name() -> str:
    try:
        from app.models.company_setting import CompanySetting
        return CompanySetting.get().store_name or 'The Bodhi Tree'
    except Exception:
        return 'The Bodhi Tree'


def send_order_confirmation(order, to: str) -> bool:
    """Send an order confirmation email to the customer."""
    name = _store_name()
    items_html = ''.join(
        f'<div class="order-row"><span>{item.item_name} × {item.quantity}</span>'
        f'<span class="price">R{item.subtotal:,.2f}</span></div>'
        for item in order.items
    )
    content = f"""
      <h1>Order Confirmed</h1>
      <p>Thank you{' ' + order.customer_name if order.customer_name else ''}. Your order has been received and is being processed.</p>
      <div class="divider"></div>
      <div class="label">Order Reference</div>
      <div class="value" style="margin-bottom:1rem;">{order.order_number}</div>
      <div class="label">Status</div>
      <div style="margin-bottom:1.5rem;"><span class="status-badge">{order.status.replace('_',' ').upper()}</span></div>
      <h2>Items</h2>
      <div style="margin-bottom:1rem;">{items_html}</div>
      <div class="divider"></div>
      <div class="order-row"><span>Shipping</span><span class="price">R{float(order.shipping_cost):,.2f}</span></div>
      {f'<div class="order-row"><span>Discount</span><span class="price">-R{float(order.discount_amount):,.2f}</span></div>' if float(order.discount_amount) > 0 else ''}
      <div class="order-row"><span style="font-weight:600;">Total</span><span class="price" style="font-size:1.5rem;">R{float(order.total_amount):,.2f}</span></div>
      <div class="divider"></div>
      <p>We'll notify you when your order ships. Questions? Reply to this email or visit our store.</p>
    """
    return send_raw(to, f'Order Confirmed — {order.order_number}', _wrap(name, content))


def send_shipping_update(order, tracking_number: Optional[str] = None) -> bool:
    """Notify customer that their order has shipped."""
    name = _store_name()
    tracking_html = f'<p><strong>Tracking number:</strong> {tracking_number}</p>' if tracking_number else ''
    content = f"""
      <h1>Your Order Is On Its Way</h1>
      <p>Great news! Order <strong>{order.order_number}</strong> has been dispatched and is heading your way.</p>
      {tracking_html}
      <div class="divider"></div>
      <div class="label">Shipping to</div>
      <div class="value">{order.customer_name or ''}<br>
        {order.address_line1 or ''}{', ' + order.address_line2 if order.address_line2 else ''}<br>
        {order.town or ''}{', ' + order.province if order.province else ''} {order.postal_code or ''}
      </div>
      <div class="divider"></div>
      <p>Thank you for shopping with us. We hope you love your order.</p>
    """
    to = order.customer_email or ''
    if not to:
        return False
    return send_raw(to, f'Your Order Is On Its Way — {order.order_number}', _wrap(name, content))


def send_password_reset(to: str, reset_url: str) -> bool:
    """Send password reset link."""
    name = _store_name()
    content = f"""
      <h1>Reset Your Password</h1>
      <p>We received a request to reset the password for your {name} account.</p>
      <p>Click the button below to set a new password. This link expires in 1 hour.</p>
      <a href="{reset_url}" class="btn">Reset Password</a>
      <div class="divider"></div>
      <p>If you didn't request a password reset, you can safely ignore this email.</p>
    """
    return send_raw(to, f'Reset Your {name} Password', _wrap(name, content))


def send_contact_ticket_notification(ticket, admin_email: str) -> bool:
    """Notify admin of a new contact ticket."""
    name = _store_name()
    content = f"""
      <h1>New Support Ticket</h1>
      <div class="label">Ticket Reference</div>
      <div class="value" style="margin-bottom:1rem;">{ticket.ticket_ref}</div>
      <div class="label">From</div>
      <div class="value">{ticket.name} &lt;{ticket.email}&gt;</div>
      <div class="divider"></div>
      <div class="label">Subject</div>
      <div class="value" style="margin-bottom:1rem;">{ticket.subject or '(No subject)'}</div>
      <div class="label">Message</div>
      <div class="value" style="white-space:pre-line;line-height:1.7;">{ticket.message}</div>
      <div class="divider"></div>
      <p>Log in to the admin dashboard to respond and update the ticket status.</p>
    """
    return send_raw(admin_email, f'[Support] New Ticket {ticket.ticket_ref}', _wrap(name, content))


def send_contact_ticket_confirmation(ticket) -> bool:
    """Send a confirmation to the customer who submitted a contact form."""
    name = _store_name()
    content = f"""
      <h1>We Received Your Message</h1>
      <p>Hi {ticket.name}, thank you for reaching out to {name}.</p>
      <p>We've received your enquiry (reference: <strong>{ticket.ticket_ref}</strong>) and will get back to you within 1–2 business days.</p>
      <div class="divider"></div>
      <div class="label">Your message</div>
      <div class="value" style="white-space:pre-line;line-height:1.7;">{ticket.message}</div>
      <div class="divider"></div>
      <p>If your enquiry is urgent, please call us during business hours.</p>
    """
    return send_raw(ticket.email, f'We received your message — {ticket.ticket_ref}', _wrap(name, content))
