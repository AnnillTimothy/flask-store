from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import csrf
from app.models.product import Product
from app.models.bundle import Bundle
from app.models.experience import Experience
from app.models.category import Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True).order_by(Product.created_at.desc()).limit(6).all()
    if not featured_products:
        featured_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()

    # Build experience scenes from the Experience model
    experiences = Experience.query.order_by(Experience.created_at.asc()).all()

    return render_template('index.html',
                           products=featured_products,
                           experiences=experiences)


@main_bp.route('/store')
def store():
    category_slug = request.args.get('category')
    categories = Category.query.order_by(Category.name).all()
    query = Product.query
    active_category = None
    if category_slug:
        active_category = Category.query.filter_by(slug=category_slug).first()
        if active_category:
            query = query.filter_by(category_id=active_category.id)
    all_products = query.order_by(Product.name).all()

    # Featured products — only show section when category filter is off
    featured = []
    if not active_category:
        featured = Product.query.filter_by(is_featured=True).order_by(Product.name).all()
        if not featured:
            # Fallback: newest 4 products
            featured = Product.query.order_by(Product.created_at.desc()).limit(4).all()

    is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
               or request.args.get('ajax') == '1')
    if is_ajax:
        return render_template('store/_products.html',
                               products=all_products,
                               featured=featured)

    return render_template('store/index.html',
                           products=all_products,
                           featured=featured,
                           categories=categories,
                           active_category=active_category)


@main_bp.route('/products')
def products():
    """Legacy redirect to store."""
    from flask import redirect
    args = request.args.to_dict()
    return redirect(url_for('main.store', **args), code=301)


@main_bp.route('/products/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    return render_template('products/detail.html', product=product)


# Keep numeric ID route for backwards compatibility
@main_bp.route('/products/id/<int:product_id>')
def product_detail_by_id(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('products/detail.html', product=product)


@main_bp.route('/experiences')
def experiences():
    experiences = Experience.query.order_by(Experience.name).all()
    return render_template('experiences/list.html',
                           experiences=experiences)


@main_bp.route('/experiences/<slug>')
def experience_detail(slug):
    experience = Experience.query.filter_by(slug=slug).first_or_404()
    other_experiences = Experience.query.filter(
        Experience.id != experience.id
    ).order_by(Experience.created_at.desc()).limit(4).all()
    return render_template('experiences/detail.html',
                           experience=experience,
                           other_experiences=other_experiences)


# Legacy bundle routes — redirect to experience pages
@main_bp.route('/bundles')
def bundles():
    return redirect(url_for('main.experiences'), code=301)


@main_bp.route('/bundles/<slug>')
def bundle_detail(slug):
    bundle = Bundle.query.filter_by(slug=slug).first_or_404()
    # If this bundle is linked to an experience, redirect there
    if bundle.experience:
        return redirect(url_for('main.experience_detail',
                                slug=bundle.experience.slug), code=301)
    # Otherwise show the old bundle detail
    other_bundles = Bundle.query.filter(
        Bundle.id != bundle.id
    ).order_by(Bundle.created_at.desc()).limit(4).all()
    return render_template('bundles/detail.html',
                           bundle=bundle,
                           other_bundles=other_bundles)


# Keep numeric ID route for backwards compatibility
@main_bp.route('/bundles/id/<int:bundle_id>')
def bundle_detail_by_id(bundle_id):
    bundle = Bundle.query.get_or_404(bundle_id)
    if bundle.experience:
        return redirect(url_for('main.experience_detail',
                                slug=bundle.experience.slug), code=301)
    other_bundles = Bundle.query.filter(
        Bundle.id != bundle.id
    ).order_by(Bundle.created_at.desc()).limit(4).all()
    return render_template('bundles/detail.html',
                           bundle=bundle,
                           other_bundles=other_bundles)


# ---------------------------------------------------------------------------
# Static / informational pages
# ---------------------------------------------------------------------------

@main_bp.route('/about')
def about():
    return render_template('pages/about.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')


@main_bp.route('/terms')
def terms():
    return render_template('pages/terms.html')


@main_bp.route('/contact')
def contact():
    return render_template('pages/contact.html')


# ---------------------------------------------------------------------------
# User profile & order history
# ---------------------------------------------------------------------------

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app.extensions import db
    from app.forms import ProfileUpdateForm
    from app.models.order import Order

    form = ProfileUpdateForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.phone = form.phone.data
        current_user.shipping_address = form.shipping_address.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('main.profile'))

    orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()
    ).all()
    return render_template('pages/profile.html', form=form, orders=orders)


# ---------------------------------------------------------------------------
# AI / Orb chat endpoint
# ---------------------------------------------------------------------------

