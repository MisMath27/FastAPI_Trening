"""Add is_featured column

Revision ID: add_is_featured
Revises: b2_description
Create Date: 2026-07-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_is_featured'
down_revision = 'b2_description'
branch_labels = None
depends_on = None

def upgrade() -> None:

    op.execute("""
        CREATE TABLE product_new (
            id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            price FLOAT NOT NULL,
            count INTEGER NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(10),
            is_featured BOOLEAN NOT NULL DEFAULT 0,
            PRIMARY KEY (id)
        )
    """)

    op.execute("""
        INSERT INTO product_new (id, title, price, count, description, status, is_featured)
        SELECT id, title, price, count, description, status, 0 FROM product
    """)

    op.execute("DROP TABLE product")

    op.execute("ALTER TABLE product_new RENAME TO product")

    op.execute("CREATE INDEX ix_product_id ON product (id)")

def downgrade() -> None:
    op.execute("""
        CREATE TABLE product_old (
            id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            price FLOAT NOT NULL,
            count INTEGER NOT NULL,
            description VARCHAR,
            status VARCHAR(10),
            PRIMARY KEY (id)
        )
    """)

    op.execute("""
        INSERT INTO product_old (id, title, price, count, description, status)
        SELECT id, title, price, count, description, status FROM product
    """)

    op.execute("DROP TABLE product")
    op.execute("ALTER TABLE product_old RENAME TO product")
    op.execute("CREATE INDEX ix_product_id ON product (id)")