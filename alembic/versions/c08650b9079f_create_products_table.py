"""Create products table

Revision ID: c08650b9079f
Revises: 
Create Date: 2026-07-17 05:41:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c08650b9079f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_id', 'products', ['id'])


def downgrade() -> None:
    op.drop_index('ix_products_id', table_name='products')
    op.drop_table('products')