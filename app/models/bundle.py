from datetime import datetime, timezone
from app.extensions import db


class Bundle(db.Model):
    __tablename__ = 'bundles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('BundleItem', backref='bundle', lazy='dynamic',
                            cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='bundle', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='bundle', lazy='dynamic')

    @property
    def image_url(self):
        if self.image_filename:
            return f'/static/uploads/{self.image_filename}'
        return 'https://placehold.co/400x300?text=Bundle'

    @property
    def original_price(self):
        """Sum of individual product prices for savings display."""
        total = 0.0
        for item in self.items:
            if item.product:
                total += item.product.price * item.quantity
        return total

    def __repr__(self):
        return f'<Bundle {self.name}>'


class BundleItem(db.Model):
    __tablename__ = 'bundle_items'

    id = db.Column(db.Integer, primary_key=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    bundle_rel = db.relationship('Bundle', foreign_keys=[bundle_id], overlaps='items,bundle')
    product_rel = db.relationship('Product', foreign_keys=[product_id], overlaps='bundle_items,product')

    def __repr__(self):
        return f'<BundleItem bundle={self.bundle_id} product={self.product_id}>'
