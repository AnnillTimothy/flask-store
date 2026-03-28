from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    products = db.relationship('Product', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

    def __str__(self):
        return self.name
