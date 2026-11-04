"""add cancelled approval status

Revision ID: a6f644949401
Revises: b3f0fb2ee1db
Create Date: 2026-11-04 13:31:03.620514

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a6f644949401"
down_revision: str | Sequence[str] | None = "b3f0fb2ee1db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE approval_status ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    """Downgrade schema."""
