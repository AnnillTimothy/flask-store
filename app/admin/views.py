import os
import re
from datetime import datetime, date
from flask import redirect, url_for, request, flash, current_app
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import SelectField, TextAreaField, StringField
from wtforms.validators import Optional as WTFOptional
from flask_wtf.file import FileField as WTFFileField, FileAllowed
from markupsafe import Markup
from app.extensions import db, admin
from app.models.user import User
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product
from app.models.bundle import Bundle, BundleItem
from app.models.experience import Experience
from app.models.order import Order, OrderItem
from app.models.shipping import ShippingRecord
from app.models.expense import Expense
from app.models.company_setting import CompanySetting
from app.models.discount_code import DiscountCode
from app.services.order_service import calculate_supplier_payouts, get_revenue_summary
from app.services.upload_service import delete_uploaded_file


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _has_file(field):
    """Return True if a form file field contains a real uploaded file."""
    data = getattr(field, 'data', None)
    return bool(data and hasattr(data, 'filename') and data.filename)


# ---------------------------------------------------------------------------
# Access control mixin
# ---------------------------------------------------------------------------

class AdminRequiredMixin:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('auth.login', next=request.url))


# ---------------------------------------------------------------------------
# Custom Admin index with dashboard stats
# ---------------------------------------------------------------------------

class SecureAdminIndexView(AdminRequiredMixin, AdminIndexView):
    @expose()
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback('index')
        stats = {
            'orders': Order.query.count(),
            'products': Product.query.count(),
            'pending_orders': Order.query.filter_by(status='pending').count(),
            'paid_orders': Order.query.filter_by(status='paid').count(),
            'processing_orders': Order.query.filter(
                Order.status.in_(['processing', 'waiting_supplier', 'in_progress', 'packed'])
            ).count(),
            'shipped_orders': Order.query.filter(
                Order.status.in_(['shipped', 'item_with_courier'])
            ).count(),
            'low_stock': Product.query.filter(Product.stock < 10).count(),
            'suppliers': Supplier.query.count(),
        }
        summary = get_revenue_summary()
        outstanding = Order.query.filter(
            Order.status.in_(['pending', 'paid', 'processing',
                              'waiting_supplier', 'in_progress', 'packed'])
        ).order_by(Order.created_at.desc()).limit(10).all()
        return self.render('admin/dashboard.html', stats=stats, summary=summary,
                           outstanding=outstanding)


# ---------------------------------------------------------------------------
# Base secure model view
# ---------------------------------------------------------------------------

class SecureModelView(AdminRequiredMixin, ModelView):
    pass


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------

class UserAdmin(AdminRequiredMixin, ModelView):
    column_list = ('id', 'username', 'email', 'phone', 'is_admin', 'created_at')
    column_searchable_list = ('username', 'email', 'phone')
    column_filters = ('is_admin',)
    can_create = False
    can_delete = True
    form_excluded_columns = ('password_hash', 'orders', 'cart')


# ---------------------------------------------------------------------------
# Supplier Admin
# ---------------------------------------------------------------------------

class SupplierAdmin(SecureModelView):
    column_list = ('id', 'name', 'website', 'contact_email', 'revenue_share_percentage',
                   'created_at')
    column_searchable_list = ('name', 'contact_email')
    column_filters = ('revenue_share_percentage',)
    form_excluded_columns = ('products', 'expenses')


# ---------------------------------------------------------------------------
# Category Admin — name only, slug auto-generated
# ---------------------------------------------------------------------------

class CategoryAdmin(SecureModelView):
    column_list = ('id', 'name')
    column_searchable_list = ('name',)
    form_columns = ('name',)

    # Hidden from the sidebar nav — categories are created inline in the Product form.
    def is_visible(self):
        return False

    def on_model_change(self, form, model, is_created):
        model.slug = re.sub(r'[^a-z0-9]+', '-', (form.name.data or '').lower()).strip('-')


# ---------------------------------------------------------------------------
# Product Admin
# ---------------------------------------------------------------------------

