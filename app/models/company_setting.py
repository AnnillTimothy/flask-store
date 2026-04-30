from datetime import datetime, timezone
from app.extensions import db


class CompanySetting(db.Model):
    """Single-row company configuration table."""
    __tablename__ = 'company_settings'

    id = db.Column(db.Integer, primary_key=True)

    # ── Brand identity ───────────────────────────────────────────
    store_name = db.Column(db.String(200), nullable=False, default='The Bodhi Tree')
    tagline = db.Column(db.String(500), nullable=True, default='Enter the journey')
    logo_filename = db.Column(db.String(500), nullable=True)

    # ── Contact & social ─────────────────────────────────────────
    contact_email = db.Column(db.String(200), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=True)
    contact_address = db.Column(db.Text, nullable=True)
    instagram_url = db.Column(db.String(500), nullable=True)
    facebook_url = db.Column(db.String(500), nullable=True)

    # ── Shipping cost (overrides config if set) ───────────────────
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=True)

    # ── Long-form text pages ──────────────────────────────────────
    about_text = db.Column(db.Text, nullable=True)
    terms_text = db.Column(db.Text, nullable=True)
    privacy_text = db.Column(db.Text, nullable=True)

    # ── Landing media (uploaded files) ────────────────────────────
    landing_video_filename = db.Column(db.String(500), nullable=True)
    landing_audio_filename = db.Column(db.String(500), nullable=True)

    # ── Store page editorial content ──────────────────────────────
    store_hero_title = db.Column(db.String(300), nullable=True)
    store_hero_sub = db.Column(db.String(500), nullable=True)
    store_wisdom_1 = db.Column(db.String(500), nullable=True)
    store_wisdom_2 = db.Column(db.String(500), nullable=True)
    store_wisdom_3 = db.Column(db.String(500), nullable=True)

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Class helpers ─────────────────────────────────────────────

    @classmethod
    def get(cls):
        """Return the single settings row, creating it if absent."""
        obj = cls.query.first()
        if not obj:
            obj = cls()
            db.session.add(obj)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        return obj

    # ── Properties ───────────────────────────────────────────────

    @property
    def display_logo(self):
        if self.logo_filename:
            return f'/static/uploads/company/{self.logo_filename}'
        return None

    @property
    def display_landing_video(self):
        if self.landing_video_filename:
            return f'/static/uploads/company/{self.landing_video_filename}'
        return None

    @property
    def display_landing_audio(self):
        if self.landing_audio_filename:
            return f'/static/uploads/company/{self.landing_audio_filename}'
        return None

    def __repr__(self):
        return f'<CompanySetting {self.store_name!r}>'

    def __str__(self):
        return self.store_name or 'Company Settings'
