"""add cost_price to products, payment_method to orders, remove revenue_share_percentage from suppliers

Revision ID: f1a2b3c4d5e6
Revises: 0fcb241b7bec
Create Date: 2026-05-19 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '0fcb241b7bec'
branch_labels = None
depends_on = None


def upgrade():
    # ── Products: add cost_price (what we pay the supplier) ─────────────────
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_price', sa.Numeric(10, 2), nullable=True))

    # ── Orders: add payment_method to track PayFast vs Peach ────────────────
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_method', sa.String(length=20),
                                      nullable=True, server_default='payfast'))

    # ── Suppliers: drop revenue_share_percentage (replaced by per-product cost_price) ──
    # SQLite batch_alter handles this safely
    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        # Column may not exist on all deployments (e.g. if a previous migration failed)
        from sqlalchemy import inspect
        conn = op.get_bind()
        inspector = inspect(conn)
        cols = [c['name'] for c in inspector.get_columns('suppliers')]
        if 'revenue_share_percentage' in cols:
            batch_op.drop_column('revenue_share_percentage')


def downgrade():
    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('revenue_share_percentage', sa.Float(),
                                      nullable=False, server_default='70.0'))

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('payment_method')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('cost_price')
