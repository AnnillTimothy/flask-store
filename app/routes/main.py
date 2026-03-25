from flask import Blueprint, render_template, request
from app.models.product import Product
from app.models.bundle import Bundle
from app.models.category import Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    featured_products = Product.query.filter_by(is_active=True).order_by(
        Product.created_at.desc()).limit(6).all()
    featured_bundles = Bundle.query.filter_by(is_active=True).order_by(
        Bundle.created_at.desc()).limit(3).all()
    return render_template('index.html',
                           products=featured_products,
                           bundles=featured_bundles)


@main_bp.route('/products')
def products():
    category_slug = request.args.get('category')
    categories = Category.query.order_by(Category.name).all()
    query = Product.query.filter_by(is_active=True)
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


@main_bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    return render_template('products/detail.html', product=product)


@main_bp.route('/bundles')
def bundles():
    bundles = Bundle.query.filter_by(is_active=True).order_by(Bundle.name).all()
    return render_template('bundles/list.html', bundles=bundles)


@main_bp.route('/bundles/<int:bundle_id>')
def bundle_detail(bundle_id):
    bundle = Bundle.query.filter_by(id=bundle_id, is_active=True).first_or_404()
    return render_template('bundles/detail.html', bundle=bundle)
