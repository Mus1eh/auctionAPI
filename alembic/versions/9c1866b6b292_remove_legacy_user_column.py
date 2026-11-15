"""remove legacy user column

Revision ID: 9c1866b6b292
Revises: 4c8c1bff7bf9
Create Date: 2026-11-12 14:01:10.121628

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c1866b6b292"
down_revision: str | Sequence[str] | None = "4c8c1bff7bf9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "users_role_name_fkey",
        "users",
        type_="foreignkey",
    )
    op.drop_column("users", "role_name")


def downgrade() -> None:
    op.add_column("users", sa.Column("role_name", sa.String(50), nullable=True))
    op.execute("""
        UPDATE users
        SET role_name = roles.name
        FROM user_roles
        JOIN roles ON roles.id = user_roles.role_id
        WHERE user_roles.user_id = users.id
    """)
    op.create_foreign_key(
        "users_role_name_fkey", "users", "roles", ["role_name"], ["name"]
    )
