"""Add description to products

Revision ID: 720357fee093
Revises: c08650b9079f
Create Date: 2026-07-17 05:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '720357fee093'
down_revision = 'c08650b9079f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('products_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_new_id', 'products_new', ['id'])
    
    # Копируем данные
    op.execute('''
        INSERT INTO products_new (id, title, price, count, description)
        SELECT id, title, price, count, '' FROM products
    ''')
    
    # Удаляем старую таблицу
    op.drop_table('products')
    
    # Переименовываем новую
    op.rename_table('products_new', 'products')


def downgrade() -> None:
    op.create_table('products_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_old_id', 'products_old', ['id'])
    
    op.execute('''
        INSERT INTO products_old (id, title, price, count)
        SELECT id, title, price, count FROM products
    ''')
    
    op.drop_table('products')
    op.rename_table('products_old', 'products')