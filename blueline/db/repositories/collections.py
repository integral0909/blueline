"""Named sets of methods."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func

from blueline.core.collections import Collection
from blueline.core.titles import as_lines, from_lines
from blueline.db.base import Repository
from blueline.db.models import StoredCollection
from blueline.errors import LibraryError


def to_stored_collection(collection: Collection) -> StoredCollection:
    return StoredCollection(
        name=collection.name.strip(),
        titles=as_lines(collection.titles),
        note=collection.note.strip(),
    )


def to_collection(stored: StoredCollection) -> Collection:
    return Collection(
        name=stored.name,
        titles=from_lines(stored.titles),
        note=stored.note,
    )


class CollectionRepository(Repository[StoredCollection]):
    """Collections in the database."""

    model = StoredCollection

    def add(self, collection: Collection) -> StoredCollection:
        if self.find(collection.name) is not None:
            raise LibraryError(f"{collection.name} is already stored")
        return self.add_row(to_stored_collection(collection))

    def find(self, name: str) -> Optional[StoredCollection]:
        statement = self.session.query(StoredCollection).filter(
            func.lower(StoredCollection.name) == name.strip().lower()
        )
        return statement.one_or_none()

    def get(self, name: str) -> StoredCollection:
        found = self.find(name)
        if found is None:
            raise LibraryError(f"no collection called {name!r} is stored")
        return found

    def save(self, collection: Collection) -> StoredCollection:
        """Store one, replacing what was there under that name."""
        existing = self.find(collection.name)
        if existing is None:
            return self.add(collection)
        existing.titles = as_lines(collection.titles)
        existing.note = collection.note.strip()
        self.session.flush()
        return existing

    def remove(self, name: str) -> None:
        self.delete_row(self.get(name))

    def all(self) -> List[StoredCollection]:
        statement = self.session.query(StoredCollection).order_by(StoredCollection.name)
        return list(statement.all())

    def sets(self) -> List[Collection]:
        """Everything stored, as the core's type."""
        return [to_collection(stored) for stored in self.all()]

    def holding(self, title: str) -> List[StoredCollection]:
        """Collections with this title among their methods.

        Matched on the stored text, so this finds Cambridge Surprise Major and
        would also find it inside a longer title. The service checks properly;
        this narrows the query.
        """
        statement = (
            self.session.query(StoredCollection)
            .filter(StoredCollection.titles.ilike(f"%{title.strip()}%"))
            .order_by(StoredCollection.name)
        )
        return list(statement.all())
