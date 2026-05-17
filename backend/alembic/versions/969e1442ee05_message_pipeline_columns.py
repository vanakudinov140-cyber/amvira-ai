"""message pipeline columns

Revision ID: 969e1442ee05
Revises: 9e87767e0122
Create Date: 2026-05-13 15:28:37.884982

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "969e1442ee05"
down_revision: Union[str, Sequence[str], None] = "9e87767e0122"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("action", sa.String(length=64), nullable=True))
    op.add_column(
        "messages",
        sa.Column("prepared_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(sa.text("UPDATE messages SET action = 'legacy' WHERE action IS NULL"))
    op.execute(sa.text("UPDATE messages SET prepared_at = created_at WHERE prepared_at IS NULL"))
    op.execute(
        sa.text(
            "UPDATE messages SET status = 'pending' "
            "WHERE status NOT IN ('pending', 'sent', 'failed')"
        ),
    )

    op.alter_column(
        "messages",
        "action",
        existing_type=sa.String(length=64),
        nullable=False,
        server_default="legacy",
    )
    op.alter_column(
        "messages",
        "prepared_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column("messages", "action", server_default=None)


def downgrade() -> None:
    op.drop_column("messages", "sent_at")
    op.drop_column("messages", "prepared_at")
    op.drop_column("messages", "action")
