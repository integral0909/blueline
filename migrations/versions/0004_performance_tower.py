"""Link a performance to the tower it was rung at.

Revision ID: 0004
Revises: 0003
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch mode because sqlite cannot add a foreign key to an existing table
    # in place. It rebuilds the table around the new column instead.
    with op.batch_alter_table("performances") as batch:
        batch.add_column(sa.Column("tower_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_performances_tower_id",
            "towers",
            ["tower_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_performances_tower_id", "performances", ["tower_id"])


def downgrade() -> None:
    op.drop_index("ix_performances_tower_id", "performances")
    with op.batch_alter_table("performances") as batch:
        batch.drop_constraint("fk_performances_tower_id", type_="foreignkey")
        batch.drop_column("tower_id")
