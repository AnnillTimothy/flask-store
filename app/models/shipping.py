from datetime import datetime, timezone
from app.extensions import db


class ShippingRecord(db.Model):
    __tablename__ = 'shipping_records'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True, nullable=False)
    tracking_number = db.Column(db.String(100))
    carrier = db.Column(db.String(80))
    status = db.Column(db.String(30), default='processing', nullable=False)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    STATUS_CHOICES = ['processing', 'shipped', 'in_transit', 'delivered']

    def __repr__(self):
        return f'<ShippingRecord order={self.order_id} status={self.status}>'
