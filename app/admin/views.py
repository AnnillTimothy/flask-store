import os
from datetime import datetime, date
from flask import redirect, url_for, request, flash, current_app
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from flask_admin.form.upload import FileUploadField
from flask_login import current_user
from wtforms import SelectField, TextAreaField
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
        # Recent orders needing attention
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
    can_delete = False
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
# Category Admin
# ---------------------------------------------------------------------------

class CategoryAdmin(SecureModelView):
    column_list = ('id', 'name', 'slug', 'description')
    column_searchable_list = ('name', 'slug')
    form_excluded_columns = ('products',)


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
                             'created_at', 'updated_at')

    form_extra_fields = {
        'image_upload': FileUploadField(
            'Image Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'products'),
            allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        ),
    }

    def on_model_delete(self, model):
        delete_uploaded_file(model.image_filename, 'products')

    def on_model_change(self, form, model, is_created):
        if hasattr(form, 'image_upload') and form.image_upload.data:
            from app.services.upload_service import save_uploaded_file
            if model.image_filename:
                delete_uploaded_file(model.image_filename, 'products')
            filename = save_uploaded_file(form.image_upload.data, 'products')
            if filename:
                model.image_filename = filename


# ---------------------------------------------------------------------------
# Bundle Admin  (with inline BundleItem editing)
# ---------------------------------------------------------------------------

class BundleItemInline(InlineFormAdmin):
    form_columns = ('id', 'product', 'quantity')
    form_label = 'Bundle Items'


class BundleAdmin(SecureModelView):
    column_list = ('id', 'name', 'is_featured', 'sale_price', 'price', 'tagline', 'created_at')
    column_searchable_list = ('name', 'slug')
    column_editable_list = ('is_featured', 'sale_price')
    form_excluded_columns = ('cart_items', 'order_items', 'created_at', 'experience')
    inline_models = (BundleItemInline(BundleItem),)


class BundleItemAdmin(SecureModelView):
    column_list = ('id', 'bundle', 'product', 'quantity')
    column_searchable_list = []
    form_columns = ('bundle', 'product', 'quantity')


# ---------------------------------------------------------------------------
# Experience Admin (with file upload for video and image)
# ---------------------------------------------------------------------------

class ExperienceAdmin(SecureModelView):
    column_list = ('id', 'name', 'is_featured', 'sale_price', 'price', 'tagline',
                   'bundle', 'created_at')
    column_searchable_list = ('name', 'slug')
    column_editable_list = ('is_featured', 'sale_price')
    form_excluded_columns = ('cart_items', 'order_items', 'created_at')

    form_extra_fields = {
        'video_upload': FileUploadField(
            'Video Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'experiences'),
            allowed_extensions=['mp4', 'webm', 'mov'],
        ),
        'image_upload': FileUploadField(
            'Image Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'experiences'),
            allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        ),
        'audio_upload': FileUploadField(
            'Background Music Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'experiences'),
            allowed_extensions=['mp3', 'ogg', 'wav', 'm4a'],
        ),
    }

    def on_model_delete(self, model):
        delete_uploaded_file(model.video_filename, 'experiences')
        delete_uploaded_file(model.image_filename, 'experiences')
        delete_uploaded_file(model.audio_filename, 'experiences')

    def on_model_change(self, form, model, is_created):
        from app.services.upload_service import save_uploaded_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS
        if hasattr(form, 'video_upload') and form.video_upload.data:
            if model.video_filename:
                delete_uploaded_file(model.video_filename, 'experiences')
            filename = save_uploaded_file(form.video_upload.data, 'experiences',
                                         ALLOWED_VIDEO_EXTENSIONS)
            if filename:
                model.video_filename = filename
        if hasattr(form, 'image_upload') and form.image_upload.data:
            if model.image_filename:
                delete_uploaded_file(model.image_filename, 'experiences')
            filename = save_uploaded_file(form.image_upload.data, 'experiences')
            if filename:
                model.image_filename = filename
        if hasattr(form, 'audio_upload') and form.audio_upload.data:
            if model.audio_filename:
                delete_uploaded_file(model.audio_filename, 'experiences')
            filename = save_uploaded_file(form.audio_upload.data, 'experiences',
                                         ALLOWED_AUDIO_EXTENSIONS)
            if filename:
                model.audio_filename = filename


