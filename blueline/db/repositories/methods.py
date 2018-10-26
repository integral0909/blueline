"""Methods and the compositions written for them."""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import func

from blueline.analysis import analyse
from blueline.core.method import Method
from sqlalchemy.orm import Query

from blueline.db.base import Repository
from blueline.db.models import StoredComposition, StoredMethod
from blueline.errors import LibraryError


def to_stored(method: Method, name: Optional[str] = None) -> StoredMethod:
    """Work out everything a method needs to be stored under."""
    report = analyse(method, name=name)
    return StoredMethod(
        title=str(report.title),
        name=report.title.name,
        stage=report.stage,
        notation=report.notation,
        classification=report.classification.kind,
    )


def to_method(stored: StoredMethod) -> Method:
    """Rebuild the method from what was stored, which is the notation."""
    return Method.from_notation(stored.name, stored.stage, stored.notation)


class MethodRepository(Repository[StoredMethod]):
    """Methods in the database."""

    model = StoredMethod

    def add(self, method: Method, name: Optional[str] = None) -> StoredMethod:
        stored = to_stored(method, name=name)
        if self.find(stored.title) is not None:
            raise LibraryError(f"{stored.title} is already stored")
        return self.add_row(stored)

    def find(self, title: str) -> Optional[StoredMethod]:
        statement = self.session.query(StoredMethod).filter(
            func.lower(StoredMethod.title) == title.strip().lower()
        )
        return statement.one_or_none()

    def get(self, title: str) -> StoredMethod:
        found = self.find(title)
        if found is None:
            raise LibraryError(f"no method called {title!r} is stored")
        return found

    def remove(self, title: str) -> None:
        self.delete_row(self.get(title))

    def _search(
        self,
        name: Optional[str] = None,
        stage: Optional[int] = None,
        classification: Optional[str] = None,
    ) -> "Query[StoredMethod]":
        statement = self.session.query(StoredMethod)
        if name is not None:
            statement = statement.filter(StoredMethod.name.ilike(f"%{name.strip()}%"))
        if stage is not None:
            statement = statement.filter(StoredMethod.stage == stage)
        if classification is not None:
            statement = statement.filter(
                func.lower(StoredMethod.classification) == classification.strip().lower()
            )
        return statement.order_by(StoredMethod.stage, StoredMethod.title)

    def search(
        self,
        name: Optional[str] = None,
        stage: Optional[int] = None,
        classification: Optional[str] = None,
    ) -> List[StoredMethod]:
        return list(self._search(name, stage, classification).all())

    def all(self) -> List[StoredMethod]:
        return self.search()

    def stages(self) -> List[int]:
        statement = self.session.query(StoredMethod.stage).distinct().order_by(StoredMethod.stage)
        return list(statement.all())


class CompositionRepository(Repository[StoredComposition]):
    """Compositions in the database, always against a stored method."""

    model = StoredComposition

    def add(
        self,
        method: StoredMethod,
        title: str,
        calling: str,
        length: int,
        is_true: bool,
        composer: Optional[str] = None,
    ) -> StoredComposition:
        composition = StoredComposition(
            method=method,
            title=title.strip(),
            calling=calling.strip(),
            length=length,
            is_true=is_true,
            composer=composer,
        )
        return self.add_row(composition)

    def for_method(self, method: StoredMethod) -> List[StoredComposition]:
        statement = (
            self.session.query(StoredComposition)
            .filter(StoredComposition.method_id == method.id)
            .order_by(StoredComposition.length.desc(), StoredComposition.title)
        )
        return list(statement.all())

    def longest(self, limit: int = 10) -> List[StoredComposition]:
        statement = self.session.query(StoredComposition).order_by(StoredComposition.length.desc()).limit(limit)
        return list(statement.all())
