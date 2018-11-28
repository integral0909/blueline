"""Methods, and the compositions written for them."""

from __future__ import annotations

from typing import List, Optional

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from blueline.db.models.base import Base, now


class StoredMethod(Base):
    """A method somebody has put in the library."""

    __tablename__ = "methods"
    __table_args__ = (UniqueConstraint("title", name="uq_methods_title"),)

    id = Column(Integer, primary_key=True)
    title = Column(String(120), index=True, nullable=False)
    name = Column(String(80), index=True, nullable=False)
    stage = Column(Integer, index=True, nullable=False)
    notation = Column(Text, nullable=False)
    classification = Column(String(40), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    compositions = relationship("StoredComposition", back_populates="method",
        cascade="all, delete-orphan",
        passive_deletes=False,)

    def __repr__(self) -> str:
        return f"StoredMethod({self.title!r})"


class StoredComposition(Base):
    """A touch somebody has written down, against the method it is rung to."""

    __tablename__ = "compositions"

    id = Column(Integer, primary_key=True)
    method_id = Column(ForeignKey("methods.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(120), nullable=False)
    composer = Column(String(80), nullable=True)
    calling = Column(Text, nullable=False)
    length = Column(Integer, index=True, nullable=False)
    is_true = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

    method = relationship("StoredMethod", back_populates="compositions")

    def __repr__(self) -> str:
        return f"StoredComposition({self.title!r}, {self.length})"
