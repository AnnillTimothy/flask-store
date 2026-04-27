from datetime import datetime, timezone
from app.extensions import db


class Experience(db.Model):
    __tablename__ = 'experiences'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    tagline = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    video_filename = db.Column(db.String(500), nullable=True)
    audio_filename = db.Column(db.String(500), nullable=True)
    image_filename = db.Column(db.String(500), nullable=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bundle = db.relationship('Bundle', back_populates='experience', foreign_keys=[bundle_id])
    cart_items = db.relationship('CartItem', back_populates='experience', lazy='dynamic')
    order_items = db.relationship('OrderItem', back_populates='experience', lazy='dynamic')

    @property
    def display_image(self):
        if self.image_filename:
            return f'/static/uploads/experiences/{self.image_filename}'
        return 'https://placehold.co/400x300?text=Experience'

    @property
    def display_video(self):
        if self.video_filename:
            return f'/static/uploads/experiences/{self.video_filename}'
        return None

    @property
    def display_audio(self):
        if self.audio_filename:
            return f'/static/uploads/experiences/{self.audio_filename}'
        return None

    def __repr__(self):
        return f'<Experience {self.name}>'

    def __str__(self):
        return self.name
