from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services import cart_service

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
def view_cart():
    cart = cart_service.get_or_create_cart()
    items = list(cart.items)
    subtotal = cart_service.get_cart_total(cart)
    from flask import current_app
    shipping = current_app.config['SHIPPING_COST']
    total = subtotal + shipping
    return render_template('cart/cart.html', cart=cart, items=items,
                           subtotal=subtotal, shipping=shipping, total=total)


@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    item_type = request.form.get('item_type', 'product')
    quantity = int(request.form.get('quantity', 1))
    next_url = request.form.get('next') or request.referrer or url_for('main.index')

    if item_type == 'bundle':
        bundle_id = request.form.get('bundle_id', type=int)
        ok, msg = cart_service.add_bundle(bundle_id, quantity)
    elif item_type == 'experience':
        experience_id = request.form.get('experience_id', type=int)
        ok, msg = cart_service.add_experience(experience_id, quantity)
    else:
        product_id = request.form.get('product_id', type=int)
        ok, msg = cart_service.add_product(product_id, quantity)

    if ok:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(next_url)


@cart_bp.route('/update', methods=['POST'])
def update_cart():
    item_id = request.form.get('item_id', type=int)
    quantity = request.form.get('quantity', type=int)
    ok, msg = cart_service.update_item(item_id, quantity)
    if ok:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove', methods=['POST'])
def remove_from_cart():
    item_id = request.form.get('item_id', type=int)
    ok, msg = cart_service.remove_item(item_id)
    if ok:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/count')
def cart_count():
    cart = cart_service.get_or_create_cart()
    count = cart_service.get_cart_count(cart)
    return jsonify({'count': count})