@main_bp.route('/ai/chat', methods=['POST'])
@csrf.exempt
def ai_chat():
    """Chat endpoint powered by Mistral AI with store context."""
    import os, requests as req_lib
    data = request.json or {}
    user_message = (data.get('message') or '').strip()
    history = data.get('history', [])

    if not user_message:
        return jsonify({'reply': 'Please type a message.'})

    api_key = os.environ.get('MISTRAL_API_KEY', '')
    if not api_key:
        return jsonify({'reply': (
            'Our AI guide is not configured yet. '
            'Please contact us directly for assistance!'
        )})

    # Build context from database
    try:
        from app.models.product import Product
        from app.models.experience import Experience
        from app.models.category import Category
        from app.models.company_setting import CompanySetting
        from app.models.discount_code import DiscountCode

        cs = CompanySetting.get()
        store_name = cs.store_name or 'The Bodhi Tree'
        products = Product.query.filter(Product.stock > 0).order_by(Product.name).all()
        experiences = Experience.query.order_by(Experience.name).all()
        categories = Category.query.order_by(Category.name).all()

        # Active, unexpired discount codes the AI can mention
        from datetime import datetime, timezone
        active_codes = DiscountCode.query.filter_by(is_active=True).all()
        valid_codes = [
            dc for dc in active_codes
            if dc.expires_at is None or dc.expires_at > datetime.now(timezone.utc)
        ]
        if valid_codes:
            code_lines = '\n'.join(
                f"- {dc.code}: {dc}" + (f" (min R{dc.min_order_amount:.0f})" if dc.min_order_amount else "")
                for dc in valid_codes[:5]
            )
            discount_note = f"AVAILABLE DISCOUNT CODES (share when helpful):\n{code_lines}"
        else:
            discount_note = "No active discount codes at this time."

        cat_list = ', '.join(c.name for c in categories) if categories else 'Various'
        prod_lines = []
        for p in products[:30]:  # cap context length
            sale = f' (ON SALE: R{p.sale_price:.2f})' if p.is_on_sale else ''
            prod_lines.append(
                f"- {p.name} | R{p.price:.2f}{sale} | "
                f"Category: {p.category.name if p.category else 'Uncategorised'} | "
                f"Stock: {p.stock} | {(p.description or '')[:120]}"
            )
        exp_lines = []
        for e in experiences:
            sale = f' (ON SALE: R{e.sale_price:.2f})' if e.is_on_sale else ''
            exp_lines.append(
                f"- {e.name} Experience | R{e.price:.2f}{sale} | "
                f"{(e.description or '')[:120]} | URL: /experiences/{e.slug}"
            )

        system_prompt = f"""You are Bodhi, the AI guide for {store_name} — a premium, experience-driven e-commerce store.
You help customers discover products, answer questions about pricing and availability, suggest experiences, and guide them through the website.

Your personality: warm, soulful, knowledgeable, slightly mystical but grounded. You speak with care and intention.
You focus on helping the customer find what resonates with them emotionally and sensually. You gently encourage purchases but are never pushy.

STORE INFORMATION:
- Store Name: {store_name}
- Tagline: {cs.tagline or 'Enter the journey'}
- Categories: {cat_list}
- Shipping: flat-rate R{float(cs.shipping_cost or 150):.0f} nationwide South Africa

PRODUCTS AVAILABLE:
{chr(10).join(prod_lines) if prod_lines else 'Products loading...'}

EXPERIENCES AVAILABLE:
{chr(10).join(exp_lines) if exp_lines else 'No experiences yet.'}

KEY PAGES:
- Home: /
- Store (all products): /store
- Experiences: /experiences
- Cart: /cart
- About: /about
- Contact: /contact

DISCOUNT CODES:
{discount_note}

Always provide specific product names and prices when relevant. If asked about something not in stock, suggest alternatives.
Keep responses concise — 2-4 sentences unless more detail is genuinely needed. Use a gentle, flowing conversational style."""

    except Exception:
        system_prompt = "You are Bodhi, a helpful shopping assistant. Help customers with their questions."

    # Build message list
    messages = [{'role': 'system', 'content': system_prompt}]
    for h in history[-8:]:  # last 8 exchanges for context
        if h.get('role') in ('user', 'assistant') and h.get('content'):
            messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': user_message})

    try:
        resp = req_lib.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'mistral-small-latest',
                'messages': messages,
                'max_tokens': 300,
                'temperature': 0.7,
            },
            timeout=15,
        )
        resp.raise_for_status()
        reply = resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        reply = "I'm having a moment of stillness... Please try again shortly, or feel free to browse the store while I gather myself. 🌿"

    return jsonify({'reply': reply})
