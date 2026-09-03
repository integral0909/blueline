"""Methods and the compositions written for them."""

from __future__ import annotations

from sqlalchemy import Select, func, select

from blueline.analysis import analyse
from blueline.core.method import Method
from blueline.db.base import Repository
from blueline.db.models import StoredComposition, StoredMethod
from blueline.errors import LibraryError


def to_stored(method: Method, name: str | None = None) -> StoredMethod:
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

    def add(self, method: Method, name: str | None = None) -> StoredMethod:
        stored = to_stored(method, name=name)
        if self.find(stored.title) is not None:
            raise LibraryError(f"{stored.title} is already stored")
        return self.add_row(stored)

    def find(self, title: str) -> StoredMethod | None:
        statement = select(StoredMethod).where(
            func.lower(StoredMethod.title) == title.strip().lower()
        )
        return self.session.scalars(statement).one_or_none()

    def get(self, title: str) -> StoredMethod:
        found = self.find(title)
        if found is None:
            raise LibraryError(f"no method called {title!r} is stored")
        return found

    def remove(self, title: str) -> None:
        self.delete_row(self.get(title))

    def _search(
        self,
        name: str | None = None,
        stage: int | None = None,
        classification: str | None = None,
    ) -> Select[tuple[StoredMethod]]:
        statement = select(StoredMethod)
        if name is not None:
            statement = statement.where(StoredMethod.name.ilike(f"%{name.strip()}%"))
        if stage is not None:
            statement = statement.where(StoredMethod.stage == stage)
        if classification is not None:
            statement = statement.where(
                func.lower(StoredMethod.classification) == classification.strip().lower()
            )
        return statement.order_by(StoredMethod.stage, StoredMethod.title)

    def search(
        self,
        name: str | None = None,
        stage: int | None = None,
        classification: str | None = None,
    ) -> list[StoredMethod]:
        return list(self.session.scalars(self._search(name, stage, classification)).all())

    def all(self) -> list[StoredMethod]:
        return self.search()

    def stages(self) -> list[int]:
        statement = select(StoredMethod.stage).distinct().order_by(StoredMethod.stage)
        return list(self.session.scalars(statement).all())


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
        composer: str | None = None,
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

    def for_method(self, method: StoredMethod) -> list[StoredComposition]:
        statement = (
            select(StoredComposition)
            .where(StoredComposition.method_id == method.id)
            .order_by(StoredComposition.length.desc(), StoredComposition.title)
        )
        return list(self.session.scalars(statement).all())

    def longest(self, limit: int = 10) -> list[StoredComposition]:
        statement = select(StoredComposition).order_by(StoredComposition.length.desc()).limit(limit)
        return list(self.session.scalars(statement).all())
