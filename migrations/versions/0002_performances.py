"""Performances.

Revision ID: 0002
Revises: 0001
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("method_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("length", sa.Integer(), nullable=False),
        sa.Column("rang_on", sa.Date(), nullable=False),
        sa.Column("place", sa.String(length=160), nullable=False),
        sa.Column("composer", sa.String(length=80), nullable=True),
        sa.Column("ringers", sa.Text(), nullable=False),
        sa.Column("conductor", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # A method being deleted should not take the performances with it.
        # Somebody rang that peal whether or not the library still holds the
        # method, so the link goes null rather than the row going away.
        sa.ForeignKeyConstraint(["method_id"], ["methods.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("method_id", "title", "stage", "length", "rang_on", "place"):
        op.create_index(f"ix_performances_{column}", "performances", [column])


def downgrade() -> None:
    op.drop_table("performances")
