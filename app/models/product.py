from datetime import datetime, timezone
from app.extensions import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    type = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.String(100), nullable=True)   # e.g. "500g", "1kg", "6-pack"
    flavor = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    stock = db.Column(db.Integer, default=50, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    category = db.relationship('Category', back_populates='products')
    supplier = db.relationship('Supplier', back_populates='products')
    bundle_items = db.relationship('BundleItem', back_populates='product', lazy='dynamic')
    cart_items = db.relationship('CartItem', back_populates='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', back_populates='product', lazy='dynamic')

    @property
    def display_image(self):
        return self.image_url or 'https://placehold.co/400x300?text=No+Image'

    def __repr__(self):
        return f'<Product {self.name}>'

    def __str__(self):
        return self.name
