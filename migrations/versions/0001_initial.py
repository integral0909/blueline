"""Methods and compositions.

Revision ID: 0001
Revises:
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "methods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("notation", sa.Text(), nullable=False),
        sa.Column("classification", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", name="uq_methods_title"),
    )
    op.create_index("ix_methods_title", "methods", ["title"])
    op.create_index("ix_methods_stage", "methods", ["stage"])

    op.create_table(
        "compositions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("method_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("composer", sa.String(length=80), nullable=True),
        sa.Column("calling", sa.Text(), nullable=False),
        sa.Column("length", sa.Integer(), nullable=False),
        sa.Column("is_true", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["method_id"], ["methods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compositions_method_id", "compositions", ["method_id"])
    op.create_index("ix_compositions_length", "compositions", ["length"])


def downgrade() -> None:
    op.drop_table("compositions")
    op.drop_table("methods")
