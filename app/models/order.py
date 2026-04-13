from datetime import datetime, timezone
from app.extensions import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_number = db.Column(db.String(32), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), default=150.00, nullable=False)
    status = db.Column(db.String(30), default='pending', nullable=False)
    payment_reference = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('OrderItem', back_populates='order', lazy='dynamic',
                            cascade='all, delete-orphan')
    shipping_record = db.relationship('ShippingRecord', back_populates='order', uselist=False)

    STATUS_CHOICES = ['pending', 'paid', 'shipped', 'cancelled']

    @property
    def subtotal(self):
        return float(self.total_amount) - float(self.shipping_cost)

    def __repr__(self):
        return f'<Order {self.order_number} status={self.status}>'

    def __str__(self):
        return f'Order {self.order_number}'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=True)
    experience_id = db.Column(db.Integer, db.ForeignKey('experiences.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'product', 'bundle', or 'experience'

    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', back_populates='order_items')
    bundle = db.relationship('Bundle', back_populates='order_items')
    experience = db.relationship('Experience', back_populates='order_items')

    @property
    def item_name(self):
        """Derive item name from the related object."""
        if self.item_type == 'product' and self.product:
            return self.product.name
        if self.item_type == 'bundle' and self.bundle:
            return self.bundle.name
        if self.item_type == 'experience' and self.experience:
            return self.experience.name
        return 'Unknown Item'

    @property
    def subtotal(self):
        return float(self.price_at_purchase) * self.quantity

    def __repr__(self):
        return f'<OrderItem id={self.id} type={self.item_type}>'

    def __str__(self):
        return f'{self.item_name} x{self.quantity}'
