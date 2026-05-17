"""message_feedback table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-15 18:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("approved_by_operator", sa.Boolean(), nullable=True),
        sa.Column("manually_edited", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("edited_ratio", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("client_returned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("return_days", sa.Integer(), nullable=True),
        sa.Column("revenue_after_return", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id"),
    )
    op.create_index(
        op.f("ix_message_feedback_message_id"),
        "message_feedback",
        ["message_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_message_feedback_message_id"), table_name="message_feedback")
    op.drop_table("message_feedback")