class ProductAdmin(SecureModelView):
    column_list = ('id', 'name', 'is_featured', 'sale_price', 'price', 'stock',
                   'category', 'supplier', 'brand')
    column_searchable_list = ('name', 'slug', 'type', 'flavor', 'brand')
    column_filters = ('category_id', 'supplier_id', 'brand', 'is_featured')
    column_editable_list = ('is_featured', 'sale_price', 'stock')
    form_excluded_columns = ('bundle_items', 'cart_items', 'order_items',
                             'created_at', 'updated_at', 'image_filename', 'image_url', 'slug')

    form_extra_fields = {
        'image_upload': WTFFileField(
            'Product Image',
            validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only!')],
        ),
        # Quick-create: type a new category name here; leave blank to use the Category dropdown above
        'new_category_name': StringField(
            'Quick-Add Category (or select above)',
            validators=[WTFOptional()],
            description='Type a new category name to create it on the fly, '
                        'or leave blank and select an existing one above.',
        ),
    }

    def on_model_delete(self, model):
        delete_uploaded_file(model.image_filename, 'products')

    def on_model_change(self, form, model, is_created):
        # Generate slug without triggering autoflush (model may have slug=None in session)
        if not model.slug:
            base = re.sub(r'[^a-z0-9]+', '-', (model.name or '').lower()).strip('-')
            slug, counter = base, 1
            with db.session.no_autoflush:
                while Product.query.filter(
                    Product.slug == slug, Product.id != (model.id or -1)
                ).first():
                    slug = f'{base}-{counter}'
                    counter += 1
            model.slug = slug
        # Quick-create category if a new name was typed
        new_cat_field = getattr(form, 'new_category_name', None)
        new_cat = (new_cat_field.data or '').strip() if new_cat_field else ''
        if new_cat:
            with db.session.no_autoflush:
                cat = Category.query.filter_by(name=new_cat).first()
            if not cat:
                cat_slug = re.sub(r'[^a-z0-9]+', '-', new_cat.lower()).strip('-')
                base_slug, n = cat_slug, 1
                with db.session.no_autoflush:
                    while Category.query.filter_by(slug=cat_slug).first():
                        cat_slug = f'{base_slug}-{n}'
                        n += 1
                cat = Category(name=new_cat, slug=cat_slug)
                db.session.add(cat)
                db.session.flush()
            model.category = cat
        if _has_file(form.image_upload):
            from app.services.upload_service import save_uploaded_file
            if model.image_filename:
                delete_uploaded_file(model.image_filename, 'products')
            filename = save_uploaded_file(form.image_upload.data, 'products')
            if filename:
                model.image_filename = filename


# ---------------------------------------------------------------------------
# Experience Admin — auto-manages linked bundle; products edited inline
# ---------------------------------------------------------------------------

