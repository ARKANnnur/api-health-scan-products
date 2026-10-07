from typing import Sequence, Union

from alembic import op

revision: str = "fdf420e13dc0"
down_revision: Union[str, Sequence[str], None] = "5c56697f0888"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "consent_logs_user_id_fkey",
        "consent_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "consent_logs_user_id_fkey",
        "consent_logs",
        "users",
        ["user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "consent_logs_user_id_fkey",
        "consent_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "consent_logs_user_id_fkey",
        "consent_logs",
        "profiles",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
