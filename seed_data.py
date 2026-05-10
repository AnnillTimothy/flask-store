#!/usr/bin/env python
"""
seed_data.py  –  Populate the database with real store content.
=================================================================

HOW TO USE
----------
1.  Run migrations first:      flask db upgrade
2.  Fill in your data below in each DATA section.
3.  Run this script:           python seed_data.py

The script is idempotent – running it twice won't create duplicates.
Re-run any time you add new rows to the data sections below.

DATA MODEL QUICK REFERENCE
---------------------------
Supplier   – who supplies/makes the product (used for payout reporting)
Category   – product grouping shown in the store filter
Product    – individual item sold on its own; belongs to a Supplier & Category
Experience – the "vibe" product the customer actually buys, e.g. "Lo-Fi Nights"
             Each Experience owns a Bundle (auto-created here).
             Bundle    – internal record that groups the physical items included
             BundleItem– one product + quantity inside a Bundle
DiscountCode – promo codes applied at checkout

CORE CONCEPT
------------
Customers buy an Experience (a mood / ritual / feeling).
Behind the scenes that Experience is fulfilled by shipping the bundle of
physical products defined in its BundleItems.
Example: "The Forest Walk Experience" → Bundle contains:
    1× Blue Lotus Tea  +  1× Functional Mushroom Coffee  +  1× Hydration Electrolytes
"""

import re
import sys
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.company_setting import CompanySetting
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product
from app.models.bundle import Bundle, BundleItem
from app.models.experience import Experience
from app.models.discount_code import DiscountCode

app = create_app()


# ============================================================
# HELPERS
# ============================================================