# ---------------------------------------------------------------------------
# Company Settings Admin
# ---------------------------------------------------------------------------

class CompanySettingAdmin(AdminRequiredMixin, ModelView):
    can_create = False
    can_delete = False
    column_list = ('store_name', 'tagline', 'contact_email', 'contact_phone', 'updated_at')
    form_excluded_columns = ('updated_at',)

    form_extra_fields = {
        'logo_upload': FileUploadField(
            'Logo Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'company'),
            allowed_extensions=['png', 'jpg', 'jpeg', 'svg', 'webp'],
        ),
        'landing_video_upload': FileUploadField(
            'Landing BG Video Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'company'),
            allowed_extensions=['mp4', 'webm', 'mov'],
        ),
        'landing_audio_upload': FileUploadField(
            'Landing BG Audio Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'company'),
            allowed_extensions=['mp3', 'ogg', 'wav', 'm4a'],
        ),
    }

    def on_model_change(self, form, model, is_created):
        from app.services.upload_service import save_uploaded_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS
        if hasattr(form, 'logo_upload') and form.logo_upload.data:
            delete_uploaded_file(model.logo_filename, 'company')
            fn = save_uploaded_file(form.logo_upload.data, 'company',
                                    {'png', 'jpg', 'jpeg', 'svg', 'webp'})
            if fn:
                model.logo_filename = fn
        if hasattr(form, 'landing_video_upload') and form.landing_video_upload.data:
            delete_uploaded_file(model.landing_video_filename, 'company')
            fn = save_uploaded_file(form.landing_video_upload.data, 'company',
                                    ALLOWED_VIDEO_EXTENSIONS)
            if fn:
                model.landing_video_filename = fn
        if hasattr(form, 'landing_audio_upload') and form.landing_audio_upload.data:
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
    can_delete = False
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
# Setup function
# ---------------------------------------------------------------------------

