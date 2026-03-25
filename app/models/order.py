from datetime import datetime, timezone
from app.extensions import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(30), default='pending', nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=150.0, nullable=False)
    payment_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    shipping_address = db.Column(db.Text)
    customer_name = db.Column(db.String(200))
    customer_email = db.Column(db.String(120))

    items = db.relationship('OrderItem', backref='order', lazy='dynamic',
                            cascade='all, delete-orphan')
    shipping_record = db.relationship('ShippingRecord', backref='order', uselist=False)

    STATUS_CHOICES = ['pending', 'paid', 'shipped', 'delivered', 'cancelled']

    @property
    def subtotal(self):
        return self.total_amount - self.shipping_cost

    def __repr__(self):
        return f'<Order id={self.id} status={self.status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'product' or 'bundle'
    item_name = db.Column(db.String(200), nullable=False)  # name at time of purchase

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __repr__(self):
        return f'<OrderItem id={self.id} name={self.item_name}>'