class ExperienceAdmin(SecureModelView):
    column_list = ('id', 'name', 'is_featured', 'is_seasonal', 'sale_price', 'price',
                   'tagline', 'product_count', 'created_at')
    column_searchable_list = ('name', 'slug')
    column_editable_list = ('is_featured', 'is_seasonal', 'sale_price')
    column_labels = {'product_count': 'Products'}
    form_excluded_columns = ('cart_items', 'order_items', 'created_at',
                             'video_filename', 'audio_filename', 'image_filename',
                             'slug', 'bundle_id', 'bundle')

    @staticmethod
    def _product_count_formatter(view, context, model, name):
        count = model.bundle.items.count() if model.bundle else 0
        edit_url = url_for('experience.edit_view', id=model.id) + '#exp-products-panel'
        colour = '#c8a96e' if count > 0 else '#888'
        label = f'{count} product{"s" if count != 1 else ""}'
        return Markup(
            f'<a href="{edit_url}" style="color:{colour};font-weight:600;">'
            f'{label}</a>'
        )

    column_formatters = {'product_count': _product_count_formatter}

    form_extra_fields = {
        'video_upload': WTFFileField(
            'Background Video',
            validators=[FileAllowed(['mp4', 'webm', 'mov'], 'Video files only!')],
        ),
        'image_upload': WTFFileField(
            'Cover Image',
            validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only!')],
        ),
        'audio_upload': WTFFileField(
            'Background Music',
            validators=[FileAllowed(['mp3', 'ogg', 'wav', 'm4a'], 'Audio files only!')],
        ),
    }

    # Custom edit template adds inline product management below the form.
    edit_template = 'admin/experience_edit.html'

    def render(self, template, **kwargs):
        """Inject the full product list so the edit template can render the add-product dropdown."""
        if template == self.edit_template:
            kwargs.setdefault('all_products',
                              Product.query.order_by(Product.name).all())
        return super().render(template, **kwargs)

    @expose('/manage-product/', methods=['POST'])
    def manage_product(self):
        """Add or remove a product from this experience's bundle inline."""
        if not self.is_accessible():
            return redirect(url_for('auth.login'))

        experience_id = request.form.get('experience_id', type=int)
        action = request.form.get('action')
        exp = Experience.query.get(experience_id) if experience_id else None
        if not exp:
            flash('Experience not found.', 'error')
            return redirect(url_for('.index_view'))

        if action == 'add':
            product_id = request.form.get('product_id', type=int)
            qty = max(1, request.form.get('quantity', type=int, default=1))
            if product_id and exp.bundle_id:
                existing = BundleItem.query.filter_by(
                    bundle_id=exp.bundle_id, product_id=product_id
                ).first()
                if existing:
                    existing.quantity += qty
                else:
                    db.session.add(
                        BundleItem(bundle_id=exp.bundle_id,
                                   product_id=product_id, quantity=qty)
                    )
                db.session.commit()
                flash('Product added to experience.', 'success')

        elif action == 'remove':
            item_id = request.form.get('item_id', type=int)
            if item_id and exp.bundle_id:
                item = BundleItem.query.get(item_id)
                if item and item.bundle_id == exp.bundle_id:
                    db.session.delete(item)
                    db.session.commit()
                    flash('Product removed from experience.', 'success')

        return redirect(url_for('.edit_view', id=experience_id))

    def get_save_return_url(self, model, is_created=False):
        """After creating an experience, go straight to its edit page so
        products can be added immediately via the inline panel."""
        if is_created:
            return url_for('.edit_view', id=model.id)
        return super().get_save_return_url(model, is_created)

    def on_model_delete(self, model):
        """Clean up uploaded files. Bundle deletion happens in delete_model
        AFTER the experience row is removed (bundle_id is NOT NULL)."""
        delete_uploaded_file(model.video_filename, 'experiences')
        delete_uploaded_file(model.image_filename, 'experiences')
        delete_uploaded_file(model.audio_filename, 'experiences')

    def delete_model(self, model):
        """Delete the experience then clean up its orphaned bundle."""
        bundle_id = model.bundle_id
        result = super().delete_model(model)
        if result and bundle_id:
            bundle = Bundle.query.get(bundle_id)
            if bundle:
                db.session.delete(bundle)
                db.session.commit()
        return result

    def on_model_change(self, form, model, is_created):
        from app.services.upload_service import (
            save_uploaded_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS,
        )
        # Auto-slug (no_autoflush prevents flushing a model with slug=NULL)
        if not model.slug:
            base = re.sub(r'[^a-z0-9]+', '-', (model.name or '').lower()).strip('-')
            slug, counter = base, 1
            with db.session.no_autoflush:
                while Experience.query.filter(
                    Experience.slug == slug, Experience.id != (model.id or -1)
                ).first():
                    slug = f'{base}-{counter}'
                    counter += 1
            model.slug = slug

        # Ensure a bundle always exists so products can be attached.
        # Using ORM relationship assignment lets SQLAlchemy resolve the FK ordering.
        if not model.bundle_id:
            bundle = Bundle(
                name=model.name or 'Experience Bundle',
                slug=f'bundle-{model.slug or "new"}',
                price=model.price or 0,
            )
            db.session.add(bundle)
            model.bundle = bundle
        else:
            b = Bundle.query.get(model.bundle_id)
            if b:
                b.price = model.price
                b.name = model.name

        if _has_file(form.video_upload):
            if model.video_filename:
                delete_uploaded_file(model.video_filename, 'experiences')
            fn = save_uploaded_file(form.video_upload.data, 'experiences',
                                    ALLOWED_VIDEO_EXTENSIONS)
            if fn:
                model.video_filename = fn
        if _has_file(form.image_upload):
            if model.image_filename:
                delete_uploaded_file(model.image_filename, 'experiences')
            fn = save_uploaded_file(form.image_upload.data, 'experiences')
            if fn:
                model.image_filename = fn
        if _has_file(form.audio_upload):
            if model.audio_filename:
                delete_uploaded_file(model.audio_filename, 'experiences')
            fn = save_uploaded_file(form.audio_upload.data, 'experiences',
                                    ALLOWED_AUDIO_EXTENSIONS)
            if fn:
                model.audio_filename = fn


# ---------------------------------------------------------------------------
# Company Settings Admin
# ---------------------------------------------------------------------------

