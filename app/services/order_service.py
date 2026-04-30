import uuid
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.services import cart_service


def _generate_order_number():
    """Generate a unique order number like ORD-A1B2C3D4."""
    return 'ORD-' + uuid.uuid4().hex[:8].upper()


def create_order_from_cart(cart, customer_name, customer_email,
                           customer_phone, shipping_address,
                           shipping_cost=150.0, discount_code=None,
                           discount_amount=0.0):
    """Create an Order from the contents of a Cart."""
    items = list(cart.items)
    if not items:
        return None, 'Cart is empty.'

    subtotal = cart_service.get_cart_total(cart)
    total = subtotal - discount_amount + shipping_cost

    order = Order(
        user_id=cart.user_id,
        order_number=_generate_order_number(),
        status='pending',
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        shipping_address=shipping_address,
        discount_code=discount_code,
        discount_amount=discount_amount,
        total_amount=max(total, 0),
        shipping_cost=shipping_cost,
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    for cart_item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            bundle_id=cart_item.bundle_id,
            experience_id=cart_item.experience_id,
            quantity=cart_item.quantity,
            price_at_purchase=cart_item.unit_price,
            item_type=cart_item.item_type,
        )
        db.session.add(order_item)

        # Decrement stock for product items
        if cart_item.item_type == 'product' and cart_item.product:
            cart_item.product.stock = max(0, cart_item.product.stock - cart_item.quantity)
        elif cart_item.item_type == 'bundle' and cart_item.bundle:
            # Reduce stock for each product in the bundle
            for bundle_item in cart_item.bundle.items:
                if bundle_item.product:
                    deduct = bundle_item.quantity * cart_item.quantity
                    bundle_item.product.stock = max(0, bundle_item.product.stock - deduct)
        elif cart_item.item_type == 'experience' and cart_item.experience:
            # Reduce stock for each product in the experience's bundle
            if cart_item.experience.bundle:
                for bundle_item in cart_item.experience.bundle.items:
                    if bundle_item.product:
                        deduct = bundle_item.quantity * cart_item.quantity
                        bundle_item.product.stock = max(0, bundle_item.product.stock - deduct)

    cart_service.clear_cart(cart)
    db.session.commit()
    return order, None


def calculate_supplier_payouts(start_date=None, end_date=None):
    """
    Return a list of dicts with supplier payout information for paid orders.
    Each dict: {supplier_id, supplier_name, revenue_share_pct, gross_revenue, payout}
    """
    from app.models.order import Order, OrderItem
    from app.models.product import Product
    from app.models.supplier import Supplier

    query = Order.query.filter(Order.status.in_(['paid', 'shipped', 'delivered']))
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    orders = query.all()
    payouts = {}  # supplier_id -> dict

    for order in orders:
        for item in order.items:
            if item.item_type != 'product' or not item.product_id:
                continue
            product = Product.query.get(item.product_id)
            if not product or not product.supplier_id:
                continue
            supplier = Supplier.query.get(product.supplier_id)
            if not supplier:
                continue

            revenue = float(item.price_at_purchase) * item.quantity
            if supplier.id not in payouts:
                payouts[supplier.id] = {
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name,
                    'revenue_share_pct': supplier.revenue_share_percentage,
                    'gross_revenue': 0.0,
                    'payout': 0.0,
                }
            payouts[supplier.id]['gross_revenue'] += revenue
            payouts[supplier.id]['payout'] += revenue * (supplier.revenue_share_percentage / 100)

    return list(payouts.values())


def get_revenue_summary(start_date=None, end_date=None):
    """Return aggregate revenue figures for paid/shipped/delivered orders."""
    from app.models.order import Order
    from app.models.expense import Expense

    query = Order.query.filter(Order.status.in_(['paid', 'shipped', 'delivered']))
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)

    orders = query.all()
    gross = sum(float(o.total_amount) for o in orders)
    shipping = sum(float(o.shipping_cost) for o in orders)

    exp_query = db.session.query(db.func.sum(Expense.amount))
    if start_date:
        exp_query = exp_query.filter(Expense.date >= start_date)
    if end_date:
        exp_query = exp_query.filter(Expense.date <= end_date)
    total_expenses = exp_query.scalar() or 0.0

    payouts = calculate_supplier_payouts(start_date, end_date)
    total_payout = sum(p['payout'] for p in payouts)

    return {
        'gross_revenue': gross,
        'shipping_revenue': shipping,
        'product_revenue': gross - shipping,
        'total_supplier_payout': total_payout,
        'total_expenses': total_expenses,
        'net_profit': gross - total_payout - total_expenses,
        'order_count': len(orders),
    }
