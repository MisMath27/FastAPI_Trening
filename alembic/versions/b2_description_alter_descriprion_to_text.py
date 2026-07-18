"""Alter descriprion to Text

Revision ID: b2_description
Revises: a2_featured
Create Date: 2026-07-18 06:06:17.487687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2_description'
down_revision: Union[str, Sequence[str], None] = 'a2_featured'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
