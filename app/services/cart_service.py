import uuid
from flask import session
from flask_login import current_user
from app.extensions import db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.bundle import Bundle
from app.models.experience import Experience


def _get_session_id():
    if 'cart_session_id' not in session:
        session['cart_session_id'] = str(uuid.uuid4())
    return session['cart_session_id']


def get_or_create_cart():
    """Return the current user's cart or a guest cart keyed by session_id."""
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
        return cart

    session_id = _get_session_id()
    cart = Cart.query.filter_by(session_id=session_id).first()
    if not cart:
        cart = Cart(session_id=session_id)
        db.session.add(cart)
        db.session.commit()
    return cart


def add_product(product_id, quantity=1):
    product = Product.query.get(product_id)
    if not product:
        return False, 'Product not found.'
    if product.stock < quantity:
        return False, 'Insufficient stock.'

    cart = get_or_create_cart()
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id,
                                    item_type='product').first()
    if item:
        new_qty = item.quantity + quantity
        if product.stock < new_qty:
            return False, 'Insufficient stock.'
        item.quantity = new_qty
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id,
                        item_type='product', quantity=quantity)
        db.session.add(item)
    db.session.commit()
    return True, 'Product added to cart.'


def add_bundle(bundle_id, quantity=1):
    bundle = Bundle.query.get(bundle_id)
    if not bundle:
        return False, 'Bundle not found.'

    cart = get_or_create_cart()
    item = CartItem.query.filter_by(cart_id=cart.id, bundle_id=bundle_id,
                                    item_type='bundle').first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, bundle_id=bundle_id,
                        item_type='bundle', quantity=quantity)
        db.session.add(item)
    db.session.commit()
    return True, 'Bundle added to cart.'


def add_experience(experience_id, quantity=1):
    experience = Experience.query.get(experience_id)
    if not experience:
        return False, 'Experience not found.'

    cart = get_or_create_cart()
    item = CartItem.query.filter_by(cart_id=cart.id, experience_id=experience_id,
                                    item_type='experience').first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, experience_id=experience_id,
                        item_type='experience', quantity=quantity)
        db.session.add(item)
    db.session.commit()
    return True, 'Experience added to cart.'


def update_item(item_id, quantity):
    cart = get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return False, 'Item not found.'
    if quantity <= 0:
        db.session.delete(item)
    else:
        if item.item_type == 'product' and item.product:
            if item.product.stock < quantity:
                return False, 'Insufficient stock.'
        item.quantity = quantity
    db.session.commit()
    return True, 'Cart updated.'


def remove_item(item_id):
    cart = get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return False, 'Item not found.'
    db.session.delete(item)
    db.session.commit()
    return True, 'Item removed.'


def get_cart_total(cart=None):
    if cart is None:
        cart = get_or_create_cart()
    return sum(item.subtotal for item in cart.items)


def get_cart_count(cart=None):
    if cart is None:
        cart = get_or_create_cart()
    return sum(item.quantity for item in cart.items)


def clear_cart(cart):
    for item in cart.items:
        db.session.delete(item)
    db.session.commit()
