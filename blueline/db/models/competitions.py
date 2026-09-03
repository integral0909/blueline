"""Striking competitions, and the bands who entered them."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    held_on: Mapped[date] = mapped_column(Date, index=True)
    place: Mapped[str] = mapped_column(String(160), default="")
    stage: Mapped[int] = mapped_column(Integer)
    judge: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    entries: Mapped[list[StoredEntry]] = relationship(
        back_populates="competition",
        cascade="all, delete-orphan",
        order_by="StoredEntry.position",
    )

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
        # Entries are always read as a whole set in the order announced, so
        # the two columns belong in one index rather than two.
        Index("ix_entries_position", "competition_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    band: Mapped[str] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer)
    faults: Mapped[int] = mapped_column(Integer)
    percentage: Mapped[float] = mapped_column(Float)
    drift: Mapped[str] = mapped_column(String(16), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    competition: Mapped[StoredCompetition] = relationship(back_populates="entries")

    def __repr__(self) -> str:
        return f"StoredEntry({self.band!r}, {self.position})"