def setup_admin(app):
    admin.init_app(app, index_view=SecureAdminIndexView())

    admin.add_view(UserAdmin(User, db.session, name='Users', category='Accounts'))
    admin.add_view(CompanySettingAdmin(CompanySetting, db.session, name='Company',
                                      category='Settings'))
    admin.add_view(SupplierAdmin(Supplier, db.session, name='Suppliers', category='Catalogue'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Categories', category='Catalogue'))
    admin.add_view(ProductAdmin(Product, db.session, name='Products', category='Catalogue'))
    admin.add_view(BundleAdmin(Bundle, db.session, name='Bundles', category='Catalogue'))
    admin.add_view(BundleItemAdmin(BundleItem, db.session, name='Bundle Items',
                                   category='Catalogue'))
    admin.add_view(ExperienceAdmin(Experience, db.session, name='Experiences',
                                   category='Catalogue'))
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
            'low_stock': Product.query.filter(Product.stock < 10).count(),
            'suppliers': Supplier.query.count(),
        }
        summary = get_revenue_summary()
        return self.render('admin/dashboard.html', stats=stats, summary=summary)


# ---------------------------------------------------------------------------
# Base secure model view
# ---------------------------------------------------------------------------

class SecureModelView(AdminRequiredMixin, ModelView):
    pass


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------

class UserAdmin(AdminRequiredMixin, ModelView):
    column_list = ('id', 'username', 'email', 'is_admin', 'created_at')
    column_searchable_list = ('username', 'email')
    column_filters = ('is_admin',)
    can_create = False
    can_delete = False
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
# Category Admin
# ---------------------------------------------------------------------------

class CategoryAdmin(SecureModelView):
    column_list = ('id', 'name', 'slug', 'description')
    column_searchable_list = ('name', 'slug')
    form_excluded_columns = ('products',)


# ---------------------------------------------------------------------------
# Product Admin
# ---------------------------------------------------------------------------

class ProductAdmin(SecureModelView):
    column_list = ('id', 'name', 'slug', 'brand', 'type', 'size', 'strength',
                   'quantity', 'flavor', 'price', 'stock', 'category', 'supplier')
    column_searchable_list = ('name', 'slug', 'type', 'flavor', 'brand')
    column_filters = ('category_id', 'supplier_id', 'brand')
    form_excluded_columns = ('bundle_items', 'cart_items', 'order_items',
                             'created_at', 'updated_at')

    form_extra_fields = {
        'image_upload': FileUploadField(
            'Image Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'products'),
            allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        ),
    }

    def on_model_delete(self, model):
        """Delete uploaded image when product is deleted."""
        delete_uploaded_file(model.image_filename, 'products')

    def on_model_change(self, form, model, is_created):
        """Handle image upload on create/edit."""
        if hasattr(form, 'image_upload') and form.image_upload.data:
            from app.services.upload_service import save_uploaded_file
            # Delete old file if replacing
            if model.image_filename:
                delete_uploaded_file(model.image_filename, 'products')
            filename = save_uploaded_file(form.image_upload.data, 'products')
            if filename:
                model.image_filename = filename


# ---------------------------------------------------------------------------
# Bundle Admin  (with inline BundleItem editing)
# ---------------------------------------------------------------------------

class BundleItemInline(InlineFormAdmin):
    form_columns = ('id', 'product', 'quantity')
    form_label = 'Bundle Items'


class BundleAdmin(SecureModelView):
    column_list = ('id', 'name', 'slug', 'tagline', 'price', 'created_at')
    column_searchable_list = ('name', 'slug')
    form_excluded_columns = ('cart_items', 'order_items', 'created_at', 'experience')
    inline_models = (BundleItemInline(BundleItem),)


class BundleItemAdmin(SecureModelView):
    column_list = ('id', 'bundle', 'product', 'quantity')
    column_searchable_list = []
    form_columns = ('bundle', 'product', 'quantity')


# ---------------------------------------------------------------------------
# Experience Admin (with file upload for video and image)
# ---------------------------------------------------------------------------

class ExperienceAdmin(SecureModelView):
    column_list = ('id', 'name', 'slug', 'tagline', 'price', 'bundle', 'created_at')
    column_searchable_list = ('name', 'slug')
    form_excluded_columns = ('cart_items', 'order_items', 'created_at')

    form_extra_fields = {
        'video_upload': FileUploadField(
            'Video Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'experiences'),
            allowed_extensions=['mp4', 'webm', 'mov'],
        ),
        'image_upload': FileUploadField(
            'Image Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'experiences'),
            allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        ),
        'audio_upload': FileUploadField(
            'Background Music Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'experiences'),
            allowed_extensions=['mp3', 'ogg', 'wav', 'm4a'],
        ),
    }

    def on_model_delete(self, model):
        """Delete uploaded files when experience is deleted."""
        delete_uploaded_file(model.video_filename, 'experiences')
        delete_uploaded_file(model.image_filename, 'experiences')
        delete_uploaded_file(model.audio_filename, 'experiences')

    def on_model_change(self, form, model, is_created):
        """Handle file uploads on create/edit."""
        from app.services.upload_service import save_uploaded_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS
        if hasattr(form, 'video_upload') and form.video_upload.data:
            if model.video_filename:
                delete_uploaded_file(model.video_filename, 'experiences')
            filename = save_uploaded_file(form.video_upload.data, 'experiences',
                                         ALLOWED_VIDEO_EXTENSIONS)
            if filename:
                model.video_filename = filename
        if hasattr(form, 'image_upload') and form.image_upload.data:
            if model.image_filename:
                delete_uploaded_file(model.image_filename, 'experiences')
            filename = save_uploaded_file(form.image_upload.data, 'experiences')
            if filename:
                model.image_filename = filename
        if hasattr(form, 'audio_upload') and form.audio_upload.data:
            if model.audio_filename:
                delete_uploaded_file(model.audio_filename, 'experiences')
            filename = save_uploaded_file(form.audio_upload.data, 'experiences',
                                         ALLOWED_AUDIO_EXTENSIONS)
            if filename:
                model.audio_filename = filename


# ---------------------------------------------------------------------------
# Company Settings Admin
# ---------------------------------------------------------------------------

class CompanySettingAdmin(AdminRequiredMixin, ModelView):
    """Single-row settings editor for site-wide company configuration."""
    can_create = False
    can_delete = False
    column_list = ('store_name', 'tagline', 'updated_at')
    form_excluded_columns = ('updated_at',)

    form_extra_fields = {
        'landing_video_upload': FileUploadField(
            'Landing BG Video Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'company'),
            allowed_extensions=['mp4', 'webm', 'mov'],
        ),
        'landing_audio_upload': FileUploadField(
            'Landing BG Audio Upload',
            base_path=lambda: os.path.join(current_app.config['UPLOAD_FOLDER'], 'company'),
            allowed_extensions=['mp3', 'ogg', 'wav', 'm4a'],
        ),
    }

    def on_model_change(self, form, model, is_created):
        from app.services.upload_service import save_uploaded_file, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS
        if hasattr(form, 'landing_video_upload') and form.landing_video_upload.data:
            delete_uploaded_file(model.landing_video_filename, 'company')
            fn = save_uploaded_file(form.landing_video_upload.data, 'company', ALLOWED_VIDEO_EXTENSIONS)
            if fn:
                model.landing_video_filename = fn
        if hasattr(form, 'landing_audio_upload') and form.landing_audio_upload.data:
            delete_uploaded_file(model.landing_audio_filename, 'company')
            from app.services.upload_service import ALLOWED_AUDIO_EXTENSIONS
            fn = save_uploaded_file(form.landing_audio_upload.data, 'company', ALLOWED_AUDIO_EXTENSIONS)
            if fn:
                model.landing_audio_filename = fn

    def get_query(self):
        # Ensure the single settings row always exists
        CompanySetting.get()
        return super().get_query()


# ---------------------------------------------------------------------------
# Order Admin
# ---------------------------------------------------------------------------

class OrderAdmin(AdminRequiredMixin, ModelView):
    column_list = ('id', 'order_number', 'user', 'status', 'total_amount',
                   'shipping_cost', 'payment_reference', 'created_at')
    column_searchable_list = ('order_number', 'payment_reference')
    column_filters = ('status',)
    can_create = False
    can_delete = False
    form_excluded_columns = ('items', 'shipping_record')
    form_choices = {
        'status': [(s, s.capitalize()) for s in Order.STATUS_CHOICES]
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
# Setup function
# ---------------------------------------------------------------------------

def setup_admin(app):
    admin.init_app(app, index_view=SecureAdminIndexView())

    admin.add_view(UserAdmin(User, db.session, name='Users', category='Accounts'))
    admin.add_view(CompanySettingAdmin(CompanySetting, db.session, name='Company',
                                      category='Settings'))
    admin.add_view(SupplierAdmin(Supplier, db.session, name='Suppliers', category='Catalogue'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Categories', category='Catalogue'))
    admin.add_view(ProductAdmin(Product, db.session, name='Products', category='Catalogue'))
    admin.add_view(BundleAdmin(Bundle, db.session, name='Bundles', category='Catalogue'))
    admin.add_view(BundleItemAdmin(BundleItem, db.session, name='Bundle Items',
                                   category='Catalogue'))
    admin.add_view(ExperienceAdmin(Experience, db.session, name='Experiences',
                                   category='Catalogue'))
    admin.add_view(OrderAdmin(Order, db.session, name='Orders', category='Sales'))
    admin.add_view(ShippingAdmin(ShippingRecord, db.session, name='Shipping',
                                 category='Sales'))
    admin.add_view(ExpenseAdmin(Expense, db.session, name='Expenses', category='Finance'))
    admin.add_view(RevenueReportView(name='Revenue Report', endpoint='revenue_report',
                                     category='Finance'))
    admin.add_view(SupplierPayoutView(name='Supplier Payouts', endpoint='supplier_payouts',
                                      category='Finance'))
    admin.add_view(ShippingReportView(name='Shipping Report', endpoint='shipping_report',
                                      category='Reports'))
