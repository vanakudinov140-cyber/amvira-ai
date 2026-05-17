"""message_versions table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-15 16:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("old_content", sa.Text(), nullable=False),
        sa.Column("new_content", sa.Text(), nullable=False),
        sa.Column(
            "source",
            sa.Enum("ai", "manual", "regenerate", name="messageversionsource", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_message_versions_message_id"),
        "message_versions",
        ["message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_message_versions_message_id"), table_name="message_versions")
    op.drop_table("message_versions")
