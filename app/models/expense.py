from datetime import datetime, timezone, date
from app.extensions import db


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)

    supplier = db.relationship('Supplier', back_populates='expenses')

    CATEGORY_CHOICES = ['shipping', 'marketing', 'operations', 'inventory', 'other']

    def __repr__(self):
        return f'<Expense {self.description} R{self.amount:.2f}>'

    def __str__(self):
        return f'{self.description} – R{self.amount}'
