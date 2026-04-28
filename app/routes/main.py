from flask import Blueprint, render_template, request, redirect, url_for
from app.models.product import Product
from app.models.bundle import Bundle
from app.models.experience import Experience
from app.models.category import Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
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
