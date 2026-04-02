import os
from datetime import datetime, date
from flask import redirect, url_for, request, flash, current_app
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user
from wtforms import SelectField
from app.extensions import db, admin
from app.models.user import User
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product
from app.models.bundle import Bundle, BundleItem
from app.models.order import Order, OrderItem
from app.models.shipping import ShippingRecord
from app.models.expense import Expense
from app.services.order_service import calculate_supplier_payouts, get_revenue_summary


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
    column_list = ('id', 'name', 'slug', 'type', 'quantity', 'flavor', 'price',
                   'stock', 'category', 'supplier')
    column_searchable_list = ('name', 'slug', 'type', 'flavor')
    column_filters = ('category_id', 'supplier_id')
    form_excluded_columns = ('bundle_items', 'cart_items', 'order_items',
                             'created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Bundle Admin  (with inline BundleItem editing)
# ---------------------------------------------------------------------------

class BundleItemInline(InlineFormAdmin):
    form_columns = ('id', 'product', 'quantity')
    form_label = 'Bundle Items'


class BundleAdmin(SecureModelView):
    column_list = ('id', 'name', 'slug', 'experience_type', 'tagline', 'price', 'created_at')
    column_searchable_list = ('name', 'slug')
    column_filters = ('experience_type',)
    form_excluded_columns = ('cart_items', 'order_items', 'created_at')
    form_choices = {
        'experience_type': [('', '— None —')] + Bundle.EXPERIENCE_TYPES,
    }
    inline_models = (BundleItemInline(BundleItem),)


class BundleItemAdmin(SecureModelView):
    column_list = ('id', 'bundle', 'product', 'quantity')
    column_searchable_list = []
    form_columns = ('bundle', 'product', 'quantity')


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
    admin.add_view(SupplierAdmin(Supplier, db.session, name='Suppliers', category='Catalogue'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Categories', category='Catalogue'))
    admin.add_view(ProductAdmin(Product, db.session, name='Products', category='Catalogue'))
    admin.add_view(BundleAdmin(Bundle, db.session, name='Bundles', category='Catalogue'))
    admin.add_view(BundleItemAdmin(BundleItem, db.session, name='Bundle Items',
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
