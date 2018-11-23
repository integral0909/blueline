"""Named sets of methods.

Revision ID: 0008
Revises: 0007
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        # Titles separated by newlines rather than rows in a join table.
        # Nothing joins to a method: a tower keeps Pudsey in its repertoire
        # whether or not the library holds it, and a foreign key would refuse
        # half of what a band rings.
        sa.Column("titles", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_collections_name"),
    )
    op.create_index("ix_collections_name", "collections", ["name"])


def downgrade() -> None:
    op.drop_table("collections")
