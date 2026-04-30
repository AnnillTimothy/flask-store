"""add featured, sale, discount, customer, company fields

Revision ID: a1b2c3d4e5f6
Revises: 3bb2677597cc
Create Date: 2026-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '3bb2677597cc'
branch_labels = None
depends_on = None


def upgrade():
    # ── Products ─────────────────────────────────────────────────
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('sale_price', sa.Numeric(10, 2), nullable=True))

    # ── Bundles ──────────────────────────────────────────────────
    with op.batch_alter_table('bundles') as batch_op:
        batch_op.add_column(sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('sale_price', sa.Numeric(10, 2), nullable=True))

    # ── Experiences ──────────────────────────────────────────────
    with op.batch_alter_table('experiences') as batch_op:
        batch_op.add_column(sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('sale_price', sa.Numeric(10, 2), nullable=True))

    # ── Users ────────────────────────────────────────────────────
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(30), nullable=True))
        batch_op.add_column(sa.Column('shipping_address', sa.Text(), nullable=True))

    # ── Orders ───────────────────────────────────────────────────
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('customer_name', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('customer_email', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('customer_phone', sa.String(30), nullable=True))
        batch_op.add_column(sa.Column('shipping_address', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('discount_code', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))

    # ── Company Settings ─────────────────────────────────────────
    with op.batch_alter_table('company_settings') as batch_op:
        batch_op.add_column(sa.Column('logo_filename', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('contact_email', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('contact_phone', sa.String(30), nullable=True))
        batch_op.add_column(sa.Column('contact_address', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('instagram_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('facebook_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('shipping_cost', sa.Numeric(10, 2), nullable=True))

    # ── Discount Codes (new table) ────────────────────────────────
    op.create_table(
        'discount_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('discount_type', sa.String(10), nullable=False, server_default='percent'),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('uses_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_order_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )


def downgrade():
    op.drop_table('discount_codes')

    with op.batch_alter_table('company_settings') as batch_op:
        batch_op.drop_column('shipping_cost')
        batch_op.drop_column('facebook_url')
        batch_op.drop_column('instagram_url')
        batch_op.drop_column('contact_address')
        batch_op.drop_column('contact_phone')
        batch_op.drop_column('contact_email')
        batch_op.drop_column('logo_filename')

    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('discount_amount')
        batch_op.drop_column('discount_code')
        batch_op.drop_column('shipping_address')
        batch_op.drop_column('customer_phone')
        batch_op.drop_column('customer_email')
        batch_op.drop_column('customer_name')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('shipping_address')
        batch_op.drop_column('phone')

    with op.batch_alter_table('experiences') as batch_op:
        batch_op.drop_column('sale_price')
        batch_op.drop_column('is_featured')

    with op.batch_alter_table('bundles') as batch_op:
        batch_op.drop_column('sale_price')
        batch_op.drop_column('is_featured')

    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('sale_price')
        batch_op.drop_column('is_featured')
