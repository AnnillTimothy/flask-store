from datetime import datetime, timezone
from app.extensions import db


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    revenue_share_percentage = db.Column(db.Float, default=70.0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    products = db.relationship('Product', backref='supplier', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.name}>'
