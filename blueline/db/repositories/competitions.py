"""Striking competition sheets."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from blueline.core.competitions import Competition, Entry
from blueline.db.base import Repository
from blueline.db.models import StoredCompetition, StoredEntry
from blueline.errors import LibraryError


def to_stored_competition(competition: Competition) -> StoredCompetition:
    """A sheet, ready to go in."""
    return StoredCompetition(
        name=competition.name.strip(),
        held_on=competition.held_on,
        place=competition.place.strip(),
        stage=competition.stage,
        judge=competition.judge.strip(),
        entries=[
            StoredEntry(
                band=entry.band.strip(),
                position=entry.position,
                faults=entry.faults,
                percentage=entry.percentage,
                drift=entry.drift,
                note=entry.note,
            )
            for entry in competition.ordered()
        ],
    )


def to_competition(stored: StoredCompetition) -> Competition:
    """A sheet, as the core's type."""
    return Competition(
        name=stored.name,
        held_on=stored.held_on,
        stage=stored.stage,
        place=stored.place,
        judge=stored.judge,
        entries=tuple(
            Entry(
                band=entry.band,
                position=entry.position,
                faults=entry.faults,
                percentage=entry.percentage,
                drift=entry.drift,
                note=entry.note,
            )
            for entry in stored.entries
        ),
    )


class CompetitionRepository(Repository[StoredCompetition]):
    """Competition sheets in the database."""

    model = StoredCompetition

    def add(self, competition: Competition) -> StoredCompetition:
        if self.find(competition.name, competition.held_on) is not None:
            raise LibraryError(
                f"{competition.name} on {competition.held_on:%Y-%m-%d} is already stored"
            )
        return self.add_row(to_stored_competition(competition))

    def find(self, name: str, held_on: date) -> StoredCompetition | None:
        statement = select(StoredCompetition).where(
            func.lower(StoredCompetition.name) == name.strip().lower(),
            StoredCompetition.held_on == held_on,
        )
        return self.session.scalars(statement).one_or_none()

    def get(self, competition_id: int) -> StoredCompetition:
        found = self.get_by_id(competition_id)
        if found is None:
            raise LibraryError(f"no competition number {competition_id}")
        return found

    def remove(self, competition_id: int) -> None:
        self.delete_row(self.get(competition_id))

    def search(
        self,
        name: str | None = None,
        place: str | None = None,
        band: str | None = None,
        stage: int | None = None,
    ) -> list[StoredCompetition]:
        """Sheets matching everything asked for, most recent first."""
        statement = select(StoredCompetition)
        if name is not None:
            statement = statement.where(StoredCompetition.name.ilike(f"%{name.strip()}%"))
        if place is not None:
            statement = statement.where(StoredCompetition.place.ilike(f"%{place.strip()}%"))
        if stage is not None:
            statement = statement.where(StoredCompetition.stage == stage)
        if band is not None:
            # Joined rather than filtered afterwards. A district with twenty
            # years of sheets is a lot of rows to load in order to throw most
            # of them away.
            statement = statement.join(StoredEntry).where(
                StoredEntry.band.ilike(f"%{band.strip()}%")
            )
        statement = statement.order_by(StoredCompetition.held_on.desc(), StoredCompetition.name)
        return list(self.session.scalars(statement).unique().all())

    def all(self) -> list[StoredCompetition]:
        return self.search()

    def sheets(self) -> list[Competition]:
        """Everything stored, as the core's type."""
        return [to_competition(stored) for stored in self.all()]

    def for_band(self, band: str) -> list[Competition]:
        """Every sheet a band appears on, as the core's type."""
        return [to_competition(stored) for stored in self.search(band=band)]