def _slugify(text):
    """Convert a name to a URL-safe slug."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def _get_or_create(model, filter_by, **defaults):
    """
    Fetch an existing row by filter_by kwargs, or create a new one.
    Returns (instance, created:bool).
    """
    obj = model.query.filter_by(**filter_by).first()
    if obj:
        return obj, False
    obj = model(**filter_by, **defaults)
    db.session.add(obj)
    db.session.flush()   # populate obj.id without a full commit
    return obj, True


# ============================================================
# ① COMPANY SETTINGS  (single row – edit to match the real store)
# ============================================================
# These values appear in email footers, the About page, SEO meta tags, etc.
# Leave a field as None if you don't have it yet.

COMPANY = dict(
    store_name               = 'The Bodhi Tree',
    tagline                  = 'Enter the journey',
    contact_email            = None,           # e.g. 'hello@thebodhitree.co.za'
    contact_phone            = None,           # e.g. '+27 71 000 0000'
    contact_address          = None,           # full postal / physical address
    instagram_url            = None,           # e.g. 'https://instagram.com/thebodhitree'
    facebook_url             = None,
    twitter_url              = None,
    about_text               = None,           # long-form "About Us" copy
    terms_text               = None,           # Terms & Conditions copy
    privacy_text             = None,           # Privacy Policy copy
    store_hero_title         = 'Explore the Collection',
    store_hero_sub           = 'Rituals for the mind, body & spirit.',
    store_wisdom_1           = None,           # optional quote / tagline on store page
    store_wisdom_2           = None,
    store_wisdom_3           = None,
    seasonal_section_enabled = False,
    seasonal_section_title   = 'Limited-Time Specials',
)


# ============================================================
# ② SUPPLIERS  (who makes / ships the products)
# ============================================================
# Add as many dicts as you have suppliers.
# revenue_share_percentage = how much of the sale price goes to the supplier (default 70 %).

SUPPLIERS = [
    # ── ADD YOUR SUPPLIERS BELOW ─────────────────────────────────────
    # dict(
    #     name                    = 'Example Supplier Co.',
    #     website                 = 'https://example.com',
    #     contact_email           = 'orders@example.com',
    #     revenue_share_percentage= 70.0,
    # ),
    # ─────────────────────────────────────────────────────────────────
]


# ============================================================
# ③ CATEGORIES  (product groupings shown in store filters)
# ============================================================

CATEGORIES = [
    # ── ADD YOUR CATEGORIES BELOW ────────────────────────────────────
    # 'Herbal Teas',
    # 'Adaptogens & Mushrooms',
    # 'Wellness Supplements',
    # 'Treats & Confectionery',
    # 'Skincare & Topicals',
    # ─────────────────────────────────────────────────────────────────
]


# ============================================================
# ④ PRODUCTS  (individual items sold in the store)
# ============================================================
# Each dict maps directly to Product model fields.
# 'supplier'  – matches Supplier.name  (must exist in SUPPLIERS above, or already in DB)
# 'category'  – matches Category.name  (must exist in CATEGORIES above, or already in DB)
# 'quantity'  – the pack size/weight shown to the customer, e.g. '30g', '1kg', '12-pack'
# 'strength'  – for functional products, e.g. 'Extra Strength', '500mg'
# Leave any optional field as None if you don't have it yet.

PRODUCTS = [
    # ── ADD YOUR PRODUCTS BELOW ──────────────────────────────────────

    # Example:
    # dict(
    #     name        = 'Blue Lotus Tea',
    #     description = 'A calming, dreamy herbal tea made from dried blue lotus flowers.',
    #     price       = 149.00,
    #     stock       = 50,
    #     category    = 'Herbal Teas',       # must match a Category name
    #     supplier    = 'Example Supplier Co.',  # must match a Supplier name
    #     brand       = 'Bodhi Botanicals',
    #     quantity    = '20 sachets',
    #     size        = None,
    #     flavor      = None,
    #     strength    = None,
    #     type        = 'loose-leaf tea',
    #     ingredients = 'Nymphaea caerulea (blue lotus) flower',
    #     is_featured = True,
    #     sale_price  = None,
    # ),
    # dict(
    #     name        = 'Functional Mushroom Coffee',
    #     description = 'Rich, smooth coffee blended with lion\'s mane and chaga.',
    #     price       = 189.00,
    #     stock       = 40,
    #     category    = 'Adaptogens & Mushrooms',
    #     supplier    = 'Example Supplier Co.',
    #     brand       = 'Bodhi Botanicals',
    #     quantity    = '200g',
    #     size        = None,
    #     flavor      = 'Original',
    #     strength    = None,
    #     type        = 'functional coffee',
    #     ingredients = 'Arabica coffee, Lion\'s Mane (Hericium erinaceus), Chaga (Inonotus obliquus)',
    #     is_featured = True,
    #     sale_price  = None,
    # ),
    # dict(
    #     name        = 'Hydration Electrolytes',
    #     description = 'Pure mineral electrolyte blend – no sugar, no fillers.',
    #     price       = 129.00,
    #     stock       = 60,
    #     category    = 'Wellness Supplements',
    #     supplier    = 'Example Supplier Co.',
    #     brand       = 'Bodhi Botanicals',
    #     quantity    = '30 sachets',
    #     size        = None,
    #     flavor      = 'Unflavoured',
    #     strength    = None,
    #     type        = 'supplement',
    #     ingredients = 'Sodium, Potassium, Magnesium, Calcium, Trace minerals',
    #     is_featured = False,
    #     sale_price  = None,
    # ),

    # ─────────────────────────────────────────────────────────────────
]


# ============================================================
# ⑤ EXPERIENCES  (the curated bundles customers actually buy)
# ============================================================
# Each Experience has a name, description, price, and a list of
# 'items' – (product_name, quantity) tuples.
#
# The product_name in each item MUST match the name field of a
# product in PRODUCTS above (or a product already in the database).
#
# price    = what the customer pays for the full experience
# tagline  = short marketing line shown on the experience card
# is_featured = show on homepage featured section?
# is_seasonal = show in the seasonal specials section?
# sale_price  = discounted price if on sale (None = not on sale)

EXPERIENCES = [
    # ── ADD YOUR EXPERIENCES BELOW ───────────────────────────────────

    # Example:
    # dict(
    #     name        = 'The Forest Walk Experience',
    #     tagline     = 'Ground yourself in the stillness of the forest.',
    #     description = (
    #         'Close your eyes. You\'re walking through a cool, mossy forest at dawn. '
    #         'This experience box is your forest in a cup – earthy, alive, restorative.'
    #     ),
    #     price       = 399.00,
    #     is_featured = True,
    #     is_seasonal = False,
    #     sale_price  = None,
    #     items       = [
    #         ('Blue Lotus Tea',             1),
    #         ('Functional Mushroom Coffee', 1),
    #         ('Hydration Electrolytes',     1),
    #     ],
    # ),
    # dict(
    #     name        = 'Lo-Fi Nights Experience',
    #     tagline     = 'Slow down. Sink in. Let the night be soft.',
    #     description = (
    #         'Chamomile, rose, rich dark chocolate – a ritual for winding down '
    #         'when the world goes quiet.'
    #     ),
    #     price       = 349.00,
    #     is_featured = True,
    #     is_seasonal = False,
    #     sale_price  = None,
    #     items       = [
    #         ('Chamomile Tea',         1),
    #         ('Rose Turkish Delight',  1),
    #         ('Dark Hot Chocolate',    1),
    #     ],
    # ),

    # ─────────────────────────────────────────────────────────────────
]


# ============================================================
# ⑥ DISCOUNT CODES  (promo codes for checkout)
# ============================================================
# discount_type  = 'percent'  (e.g. 10% off)  or  'fixed'  (e.g. R50 off)
# discount_value = the number – 10 means 10% or R10 depending on type
# max_uses       = None means unlimited
# min_order_amount = minimum cart total before code applies (None = no minimum)

DISCOUNT_CODES = [
    dict(
        code             = 'WELCOME10',
        description      = '10% welcome discount for new subscribers',
        discount_type    = 'percent',
        discount_value   = 10,
        is_active        = True,
        max_uses         = None,
        min_order_amount = None,
    ),
    # ── ADD MORE CODES BELOW ─────────────────────────────────────────
    # dict(
    #     code             = 'BODHI50',
    #     description      = 'R50 off orders over R500',
    #     discount_type    = 'fixed',
    #     discount_value   = 50,
    #     is_active        = True,
    #     max_uses         = None,
    #     min_order_amount = 500,
    # ),
    # ─────────────────────────────────────────────────────────────────
]


# ============================================================
# SEED FUNCTIONS  (no edits needed below this line)
# ============================================================

def seed_company():
    cs = CompanySetting.query.first()
    if not cs:
        cs = CompanySetting()
        db.session.add(cs)
    for key, value in COMPANY.items():
        if value is not None:
            setattr(cs, key, value)
    db.session.flush()
    print('✓ Company settings')


def seed_suppliers():
    for data in SUPPLIERS:
        _, created = _get_or_create(
            Supplier,
            filter_by={'name': data['name']},
            website=data.get('website'),
            contact_email=data.get('contact_email'),
            revenue_share_percentage=data.get('revenue_share_percentage', 70.0),
        )
        status = 'created' if created else 'already exists'
        print(f'  Supplier [{status}]: {data["name"]}')
    if SUPPLIERS:
        print(f'✓ {len(SUPPLIERS)} supplier(s)')


def seed_categories():
    for name in CATEGORIES:
        _, created = _get_or_create(
            Category,
            filter_by={'name': name},
            slug=_slugify(name),
        )
        status = 'created' if created else 'already exists'
        print(f'  Category [{status}]: {name}')
    if CATEGORIES:
        print(f'✓ {len(CATEGORIES)} categor{"y" if len(CATEGORIES) == 1 else "ies"}')


def seed_products():
    for data in PRODUCTS:
        name = data['name']

        # Resolve foreign keys by name
        supplier = (
            Supplier.query.filter_by(name=data['supplier']).first()
            if data.get('supplier') else None
        )
        category = (
            Category.query.filter_by(name=data['category']).first()
            if data.get('category') else None
        )

        existing = Product.query.filter_by(name=name).first()
        if existing:
            print(f'  Product [already exists]: {name}')
            continue

        slug = _slugify(name)
        # Ensure slug uniqueness
        base, n = slug, 1
        while Product.query.filter_by(slug=slug).first():
            slug = f'{base}-{n}'; n += 1

        product = Product(
            name        = name,
            slug        = slug,
            description = data.get('description'),
            price       = data['price'],
            stock       = data.get('stock', 50),
            brand       = data.get('brand'),
            quantity    = data.get('quantity'),
            size        = data.get('size'),
            flavor      = data.get('flavor'),
            strength    = data.get('strength'),
            type        = data.get('type'),
            ingredients = data.get('ingredients'),
            is_featured = data.get('is_featured', False),
            sale_price  = data.get('sale_price'),
            supplier_id = supplier.id if supplier else None,
            category_id = category.id if category else None,
        )
        db.session.add(product)
        db.session.flush()
        print(f'  Product [created]: {name}')

    if PRODUCTS:
        print(f'✓ {len(PRODUCTS)} product(s)')


def seed_experiences():
    """
    Create Experiences with their bundled products.

    Data flow:
        1. Create a Bundle (internal record, never shown to the customer directly).
        2. Create the Experience pointing to that Bundle (Experience.bundle_id = Bundle.id).
        3. Create BundleItems linking specific Products + quantities to the Bundle.

    The customer buys the Experience; the Bundle drives fulfilment.
    """
    for data in EXPERIENCES:
        name = data['name']
        existing = Experience.query.filter_by(name=name).first()
        if existing:
            print(f'  Experience [already exists]: {name}')
            continue

        # Generate slug for the experience
        slug = _slugify(name)
        base, n = slug, 1
        while Experience.query.filter_by(slug=slug).first():
            slug = f'{base}-{n}'; n += 1

        # ── Step 1: create the internal Bundle ──────────────────────
        bundle_slug = f'bundle-{slug}'
        base_bs, m = bundle_slug, 1
        while Bundle.query.filter_by(slug=bundle_slug).first():
            bundle_slug = f'{base_bs}-{m}'; m += 1

        bundle = Bundle(
            name  = f'{name} Bundle',
            slug  = bundle_slug,
            price = data['price'],      # kept in sync with the experience price
        )
        db.session.add(bundle)
        db.session.flush()   # need bundle.id before creating Experience

        # ── Step 2: create the Experience ───────────────────────────
        experience = Experience(
            name        = name,
            slug        = slug,
            tagline     = data.get('tagline'),
            description = data.get('description'),
            price       = data['price'],
            sale_price  = data.get('sale_price'),
            is_featured = data.get('is_featured', False),
            is_seasonal = data.get('is_seasonal', False),
            bundle_id   = bundle.id,
        )
        db.session.add(experience)
        db.session.flush()

        # ── Step 3: add the bundled products (BundleItems) ──────────
        items_added = []
        for product_name, qty in data.get('items', []):
            product = Product.query.filter_by(name=product_name).first()
            if not product:
                print(f'    ⚠️  Product not found for bundle item: "{product_name}" '
                      f'(experience: {name}) – skipping')
                continue
            db.session.add(BundleItem(
                bundle_id  = bundle.id,
                product_id = product.id,
                quantity   = qty,
            ))
            items_added.append(f'{qty}× {product_name}')

        print(f'  Experience [created]: {name}')
        if items_added:
            print(f'    Bundle: {", ".join(items_added)}')
        else:
            print(f'    Bundle: (no items – add products via /admin)')

    if EXPERIENCES:
        print(f'✓ {len(EXPERIENCES)} experience(s)')


def seed_discount_codes():
    for data in DISCOUNT_CODES:
        _, created = _get_or_create(
            DiscountCode,
            filter_by={'code': data['code']},
            description      = data.get('description'),
            discount_type    = data['discount_type'],
            discount_value   = data['discount_value'],
            is_active        = data.get('is_active', True),
            max_uses         = data.get('max_uses'),
            min_order_amount = data.get('min_order_amount'),
        )
        status = 'created' if created else 'already exists'
        print(f'  Code [{status}]: {data["code"]}')
    if DISCOUNT_CODES:
        print(f'✓ {len(DISCOUNT_CODES)} discount code(s)')


def seed_admin():
    email = 'admin@store.com'
    if not User.query.filter_by(email=email).first():
        admin = User(username='admin', email=email, is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        print(f'✓ Admin user created: {email} / admin123')
        print('  ⚠️  Change this password immediately after first login!')
    else:
        print(f'✓ Admin user already exists: {email}')


# ============================================================
# MAIN
# ============================================================

def seed():
    with app.app_context():
        # In production always run `flask db upgrade` before seeding.
        # For a brand-new SQLite dev database we create tables on the fly.
        db.create_all()

        print('\n🌱  Seeding database …\n')

        seed_company()
        seed_suppliers()
        seed_categories()
        seed_products()
        seed_experiences()
        seed_discount_codes()
        seed_admin()

        db.session.commit()

        print('\n✅  Seed complete!')
        print('   Admin login:  /admin  →  admin@store.com / admin123')
        print('   Products:     add media (images) via the admin Products section')
        print('   Experiences:  add media (video/audio/image) via the admin Experiences section')
        print()


if __name__ == '__main__':
    seed()