class CompanySettingAdmin(AdminRequiredMixin, ModelView):
    can_create = False
    can_delete = False
    column_list = ('store_name', 'tagline', 'contact_email', 'contact_phone',
                   'instagram_url', 'twitter_url', 'seasonal_section_enabled', 'updated_at')
    form_excluded_columns = ('updated_at', 'logo_filename',
                             'landing_video_filename', 'landing_audio_filename')

    form_extra_fields = {
        'logo_upload': WTFFileField(
            'Logo Upload',
            validators=[FileAllowed(['png', 'jpg', 'jpeg', 'svg', 'webp'], 'Images only!')],
        ),
        'landing_video_upload': WTFFileField(
            'Landing BG Video',
            validators=[FileAllowed(['mp4', 'webm', 'mov'], 'Video files only!')],
        ),
        'landing_audio_upload': WTFFileField(
            'Landing BG Audio',
            validators=[FileAllowed(['mp3', 'ogg', 'wav', 'm4a'], 'Audio files only!')],
        ),
    }

    def on_model_change(self, form, model, is_created):
        from app.services.upload_service import (
            save_uploaded_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS,
        )
        if _has_file(form.logo_upload):
            delete_uploaded_file(model.logo_filename, 'company')
            fn = save_uploaded_file(form.logo_upload.data, 'company',
                                    {'png', 'jpg', 'jpeg', 'svg', 'webp'})
            if fn:
                model.logo_filename = fn
        if _has_file(form.landing_video_upload):
            delete_uploaded_file(model.landing_video_filename, 'company')
            fn = save_uploaded_file(form.landing_video_upload.data, 'company',
                                    ALLOWED_VIDEO_EXTENSIONS)
            if fn:
                model.landing_video_filename = fn
        if _has_file(form.landing_audio_upload):
            delete_uploaded_file(model.landing_audio_filename, 'company')
            fn = save_uploaded_file(form.landing_audio_upload.data, 'company',
                                    ALLOWED_AUDIO_EXTENSIONS)
            if fn:
                model.landing_audio_filename = fn

    def get_query(self):
        CompanySetting.get()
        return super().get_query()


# ---------------------------------------------------------------------------
# Order Admin
# ---------------------------------------------------------------------------

class OrderAdmin(AdminRequiredMixin, ModelView):
    column_list = ('order_number', 'customer_name', 'customer_email', 'customer_phone',
                   'status', 'total_amount', 'discount_amount', 'created_at')
    column_searchable_list = ('order_number', 'customer_name', 'customer_email',
                              'customer_phone', 'payment_reference')
    column_filters = ('status', 'created_at')
    column_default_sort = ('created_at', True)
    can_create = False
    can_delete = True
    form_excluded_columns = ('items', 'shipping_record')
    form_choices = {
        'status': [(s, s.replace('_', ' ').capitalize()) for s in Order.STATUS_CHOICES]
    }

    def _customer_formatter(view, context, model, name):
        return Markup(
            f'<div style="font-size:0.82rem;">'
            f'<strong>{model.customer_name or ""}</strong><br>'
            f'<span style="color:#888;">{model.customer_email or ""}</span>'
            f'</div>'
        )

    column_formatters = {
        'customer_name': _customer_formatter,
    }


# ---------------------------------------------------------------------------
# Discount Code Admin
# ---------------------------------------------------------------------------

class DiscountCodeAdmin(SecureModelView):
    column_list = ('code', 'discount_type', 'discount_value', 'is_active',
                   'uses_count', 'max_uses', 'expires_at', 'created_at')
    column_searchable_list = ('code', 'description')
    column_filters = ('is_active', 'discount_type')
    column_editable_list = ('is_active',)
    form_excluded_columns = ('uses_count', 'created_at')
    form_choices = {
        'discount_type': [('percent', 'Percentage (%)'), ('fixed', 'Fixed Amount (R)')]
    }


# ---------------------------------------------------------------------------
# Shipping Admin
# ---------------------------------------------------------------------------

class ShippingAdmin(SecureModelView):
    column_list = ('id', 'order_id', 'tracking_number', 'carrier', 'status',
                   'shipped_at', 'delivered_at')
    column_filters = ('status',)
    form_choices = {
        'status': [(s, s.replace('_', ' ').capitalize())
                   for s in ShippingRecord.STATUS_CHOICES]
    }


# ---------------------------------------------------------------------------
# Expense Admin
# ---------------------------------------------------------------------------

