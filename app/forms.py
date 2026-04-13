"""
WTForms form classes for the Flask Store application.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    SelectField, SubmitField, PasswordField, BooleanField, URLField,
    FieldList, FormField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, NumberRange,
    Optional, ValidationError, URL,
)


# ---------------------------------------------------------------------------
# Auth forms
# ---------------------------------------------------------------------------

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')],
    )
    submit = SubmitField('Register')

    def validate_username(self, field):
        from app.models.user import User
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        from app.models.user import User
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


# ---------------------------------------------------------------------------
# Product form
# ---------------------------------------------------------------------------

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    type = StringField('Type', validators=[Optional(), Length(max=100)])
    quantity = StringField('Quantity / Size', validators=[Optional(), Length(max=100)])
    flavor = StringField('Flavor', validators=[Optional(), Length(max=100)])
    brand = StringField('Brand', validators=[Optional(), Length(max=200)])
    ingredients = TextAreaField('Ingredients', validators=[Optional()])
    size = StringField('Size', validators=[Optional(), Length(max=100)])
    strength = StringField('Strength', validators=[Optional(), Length(max=100)])
    price = DecimalField('Price (R)', validators=[DataRequired(), NumberRange(min=0)],
                         places=2)
    description = TextAreaField('Description', validators=[Optional()])
    image_file = FileField('Image Upload', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only!')
    ])
    image_url = StringField('Image URL (fallback)', validators=[Optional(), Length(max=500)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)],
                         default=50)
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Product')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models.category import Category
        from app.models.supplier import Supplier
        self.category_id.choices = [(0, '— Select Category —')] + [
            (c.id, c.name) for c in Category.query.order_by(Category.name).all()
        ]
        self.supplier_id.choices = [(0, '— Select Supplier —')] + [
            (s.id, s.name) for s in Supplier.query.order_by(Supplier.name).all()
        ]


# ---------------------------------------------------------------------------
# Bundle item sub-form (used within BundleForm)
# ---------------------------------------------------------------------------

class BundleItemForm(FlaskForm):
    class Meta:
        csrf = False  # sub-form; CSRF handled by parent

    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Qty', validators=[DataRequired(), NumberRange(min=1)],
                            default=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models.product import Product
        self.product_id.choices = [
            (p.id, p.name) for p in Product.query.order_by(Product.name).all()
        ]


# ---------------------------------------------------------------------------
# Bundle form
# ---------------------------------------------------------------------------

class BundleForm(FlaskForm):
    name = StringField('Bundle Name', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    tagline = StringField('Tagline', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    price = DecimalField('Bundle Price (R)', validators=[DataRequired(), NumberRange(min=0)],
                         places=2)
    image_url = StringField('Image URL', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Bundle')


# ---------------------------------------------------------------------------
# Experience form
# ---------------------------------------------------------------------------

class ExperienceForm(FlaskForm):
    name = StringField('Experience Name', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    tagline = StringField('Tagline', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    price = DecimalField('Price (R)', validators=[DataRequired(), NumberRange(min=0)],
                         places=2)
    video_file = FileField('Video Upload', validators=[
        FileAllowed(['mp4', 'webm', 'mov'], 'Video files only!')
    ])
    image_file = FileField('Image Upload', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only!')
    ])
    bundle_id = SelectField('Bundle', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Experience')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models.bundle import Bundle
        self.bundle_id.choices = [
            (b.id, b.name) for b in Bundle.query.order_by(Bundle.name).all()
        ]


# ---------------------------------------------------------------------------
# Checkout form
# ---------------------------------------------------------------------------

class CheckoutForm(FlaskForm):
    customer_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    customer_email = StringField('Email Address', validators=[DataRequired(), Email()])
    shipping_address = TextAreaField('Shipping Address', validators=[DataRequired()])
    submit = SubmitField('Proceed to Payment')


# ---------------------------------------------------------------------------
# Supplier form
# ---------------------------------------------------------------------------

class SupplierForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    website = StringField('Website', validators=[Optional(), Length(max=255)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email()])
    revenue_share_percentage = DecimalField(
        'Revenue Share %',
        validators=[DataRequired(), NumberRange(min=0, max=100)],
        places=2,
        default=70.0,
    )
    submit = SubmitField('Save Supplier')


# ---------------------------------------------------------------------------
# Category form
# ---------------------------------------------------------------------------

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=80)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')
