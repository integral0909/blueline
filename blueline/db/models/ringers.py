"""Ringers, and what they can ring."""

from __future__ import annotations


from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

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

    id = Column(Integer, primary_key=True)
    name = Column(String(80), index=True, nullable=False)
    can_ring = Column(Text, default="", nullable=False)
    learning = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    def __repr__(self) -> str:
        return f"StoredRinger({self.name!r})"
