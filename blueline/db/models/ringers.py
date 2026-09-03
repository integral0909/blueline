"""Ringers, and what they can ring."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from blueline.db.models.base import Base, now


class StoredRinger(Base):
    """Somebody who rings at a tower, and what they can ring.

    What they can ring is stored as titles separated by newlines, the same way
    a band is. Nothing joins to a method from here: a tower captain enters
    Cambridge Surprise Major because that is what they call it, whether or not
    the library happens to hold it.
    """

    __tablename__ = "ringers"
    __table_args__ = (UniqueConstraint("name", name="uq_ringers_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    can_ring: Mapped[str] = mapped_column(Text, default="")
    learning: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    def __repr__(self) -> str:
        return f"StoredRinger({self.name!r})"