class ExpenseAdmin(SecureModelView):
    column_list = ('id', 'description', 'amount', 'category', 'date', 'supplier')
    column_filters = ('category', 'supplier_id')
    column_searchable_list = ('description',)
    form_choices = {
        'category': [(c, c.capitalize()) for c in Expense.CATEGORY_CHOICES]
    }


# ---------------------------------------------------------------------------
# Revenue Report view
# ---------------------------------------------------------------------------

class RevenueReportView(AdminRequiredMixin, BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback('index')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else None
        end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else None

        summary = get_revenue_summary(start_date, end_date)
        return self.render('admin/revenue_report.html', summary=summary,
                           start=start_str or '', end=end_str or '')


# ---------------------------------------------------------------------------
# Supplier Payout Report
# ---------------------------------------------------------------------------

class SupplierPayoutView(AdminRequiredMixin, BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback('index')
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else None
        end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else None

        payouts = calculate_supplier_payouts(start_date, end_date)
        return self.render('admin/supplier_payout.html', payouts=payouts,
                           start=start_str or '', end=end_str or '')


# ---------------------------------------------------------------------------
# Shipping Report
# ---------------------------------------------------------------------------

class ShippingReportView(AdminRequiredMixin, BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback('index')
        records = (
            db.session.query(ShippingRecord, Order)
            .join(Order, ShippingRecord.order_id == Order.id)
            .order_by(ShippingRecord.id.desc())
            .all()
        )
        status_filter = request.args.get('status')
        if status_filter:
            records = [(sr, o) for sr, o in records if sr.status == status_filter]
        return self.render('admin/shipping_report.html', records=records,
                           status_filter=status_filter or '',
                           statuses=ShippingRecord.STATUS_CHOICES)


# ---------------------------------------------------------------------------
# Bundle Item Admin — hidden from nav; managed inline inside ExperienceAdmin
# ---------------------------------------------------------------------------

class BundleItemAdmin(SecureModelView):
    column_list = ('id', 'experience_name', 'product', 'quantity')
    column_searchable_list = ('bundle_id',)
    column_filters = ('bundle_id',)
    form_columns = ('bundle', 'product', 'quantity')
    column_labels = {'experience_name': 'Experience'}

    # Not shown in the sidebar — products are managed inside the Experience edit form.
    def is_visible(self):
        return False

    def _experience_name_formatter(view, context, model, name):
        if model.bundle and model.bundle.experience:
            exp = model.bundle.experience
            edit_url = url_for('experience.edit_view', id=exp.id)
            return Markup(f'<a href="{edit_url}">{exp.name}</a>')
        if model.bundle:
            return model.bundle.name
        return '—'

    column_formatters = {'experience_name': _experience_name_formatter}


# ---------------------------------------------------------------------------
# Setup function
# ---------------------------------------------------------------------------

def setup_admin(app):
    admin.init_app(app, index_view=SecureAdminIndexView())

    admin.add_view(UserAdmin(User, db.session, name='Users', category='Accounts'))
    admin.add_view(CompanySettingAdmin(CompanySetting, db.session, name='Company',
                                      category='Settings'))
    admin.add_view(SupplierAdmin(Supplier, db.session, name='Suppliers', category='Catalogue'))
    admin.add_view(ProductAdmin(Product, db.session, name='Products', category='Catalogue'))
    admin.add_view(ExperienceAdmin(Experience, db.session, name='Experiences',
                                   category='Catalogue'))
    # Categories and BundleItems are not registered as standalone admin views.
    # Categories are created inline via the Product form's quick-add field.
    # BundleItems (experience products) are managed inline via the Experience edit form.
    admin.add_view(OrderAdmin(Order, db.session, name='Orders', category='Sales'))
    admin.add_view(ShippingAdmin(ShippingRecord, db.session, name='Shipping', category='Sales'))
    admin.add_view(DiscountCodeAdmin(DiscountCode, db.session, name='Discount Codes',
                                     category='Sales'))
    admin.add_view(ExpenseAdmin(Expense, db.session, name='Expenses', category='Finance'))
    admin.add_view(RevenueReportView(name='Revenue Report', endpoint='revenue_report',
                                     category='Finance'))
    admin.add_view(SupplierPayoutView(name='Supplier Payouts', endpoint='supplier_payouts',
                                      category='Finance'))
    admin.add_view(ShippingReportView(name='Shipping Report', endpoint='shipping_report',
                                      category='Reports'))
