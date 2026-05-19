from datetime import datetime, timezone
from app.extensions import db


class Subscriber(db.Model):
    """Marketing subscriber captured via the email popup or contact form."""
    __tablename__ = 'subscribers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True, nullable=False)
    source = db.Column(db.String(80), nullable=True)  # 'popup', 'contact_form', 'checkout'
    klaviyo_profile_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f'<Subscriber {self.email} subscribed={self.is_subscribed}>'

    def __str__(self):
        return self.email
