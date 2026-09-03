"""Named sets of methods a tower keeps."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from blueline.db.models.base import Base, now


class StoredCollection(Base):
    """A named set of methods.

    The titles are kept as text separated by newlines rather than as rows in a
    join table. Nothing joins to a method from here on purpose: a tower puts
    Pudsey Surprise Major in its repertoire whether or not the library holds
    it, and a foreign key would refuse half of what a band actually rings.

    That does mean this cannot be asked which collections hold a method
    without a text match. The repository narrows on the text and the service
    checks properly, which is the same shape the ringers table uses.
    """

    __tablename__ = "collections"
    __table_args__ = (UniqueConstraint("name", name="uq_collections_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    titles: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    def __repr__(self) -> str:
        return f"StoredCollection({self.name!r})"
