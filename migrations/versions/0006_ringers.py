"""Ringers.

Revision ID: 0006
Revises: 0005
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ringers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        # Titles separated by newlines. Nothing joins to a method from here:
        # a captain enters what they call it whether or not the library holds
        # it, and a foreign key would refuse half of what they type.
        sa.Column("can_ring", sa.Text(), nullable=False),
        sa.Column("learning", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_ringers_name"),
    )
    op.create_index("ix_ringers_name", "ringers", ["name"])


def downgrade() -> None:
    op.drop_table("ringers")
