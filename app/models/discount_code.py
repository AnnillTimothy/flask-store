from datetime import datetime, timezone
from app.extensions import db


class DiscountCode(db.Model):
    """Discount / promo codes that can be applied at checkout."""
    __tablename__ = 'discount_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # 'percent' or 'fixed'
    discount_type = db.Column(db.String(10), nullable=False, default='percent')
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)   # None = unlimited
    uses_count = db.Column(db.Integer, default=0, nullable=False)
    min_order_amount = db.Column(db.Numeric(10, 2), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    TYPE_CHOICES = ['percent', 'fixed']

    def is_valid(self, cart_total=0):
        """Return True if the code can currently be used."""
        if not self.is_active:
            return False, 'This discount code is inactive.'
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False, 'This discount code has expired.'
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False, 'This discount code has reached its usage limit.'
        if self.min_order_amount and cart_total < float(self.min_order_amount):
            return False, f'Minimum order of R{self.min_order_amount:.2f} required.'
        return True, 'Valid'

    def calculate_discount(self, subtotal):
        """Return the discount amount to subtract from subtotal."""
        if self.discount_type == 'percent':
            return round(float(subtotal) * float(self.discount_value) / 100, 2)
        else:
            return min(float(self.discount_value), float(subtotal))

    def __repr__(self):
        return f'<DiscountCode {self.code} {self.discount_type} {self.discount_value}>'

    def __str__(self):
        if self.discount_type == 'percent':
            return f'{self.code} ({self.discount_value}% off)'
        return f'{self.code} (R{self.discount_value} off)'
