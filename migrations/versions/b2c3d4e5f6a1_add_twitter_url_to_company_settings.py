"""add twitter_url to company_settings

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('company_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('twitter_url', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('company_settings', schema=None) as batch_op:
        batch_op.drop_column('twitter_url')
