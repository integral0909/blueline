"""Methods, and the compositions written for them."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from blueline.db.models.base import Base, now


class StoredMethod(Base):
    """A method somebody has put in the library."""

    __tablename__ = "methods"
    __table_args__ = (UniqueConstraint("title", name="uq_methods_title"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    stage: Mapped[int] = mapped_column(Integer, index=True)
    notation: Mapped[str] = mapped_column(Text)
    classification: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    compositions: Mapped[list[StoredComposition]] = relationship(
        back_populates="method",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )

    def __repr__(self) -> str:
        return f"StoredMethod({self.title!r})"


class StoredComposition(Base):
    """A touch somebody has written down, against the method it is rung to."""

    __tablename__ = "compositions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    method_id: Mapped[int] = mapped_column(ForeignKey("methods.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    composer: Mapped[str | None] = mapped_column(String(80), nullable=True)
    calling: Mapped[str] = mapped_column(Text)
    length: Mapped[int] = mapped_column(Integer, index=True)
    is_true: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    method: Mapped[StoredMethod] = relationship(back_populates="compositions")

    def __repr__(self) -> str:
        return f"StoredComposition({self.title!r}, {self.length})"
