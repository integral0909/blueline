"""Striking competitions, and the bands who entered them."""

from __future__ import annotations

from typing import List

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from blueline.db.models.base import Base, now


class StoredCompetition(Base):
    """A striking competition, and what the judge marked.

    Kept because a district holds the same competition every year and the
    interesting question is not what one band scored but whether the tower is
    getting better. Answering that needs last year's sheet.

    The blow times are not stored. They run to thousands of numbers per band,
    they are only ever used to produce the marking, and a competition sheet
    that had to carry the raw recording would be the size of the recording.
    """

    __tablename__ = "competitions"
    __table_args__ = (UniqueConstraint("name", "held_on", name="uq_competitions_name_held_on"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(120), index=True, nullable=False)
    held_on = Column(Date, index=True, nullable=False)
    place = Column(String(160), default="", nullable=False)
    stage = Column(Integer, nullable=False)
    judge = Column(String(120), default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    entries = relationship("StoredEntry", back_populates="competition",
        cascade="all, delete-orphan",
        order_by="StoredEntry.position",)

    def __repr__(self) -> str:
        return f"StoredCompetition({self.name!r}, {self.held_on})"


class StoredEntry(Base):
    """One band's result in a competition.

    The position is stored rather than worked out on the way back. A judge can
    place two bands equal, or move one down for a mistake that has nothing to
    do with the fault count, and the sheet has to say what was announced rather
    than what the arithmetic would have said.
    """

    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("competition_id", "band", name="uq_entries_competition_band"),
    )

    id = Column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    band = Column(String(120), nullable=False)
    position = Column(Integer, nullable=False)
    faults = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    drift = Column(String(16), default="", nullable=False)
    note = Column(Text, default="", nullable=False)

    competition = relationship("StoredCompetition", back_populates="entries")

    def __repr__(self) -> str:
        return f"StoredEntry({self.band!r}, {self.position})"
