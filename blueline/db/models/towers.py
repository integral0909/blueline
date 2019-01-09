"""Rings of bells, and the performances rung on them."""

from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from blueline.db.models.base import Base, now


class StoredTower(Base):
    """A ring of bells somewhere.

    The tenor weight is kept in pounds rather than as three numbers. It is
    stored so it can be sorted and compared, and hundredweight, quarters and
    pounds do not sort as three columns without a lot of care that one integer
    does not need.
    """

    __tablename__ = "towers"
    __table_args__ = (UniqueConstraint("place", name="uq_towers_place"),)

    id = Column(Integer, primary_key=True)
    place = Column(String(160), index=True, nullable=False)
    bells = Column(Integer, index=True, nullable=False)
    tenor_pounds = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

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

    id = Column(Integer, primary_key=True)
    method_id = Column(
        ForeignKey("methods.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tower_id = Column(
        ForeignKey("towers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title = Column(String(120), index=True, nullable=False)
    stage = Column(Integer, index=True, nullable=False)
    length = Column(Integer, index=True, nullable=False)
    rang_on = Column(Date, index=True, nullable=False)
    place = Column(String(160), index=True, nullable=False)
    composer = Column(String(80), nullable=True)
    #: Rows a minute, so the time it took can be worked out again. Stored
    #: because it is a fact about the performance, unlike the duration, which
    #: falls out of it and the length.
    peal_speed = Column(Float, default=30.0, nullable=False)
    #: The band, one name per bell, separated by newlines.
    ringers = Column(Text, nullable=False)
    conductor = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

    method = relationship("StoredMethod")
    tower = relationship("StoredTower")

    def __repr__(self) -> str:
        return f"StoredPerformance({self.length} {self.title!r})"
