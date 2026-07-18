"""Extend product_status enum

Revision ID: 08cc09f7fbe9
Revises: 1a290737154c
Create Date: 2026-07-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '08cc09f7fbe9'
down_revision = '1a290737154c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # SQLite не поддерживает ALTER TYPE. Пересоздаём колонку с новыми значениями.
    # Шаг 1: Создаём новую колонку с новым типом (VARCHAR(10))
    op.add_column('product', sa.Column('status_new', sa.String(10), nullable=True))
    
    # Шаг 2: Копируем данные из старой колонки в новую
    op.execute("UPDATE product SET status_new = status")
    
    # Шаг 3: Удаляем старую колонку
    op.drop_column('product', 'status')
    
    # Шаг 4: Переименовываем новую колонку в старое имя
    op.alter_column('product', 'status_new', new_column_name='status')

def downgrade() -> None:
    # Откат: возвращаем колонку к предыдущему состоянию
    op.add_column('product', sa.Column('status_old', sa.String(9), nullable=True))
    
    # Копируем данные (значения 'deprecated' становятся 'archived')
    op.execute("UPDATE product SET status_old = status WHERE status != 'deprecated'")
    op.execute("UPDATE product SET status_old = 'archived' WHERE status = 'deprecated'")
    
    # Удаляем новую колонку
    op.drop_column('product', 'status')
    
    # Переименовываем старую колонку обратно
    op.alter_column('product', 'status_old', new_column_name='status')