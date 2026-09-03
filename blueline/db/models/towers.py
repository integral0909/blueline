"""Rings of bells, and the performances rung on them."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from blueline.db.models.base import Base, now
from blueline.db.models.methods import StoredMethod


class StoredTower(Base):
    """A ring of bells somewhere.

    The tenor weight is kept in pounds rather than as three numbers. It is
    stored so it can be sorted and compared, and hundredweight, quarters and
    pounds do not sort as three columns without a lot of care that one integer
    does not need.
    """

    __tablename__ = "towers"
    __table_args__ = (UniqueConstraint("place", name="uq_towers_place"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    place: Mapped[str] = mapped_column(String(160), index=True)
    bells: Mapped[int] = mapped_column(Integer, index=True)
    tenor_pounds: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    def __repr__(self) -> str:
        return f"StoredTower({self.place!r}, {self.bells})"


class StoredPerformance(Base):
    """Something a band rang, written up.

    The band is stored as one string rather than a table of ringers. A peal
    board is a list of names and nothing else joins to them, and a ringers
    table that only ever gets read back as a list would be a lot of machinery
    for no question anybody is asking.
    """

    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    method_id: Mapped[int | None] = mapped_column(
        ForeignKey("methods.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tower_id: Mapped[int | None] = mapped_column(
        ForeignKey("towers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(120), index=True)
    stage: Mapped[int] = mapped_column(Integer, index=True)
    length: Mapped[int] = mapped_column(Integer, index=True)
    rang_on: Mapped[date] = mapped_column(Date, index=True)
    place: Mapped[str] = mapped_column(String(160), index=True)
    composer: Mapped[str | None] = mapped_column(String(80), nullable=True)
    #: Rows a minute, so the time it took can be worked out again. Stored
    #: because it is a fact about the performance, unlike the duration, which
    #: falls out of it and the length.
    peal_speed: Mapped[float] = mapped_column(Float, default=30.0)
    #: The band, one name per bell, separated by newlines.
    ringers: Mapped[str] = mapped_column(Text)
    conductor: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    method: Mapped[StoredMethod | None] = relationship()
    tower: Mapped[StoredTower | None] = relationship()

    def __repr__(self) -> str:
        return f"StoredPerformance({self.length} {self.title!r})"
