"""password reset token purpose

Revision ID: e5a1c3d7b2f4
Revises: d41f7a2c9b10
Create Date: 2026-11-16 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5a1c3d7b2f4"
down_revision: str | Sequence[str] | None = "d41f7a2c9b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # existing rows are all password reset tokens, so the default backfills them
    op.add_column(
        "password_reset_tokens",
        sa.Column(
            "purpose",
            sa.String(length=32),
            server_default="password_reset",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_purpose"),
        "password_reset_tokens",
        ["purpose"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_password_reset_tokens_purpose"), table_name="password_reset_tokens"
    )
    op.drop_column("password_reset_tokens", "purpose")
