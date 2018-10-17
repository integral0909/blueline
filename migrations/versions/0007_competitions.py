"""Striking competitions and their entries.

Revision ID: 0007
Revises: 0006
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("held_on", sa.Date(), nullable=False),
        sa.Column("place", sa.String(length=160), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("judge", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # The same competition runs every year, so the name alone cannot be
        # unique. Name and date together can: nobody holds two of the same
        # competition on one day.
        sa.UniqueConstraint("name", "held_on", name="uq_competitions_name_held_on"),
    )
    op.create_index("ix_competitions_name", "competitions", ["name"])
    op.create_index("ix_competitions_held_on", "competitions", ["held_on"])

    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("band", sa.String(length=120), nullable=False),
        # What the judge announced, not what the fault count would have said.
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("faults", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.Column("drift", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["competition_id"], ["competitions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("competition_id", "band", name="uq_entries_competition_band"),
    )
    op.create_index("ix_entries_competition_id", "entries", ["competition_id"])


def downgrade() -> None:
    op.drop_table("entries")
    op.drop_table("competitions")
