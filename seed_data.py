#!/usr/bin/env python
"""
Seed script – populate the database with initial admin user data only.
Content (products, categories, bundles) is managed via the admin dashboard.

Run after:
    flask db upgrade
"""
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()


def seed():
    with app.app_context():
        # ------------------------------------------------------------------ #
        # Admin user
        # ------------------------------------------------------------------ #
        if not User.query.filter_by(email='admin@store.com').first():
            admin = User(username='admin', email='admin@store.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✓ Admin user created: admin@store.com / admin123')
        else:
            print('✓ Admin user already exists')

        print('\n✅ Seed complete!')
        print('   Log in to /admin with admin@store.com / admin123')
        print('   Use the admin dashboard to add suppliers, categories, products and bundles.')


if __name__ == '__main__':
    seed()

