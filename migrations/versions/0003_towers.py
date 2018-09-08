"""Towers.

Revision ID: 0003
Revises: 0002
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "towers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("place", sa.String(length=160), nullable=False),
        sa.Column("bells", sa.Integer(), nullable=False),
        # In pounds rather than as three columns, because it is stored so it
        # can be sorted and hundredweight-quarters-pounds does not sort across
        # three columns without care that one integer does not need.
        sa.Column("tenor_pounds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("place", name="uq_towers_place"),
    )
    for column in ("place", "bells", "tenor_pounds"):
        op.create_index(f"ix_towers_{column}", "towers", [column])


def downgrade() -> None:
    op.drop_table("towers")
