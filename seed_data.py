#!/usr/bin/env python
"""
Seed script – populate the database with demo data.
Run after:
    flask db init && flask db migrate -m "init" && flask db upgrade
"""
from datetime import date
import random

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product
from app.models.bundle import Bundle, BundleItem
from app.models.expense import Expense

app = create_app()


def seed():
    with app.app_context():
        # ------------------------------------------------------------------ #
        # Users
        # ------------------------------------------------------------------ #
        if not User.query.filter_by(email='admin@store.com').first():
            admin = User(username='admin', email='admin@store.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)

        if not User.query.filter_by(email='customer@example.com').first():
            customer = User(username='johndoe', email='customer@example.com')
            customer.set_password('password123')
            db.session.add(customer)

        db.session.commit()
        print('✓ Users seeded')

        # ------------------------------------------------------------------ #
        # Suppliers
        # ------------------------------------------------------------------ #
        suppliers_data = [
            ('TechWorld SA', 'tech@techworld.co.za', '+27 11 123 4567',
             '10 Innovation Drive, Johannesburg, GP 2000', 70.0),
            ('Fashion Hub', 'orders@fashionhub.co.za', '+27 21 987 6543',
             '5 Style Street, Cape Town, WC 8001', 65.0),
            ('HomeGoods Direct', 'supply@homegoods.co.za', '+27 31 555 0000',
             '22 Comfort Road, Durban, KN 4001', 72.0),
        ]
        suppliers = []
        for name, email, phone, address, share in suppliers_data:
            s = Supplier.query.filter_by(name=name).first()
            if not s:
                s = Supplier(name=name, email=email, phone=phone,
                             address=address, revenue_share_percentage=share)
                db.session.add(s)
            suppliers.append(s)
        db.session.commit()
        print('✓ Suppliers seeded')

        # ------------------------------------------------------------------ #
        # Categories
        # ------------------------------------------------------------------ #
        cats_data = [
            ('Electronics', 'Gadgets, devices and accessories', 'electronics'),
            ('Clothing', 'Apparel and fashion items', 'clothing'),
            ('Home & Garden', 'Everything for your home and garden', 'home-garden'),
            ('Sports', 'Sports equipment and activewear', 'sports'),
            ('Beauty', 'Skincare, makeup and wellness products', 'beauty'),
        ]
        categories = {}
        for name, desc, slug in cats_data:
            c = Category.query.filter_by(slug=slug).first()
            if not c:
                c = Category(name=name, description=desc, slug=slug)
                db.session.add(c)
            categories[slug] = c
        db.session.commit()
        print('✓ Categories seeded')

        # ------------------------------------------------------------------ #
        # Products
        # ------------------------------------------------------------------ #
        products_data = [
            # Electronics
            ('Wireless Bluetooth Headphones', 'Premium noise-cancelling wireless headphones with 30hr battery.',
             899.00, 50, 'electronics', suppliers[0]),
            ('Smart LED Desk Lamp', 'USB-powered LED desk lamp with adjustable brightness and colour temp.',
             349.00, 80, 'electronics', suppliers[0]),
            ('Portable Power Bank 20000mAh', 'Fast-charge power bank with dual USB-C and USB-A ports.',
             599.00, 60, 'electronics', suppliers[0]),

            # Clothing
            ('Classic White T-Shirt', '100% cotton unisex t-shirt available in all sizes.',
             149.00, 200, 'clothing', suppliers[1]),
            ('Slim-Fit Chino Pants', 'Modern slim-fit chinos in navy blue, perfect for casual or office wear.',
             449.00, 120, 'clothing', suppliers[1]),
            ('Zip-Up Hoodie', 'Soft fleece zip-up hoodie with kangaroo pocket.',
             399.00, 90, 'clothing', suppliers[1]),

            # Home & Garden
            ('Stainless Steel Mixing Bowls Set', 'Set of 5 nesting stainless steel mixing bowls with lids.',
             299.00, 40, 'home-garden', suppliers[2]),
            ('Indoor Herb Garden Kit', 'Complete kit with pots, soil and seeds for growing herbs indoors.',
             249.00, 35, 'home-garden', suppliers[2]),
            ('Bamboo Cutting Board Set', 'Set of 3 eco-friendly bamboo cutting boards.',
             199.00, 55, 'home-garden', suppliers[2]),

            # Sports
            ('Yoga Mat Pro', 'Non-slip 6mm thick yoga mat with carrying strap.',
             299.00, 75, 'sports', suppliers[2]),
            ('Resistance Band Set', 'Set of 5 resistance bands from light to extra-heavy.',
             199.00, 100, 'sports', suppliers[2]),
            ('Insulated Water Bottle 1L', 'Double-wall vacuum insulated stainless steel bottle.',
             249.00, 130, 'sports', suppliers[0]),

            # Beauty
            ('Vitamin C Serum 30ml', 'Brightening vitamin C serum with hyaluronic acid.',
             349.00, 60, 'beauty', suppliers[1]),
            ('Natural Shea Butter Lotion', 'Deeply moisturising body lotion with raw shea butter.',
             179.00, 80, 'beauty', suppliers[1]),
            ('Facial Cleansing Brush', 'Rechargeable sonic facial cleansing brush with 3 speed settings.',
             499.00, 45, 'beauty', suppliers[0]),
        ]

        products = []
        for name, desc, price, stock, cat_slug, supplier in products_data:
            p = Product.query.filter_by(name=name).first()
            if not p:
                p = Product(
                    name=name, description=desc, price=price,
                    stock=stock, is_active=True,
                    category_id=categories[cat_slug].id,
                    supplier_id=supplier.id,
                )
                db.session.add(p)
            products.append(p)
        db.session.commit()
        print('✓ Products seeded')

        # ------------------------------------------------------------------ #
        # Bundles
        # ------------------------------------------------------------------ #
        # Reload products so we have their IDs
        products = Product.query.all()
        prod_map = {p.name: p for p in products}

        bundles_data = [
            (
                'Tech Starter Bundle',
                'Everything you need to power up your digital life.',
                1599.00,
                [
                    ('Wireless Bluetooth Headphones', 1),
                    ('Smart LED Desk Lamp', 1),
                    ('Portable Power Bank 20000mAh', 1),
                    ('Insulated Water Bottle 1L', 1),
                ],
            ),
            (
                'Home Wellness Bundle',
                'Create a healthy and productive home environment.',
                899.00,
                [
                    ('Stainless Steel Mixing Bowls Set', 1),
                    ('Indoor Herb Garden Kit', 1),
                    ('Bamboo Cutting Board Set', 1),
                    ('Yoga Mat Pro', 1),
                    ('Insulated Water Bottle 1L', 1),
                ],
            ),
            (
                'Beauty Essentials Bundle',
                'A complete skincare and beauty routine in one box.',
                849.00,
                [
                    ('Vitamin C Serum 30ml', 1),
                    ('Natural Shea Butter Lotion', 2),
                    ('Facial Cleansing Brush', 1),
                ],
            ),
        ]

        for bname, bdesc, bprice, bitems in bundles_data:
            b = Bundle.query.filter_by(name=bname).first()
            if not b:
                b = Bundle(name=bname, description=bdesc, price=bprice, is_active=True)
                db.session.add(b)
                db.session.flush()
                for pname, qty in bitems:
                    product = prod_map.get(pname)
                    if product:
                        bi = BundleItem(bundle_id=b.id, product_id=product.id, quantity=qty)
                        db.session.add(bi)
        db.session.commit()
        print('✓ Bundles seeded')

        # ------------------------------------------------------------------ #
        # Sample Expenses
        # ------------------------------------------------------------------ #
        if Expense.query.count() == 0:
            expenses = [
                Expense(description='Google Ads – March', amount=500.00,
                        category='marketing', date=date(2024, 3, 15)),
                Expense(description='Courier bags & packaging', amount=320.00,
                        category='shipping', date=date(2024, 3, 20)),
                Expense(description='Domain & hosting renewal', amount=899.00,
                        category='operations', date=date(2024, 3, 22)),
            ]
            db.session.add_all(expenses)
            db.session.commit()
        print('✓ Expenses seeded')

        print('\n✅ Seed complete!')
        print('   Admin login: admin@store.com / admin123')


if __name__ == '__main__':
    seed()
