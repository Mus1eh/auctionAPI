"""added user roles association

Revision ID: 4c8c1bff7bf9
Revises: 727e333865fc
Create Date: 2026-11-12 11:06:14.899494

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c8c1bff7bf9"
down_revision: str | Sequence[str] | None = "727e333865fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT users.id, roles.id
        FROM users
        JOIN roles ON roles.name = users.role_name
        WHERE users.role_name IS NOT NULL
    """)


def downgrade():
    op.drop_table("user_roles")
