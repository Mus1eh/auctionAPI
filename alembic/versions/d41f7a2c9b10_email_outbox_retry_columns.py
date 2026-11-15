"""email outbox retry columns

Revision ID: d41f7a2c9b10
Revises: 9c1866b6b292
Create Date: 2026-11-15 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d41f7a2c9b10"
down_revision: str | Sequence[str] | None = "9c1866b6b292"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_outbox",
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("email_outbox", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column(
        "email_outbox",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_outbox", "next_attempt_at")
    op.drop_column("email_outbox", "last_error")
    op.drop_column("email_outbox", "attempts")
