
"""extend user profile preferences

Revision ID: 4d0aeef4b441
Revises: d1b6cc280077
Create Date: 2026-08-10 00:48:00.838194

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "4d0aeef4b441"
down_revision: Union[str, Sequence[str], None] = "d1b6cc280077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "user_profiles",
        sa.Column(
            "role",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "user_profiles",
        sa.Column(
            "insight_preferences",
            sa.JSON(),
            nullable=True,
        ),
    )

    op.add_column(
        "user_profiles",
        sa.Column(
            "alert_preferences",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "user_profiles",
        "alert_preferences",
    )

    op.drop_column(
        "user_profiles",
        "insight_preferences",
    )

    op.drop_column(
        "user_profiles",
        "role",
    )

