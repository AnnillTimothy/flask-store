from datetime import datetime, timezone
from app.extensions import db


class Bundle(db.Model):
    __tablename__ = 'bundles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    tagline = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('BundleItem', back_populates='bundle', lazy='dynamic',
                            cascade='all, delete-orphan')
    experience = db.relationship('Experience', back_populates='bundle', uselist=False)
    cart_items = db.relationship('CartItem', back_populates='bundle', lazy='dynamic')
    order_items = db.relationship('OrderItem', back_populates='bundle', lazy='dynamic')

    @property
    def display_price(self):
        if self.sale_price is not None and self.sale_price < self.price:
            return self.sale_price
        return self.price

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def display_image(self):
        return self.image_url or 'https://placehold.co/400x300?text=Bundle'

    @property
    def total_price(self):
        """Sum of individual product prices (for savings display)."""
        from decimal import Decimal
        total = Decimal('0')
        for item in self.items:
            if item.product:
                total += item.product.price * item.quantity
        return total

    def __repr__(self):
        return f'<Bundle {self.name}>'

    def __str__(self):
        return self.name


class BundleItem(db.Model):
    __tablename__ = 'bundle_items'

    id = db.Column(db.Integer, primary_key=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    bundle = db.relationship('Bundle', back_populates='items', foreign_keys=[bundle_id])
    product = db.relationship('Product', back_populates='bundle_items', foreign_keys=[product_id])

    def __repr__(self):
        return f'<BundleItem bundle={self.bundle_id} product={self.product_id} qty={self.quantity}>'

    def __str__(self):
        product_name = self.product.name if self.product else f'Product #{self.product_id}'
        return f'{product_name} x{self.quantity}'
