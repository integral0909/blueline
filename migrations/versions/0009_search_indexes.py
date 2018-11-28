"""Indexes for the columns a search actually filters on.

Revision ID: 0009
Revises: 0008

The stage, the place and the date were indexed from the start because they
were obvious. These three were not, and each of them is behind a query that
runs on every page of a listing.

Read alongside test_query_plans, which checks sqlite actually uses them. An
index nothing chooses is a write cost with no read to pay for it.
"""

from __future__ import annotations

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Searching the library by name matches the bare name rather than the
    # title, so the title index does not serve it.
    op.create_index("ix_methods_name", "methods", ["name"])

    # Every listing that narrows to Surprise, and the learning order, which
    # groups by it.
    op.create_index("ix_methods_classification", "methods", ["classification"])

    # A competition's entries are always read as a whole set in the order the
    # judge announced, so the two columns belong in one index rather than two.
    op.create_index("ix_entries_position", "entries", ["competition_id", "position"])


def downgrade() -> None:
    op.drop_index("ix_entries_position", "entries")
    op.drop_index("ix_methods_classification", "methods")
    op.drop_index("ix_methods_name", "methods")
