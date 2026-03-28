from datetime import datetime, timezone
from app.extensions import db


class ShippingRecord(db.Model):
    __tablename__ = 'shipping_records'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True, nullable=False)
    tracking_number = db.Column(db.String(100), nullable=True)
    carrier = db.Column(db.String(80), nullable=True)
    status = db.Column(db.String(30), default='processing', nullable=False)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship('Order', back_populates='shipping_record')

    STATUS_CHOICES = ['processing', 'shipped', 'in_transit', 'delivered']

    def __repr__(self):
        return f'<ShippingRecord order={self.order_id} status={self.status}>'

    def __str__(self):
        return f'Shipping #{self.order_id} – {self.status}'
