from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, current_app, session)
from app.extensions import db, csrf
from app.services import cart_service, order_service, payfast
from app.models.order import Order
from app.forms import CheckoutForm

checkout_bp = Blueprint('checkout', __name__)


@checkout_bp.route('/')
def checkout():
    cart = cart_service.get_or_create_cart()
    items = list(cart.items)
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    form = CheckoutForm()
    subtotal = cart_service.get_cart_total(cart)
    shipping = current_app.config['SHIPPING_COST']
    total = subtotal + shipping
    return render_template('checkout/checkout.html', form=form, items=items,
                           subtotal=subtotal, shipping=shipping, total=total)


@checkout_bp.route('/pay', methods=['POST'])
def pay():
    cart = cart_service.get_or_create_cart()
    if not list(cart.items):
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    form = CheckoutForm()
    if not form.validate_on_submit():
        subtotal = cart_service.get_cart_total(cart)
        shipping = current_app.config['SHIPPING_COST']
        total = subtotal + shipping
        return render_template('checkout/checkout.html', form=form,
                               items=list(cart.items),
                               subtotal=subtotal, shipping=shipping, total=total)

    # Store customer details in session for PayFast and confirmation page
    session['checkout_name'] = form.customer_name.data
    session['checkout_email'] = form.customer_email.data
    session['checkout_address'] = form.shipping_address.data

    shipping_cost = current_app.config['SHIPPING_COST']
    order, error = order_service.create_order_from_cart(
        cart=cart,
        customer_name=form.customer_name.data,
        customer_email=form.customer_email.data,
        shipping_address=form.shipping_address.data,
        shipping_cost=shipping_cost,
    )
    if error:
        flash(error, 'danger')
        return redirect(url_for('checkout.checkout'))

    # Store order id in session so return/cancel routes can access it
    session['pending_order_id'] = order.id

    return_url = url_for('checkout.payment_return', _external=True)
    cancel_url = url_for('checkout.payment_cancel', _external=True)
    notify_url = url_for('checkout.payment_notify', _external=True)

    payment_data = payfast.build_payment_data(
        order,
        return_url,
        cancel_url,
        notify_url,
        customer_name=form.customer_name.data,
        customer_email=form.customer_email.data,
    )
    payment_url = payfast.get_payment_url()

    return render_template('checkout/payfast_redirect.html',
                           payment_url=payment_url,
                           payment_data=payment_data)


@checkout_bp.route('/notify', methods=['POST'])
@csrf.exempt
def payment_notify():
    """PayFast ITN endpoint."""
    itn_data = request.form.to_dict()

    if not payfast.validate_itn(itn_data):
        current_app.logger.warning('Invalid PayFast ITN received')
        return 'Invalid ITN', 400

    order_id = itn_data.get('m_payment_id')
    payment_status = itn_data.get('payment_status', '').upper()
    pf_payment_id = itn_data.get('pf_payment_id', '')

    if order_id:
        order = Order.query.get(int(order_id))
        if order:
            if payment_status == 'COMPLETE':
                order.status = 'paid'
                order.payment_reference = pf_payment_id
            elif payment_status == 'FAILED':
                order.status = 'cancelled'
            db.session.commit()

    return 'OK', 200


@checkout_bp.route('/return')
def payment_return():
    order_id = session.pop('pending_order_id', None)
    order = Order.query.get(order_id) if order_id else None
    customer_name = session.pop('checkout_name', '')
    customer_email = session.pop('checkout_email', '')
    session.pop('checkout_address', None)
    return render_template('checkout/success.html', order=order,
                           customer_name=customer_name,
                           customer_email=customer_email)


@checkout_bp.route('/cancel')
def payment_cancel():
    order_id = session.pop('pending_order_id', None)
    session.pop('checkout_name', None)
    session.pop('checkout_email', None)
    session.pop('checkout_address', None)
    if order_id:
        order = Order.query.get(order_id)
        if order and order.status == 'pending':
            order.status = 'cancelled'
            db.session.commit()
    flash('Payment was cancelled. Your order has been cancelled.', 'warning')
    return redirect(url_for('main.index'))
