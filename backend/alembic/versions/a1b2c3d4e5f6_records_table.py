"""records table for yclients sync

Revision ID: a1b2c3d4e5f6
Revises: 969e1442ee05
Create Date: 2026-05-15 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "969e1442ee05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("yclients_record_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("staff_id", sa.Integer(), nullable=True),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attendance", sa.Integer(), nullable=True),
        sa.Column("save_sum", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_records_yclients_record_id"),
        "records",
        ["yclients_record_id"],
        unique=True,
    )
    op.create_index(op.f("ix_records_client_id"), "records", ["client_id"], unique=False)
    op.create_index(op.f("ix_records_staff_id"), "records", ["staff_id"], unique=False)
    op.create_index(op.f("ix_records_service_id"), "records", ["service_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_records_service_id"), table_name="records")
    op.drop_index(op.f("ix_records_staff_id"), table_name="records")
    op.drop_index(op.f("ix_records_client_id"), table_name="records")
    op.drop_index(op.f("ix_records_yclients_record_id"), table_name="records")
    op.drop_table("records")
