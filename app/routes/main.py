from flask import Blueprint, render_template, request
from app.models.product import Product
from app.models.bundle import Bundle
from app.models.category import Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    featured_bundles = Bundle.query.order_by(Bundle.created_at.desc()).limit(3).all()

    # Build experience scenes from bundles that have an experience_type
    experiences = []
    for key, label in Bundle.EXPERIENCE_TYPES:
        bundle = Bundle.query.filter_by(experience_type=key).first()
        experiences.append({
            'key': key,
            'label': label,
            'bundle': bundle,
        })

    return render_template('index.html',
                           products=featured_products,
                           bundles=featured_bundles,
                           experiences=experiences)


@main_bp.route('/products')
def products():
    category_slug = request.args.get('category')
    categories = Category.query.order_by(Category.name).all()
    query = Product.query
    active_category = None
    if category_slug:
        active_category = Category.query.filter_by(slug=category_slug).first()
        if active_category:
            query = query.filter_by(category_id=active_category.id)
    products = query.order_by(Product.name).all()
    return render_template('products/list.html',
                           products=products,
                           categories=categories,
                           active_category=active_category)


@main_bp.route('/products/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    return render_template('products/detail.html', product=product)


# Keep numeric ID route for backwards compatibility
@main_bp.route('/products/id/<int:product_id>')
def product_detail_by_id(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('products/detail.html', product=product)


@main_bp.route('/bundles')
def bundles():
    experience = request.args.get('experience')
    query = Bundle.query
    if experience:
        query = query.filter_by(experience_type=experience)
    bundles = query.order_by(Bundle.name).all()
    return render_template('bundles/list.html',
                           bundles=bundles,
                           experience_types=Bundle.EXPERIENCE_TYPES,
                           active_experience=experience)


@main_bp.route('/bundles/<slug>')
def bundle_detail(slug):
    bundle = Bundle.query.filter_by(slug=slug).first_or_404()
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
    other_bundles = Bundle.query.filter(
        Bundle.id != bundle.id
    ).order_by(Bundle.created_at.desc()).limit(4).all()
    return render_template('bundles/detail.html',
                           bundle=bundle,
                           other_bundles=other_bundles)
