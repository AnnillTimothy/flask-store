from datetime import datetime, timezone
from app.extensions import db


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('CartItem', backref='cart', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f'<Cart id={self.id}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('bundles.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'product' or 'bundle'

    @property
    def unit_price(self):
        if self.item_type == 'product' and self.product:
            return self.product.price
        if self.item_type == 'bundle' and self.bundle:
            return self.bundle.price
        return 0.0

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    @property
    def name(self):
        if self.item_type == 'product' and self.product:
            return self.product.name
        if self.item_type == 'bundle' and self.bundle:
            return self.bundle.name
        return 'Unknown Item'

    @property
    def image_url(self):
        if self.item_type == 'product' and self.product:
            return self.product.image_url
        if self.item_type == 'bundle' and self.bundle:
            return self.bundle.image_url
        return 'https://placehold.co/400x300?text=Item'

    def __repr__(self):
        return f'<CartItem id={self.id} type={self.item_type}>'
