"""How fast a performance was rung.

Revision ID: 0005
Revises: 0004
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

#: Thirty rows a minute, which is ordinary for a tower of eight. Anything
#: already stored was recorded before this column existed and thirty is the
#: least wrong guess for it.
DEFAULT_SPEED = 30.0


def upgrade() -> None:
    with op.batch_alter_table("performances") as batch:
        batch.add_column(
            sa.Column(
                "peal_speed",
                sa.Float(),
                nullable=False,
                server_default=str(DEFAULT_SPEED),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("performances") as batch:
        batch.drop_column("peal_speed")
