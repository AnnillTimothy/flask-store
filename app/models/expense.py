from datetime import datetime, timezone, date
from app.extensions import db


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    CATEGORY_CHOICES = ['shipping', 'marketing', 'operations', 'inventory', 'other']

    def __repr__(self):
        return f'<Expense {self.description} R{self.amount:.2f}>'
