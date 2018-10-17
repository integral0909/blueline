from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from blueline.db.models import (
    Base,
    StoredCompetition,
    StoredComposition,
    StoredEntry,
    StoredMethod,
    StoredPerformance,
    now,
)
from blueline.db.session import session_scope


def a_method(**over) -> StoredMethod:
    fields = {
        "title": "Cambridge Surprise Major",
        "name": "Cambridge",
        "stage": 8,
        "notation": "x38x14x1258x36x14x58x16x78,12",
        "classification": "Surprise",
    }
    fields.update(over)
    return StoredMethod(**fields)


class TestClock:
    def test_it_gives_an_aware_time(self):
        assert now().tzinfo is not None

    def test_it_is_in_utc(self):
        assert now().utcoffset().total_seconds() == 0


class TestStoringMethods:
    def test_a_method_can_be_stored_and_read_back(self, factory):
        with session_scope(factory) as session:
            session.add(a_method())
        with session_scope(factory) as session:
            found = session.scalars(select(StoredMethod)).one()
            assert found.title == "Cambridge Surprise Major"
            assert found.stage == 8

    def test_it_gets_an_id(self, factory):
        with session_scope(factory) as session:
            stored = a_method()
            session.add(stored)
        assert stored.id is not None

    def test_it_is_stamped_on_the_way_in(self, factory):
        with session_scope(factory) as session:
            stored = a_method()
            session.add(stored)
        assert stored.created_at is not None
        assert stored.updated_at is not None

    def test_two_methods_cannot_share_a_title(self, factory):
        with session_scope(factory) as session:
            session.add(a_method())
        with pytest.raises(IntegrityError), session_scope(factory) as session:
            session.add(a_method())

    def test_the_same_name_at_another_stage_is_fine(self, factory):
        with session_scope(factory) as session:
            session.add(a_method())
            session.add(a_method(title="Cambridge Surprise Minor", stage=6))
        with session_scope(factory) as session:
            assert len(session.scalars(select(StoredMethod)).all()) == 2

    def test_a_classification_may_be_left_off(self, factory):
        with session_scope(factory) as session:
            session.add(a_method(title="Grandsire Triples", classification=None))
        with session_scope(factory) as session:
            found = session.scalars(select(StoredMethod)).one()
            assert found.classification is None

    def test_it_reads_back_as_its_title(self):
        assert repr(a_method()) == "StoredMethod('Cambridge Surprise Major')"


class TestStoringCompositions:
    def test_a_composition_hangs_off_its_method(self, factory):
        with session_scope(factory) as session:
            method = a_method()
            method.compositions.append(
                StoredComposition(title="1250", composer="F Ahman", calling="-p-", length=1250)
            )
            session.add(method)
        with session_scope(factory) as session:
            found = session.scalars(select(StoredMethod)).one()
            assert len(found.compositions) == 1
            assert found.compositions[0].method.title == found.title

    def test_deleting_the_method_takes_its_compositions_with_it(self, factory):
        with session_scope(factory) as session:
            method = a_method()
            method.compositions.append(StoredComposition(title="x", calling="-", length=224))
            session.add(method)
        with session_scope(factory) as session:
            session.delete(session.scalars(select(StoredMethod)).one())
        with session_scope(factory) as session:
            assert session.scalars(select(StoredComposition)).all() == []

    def test_a_composition_defaults_to_unproven(self, factory):
        with session_scope(factory) as session:
            method = a_method()
            method.compositions.append(StoredComposition(title="x", calling="-", length=224))
            session.add(method)
        with session_scope(factory) as session:
            assert session.scalars(select(StoredComposition)).one().is_true is False

    def test_it_reads_back_as_its_title_and_length(self):
        composition = StoredComposition(title="5040", calling="-", length=5040)
        assert repr(composition) == "StoredComposition('5040', 5040)"


class TestSessionScope:
    def test_it_commits_on_the_way_out(self, factory):
        with session_scope(factory) as session:
            session.add(a_method())
        with session_scope(factory) as session:
            assert session.scalars(select(StoredMethod)).all() != []

    def test_it_rolls_back_when_something_throws(self, factory):
        with pytest.raises(RuntimeError), session_scope(factory) as session:
            session.add(a_method())
            raise RuntimeError("changed my mind")
        with session_scope(factory) as session:
            assert session.scalars(select(StoredMethod)).all() == []


class TestSchema:
    def test_there_are_tables(self):
        # Deliberately not a fixed list. Every new table used to mean editing
        # this line, which is a test that only ever says the list was edited.
        # What matters is that the migrations agree, and test_migrations
        # checks that against the metadata.
        assert Base.metadata.tables

    def test_every_table_has_a_primary_key(self):
        for name, table in Base.metadata.tables.items():
            assert table.primary_key.columns, f"{name} has no primary key"

    def test_every_table_records_when_its_rows_were_made(self):
        # Rows owned by a parent are excused. An entry in a competition is
        # made when the competition is, cannot outlive it, and a second
        # timestamp saying the same thing is one more thing to keep honest.
        for name, table in Base.metadata.tables.items():
            if any(column.foreign_keys for column in table.c if column.name.endswith("_id")):
                continue
            assert "created_at" in table.c, f"{name} does not say when"

    def test_an_owned_row_goes_when_its_owner_does(self):
        entries = Base.metadata.tables["entries"]
        key = next(iter(entries.c.competition_id.foreign_keys))
        assert key.ondelete == "CASCADE"

    def test_the_title_is_indexed_because_everything_looks_up_by_it(self):
        assert Base.metadata.tables["methods"].c.title.index


class TestStoringPerformances:
    def a_performance(self, **over) -> StoredPerformance:
        fields = {
            "title": "Cambridge Surprise Major",
            "stage": 8,
            "length": 5024,
            "rang_on": date(2023, 3, 18),
            "place": "St Andrew, Marchgate",
            "composer": "F Ahman",
            "ringers": "\n".join(["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]),
            "conductor": 8,
        }
        fields.update(over)
        return StoredPerformance(**fields)

    def test_one_can_be_stored_without_a_method(self, factory):
        with session_scope(factory) as session:
            session.add(self.a_performance())
        with session_scope(factory) as session:
            found = session.scalars(select(StoredPerformance)).one()
            assert found.method_id is None
            assert found.length == 5024

    def test_it_can_hang_off_a_method(self, factory):
        with session_scope(factory) as session:
            method = a_method()
            session.add(method)
            session.flush()
            session.add(self.a_performance(method_id=method.id))
        with session_scope(factory) as session:
            found = session.scalars(select(StoredPerformance)).one()
            assert found.method.title == "Cambridge Surprise Major"

    def test_deleting_the_method_leaves_the_performance_behind(self, factory):
        # Somebody rang that peal whether or not the library still holds the
        # method, so the link goes null rather than the row going away.
        with session_scope(factory) as session:
            method = a_method()
            session.add(method)
            session.flush()
            session.add(self.a_performance(method_id=method.id))
        with session_scope(factory) as session:
            session.delete(session.scalars(select(StoredMethod)).one())
        with session_scope(factory) as session:
            found = session.scalars(select(StoredPerformance)).one()
            assert found.method_id is None

    def test_the_band_is_stored_as_lines(self, factory):
        with session_scope(factory) as session:
            session.add(self.a_performance())
        with session_scope(factory) as session:
            found = session.scalars(select(StoredPerformance)).one()
            assert found.ringers.splitlines() == [
                "Ann",
                "Bob",
                "Cara",
                "Dan",
                "Eve",
                "Finn",
                "Gus",
                "Hana",
            ]

    def test_the_date_survives(self, factory):
        with session_scope(factory) as session:
            session.add(self.a_performance())
        with session_scope(factory) as session:
            assert session.scalars(select(StoredPerformance)).one().rang_on == date(2023, 3, 18)

    def test_it_reads_back_as_its_length_and_title(self):
        assert repr(self.a_performance()) == ("StoredPerformance(5024 'Cambridge Surprise Major')")


class TestStoringCompetitions:
    def a_competition(self, **over) -> StoredCompetition:
        fields = {
            "name": "Marchgate District Striking",
            "held_on": date(2023, 5, 6),
            "place": "St Andrew, Marchgate",
            "stage": 6,
            "judge": "F Ahman",
        }
        fields.update(over)
        return StoredCompetition(**fields)

    def an_entry(self, **over) -> StoredEntry:
        fields = {
            "band": "St Mary",
            "position": 1,
            "faults": 14,
            "percentage": 97.5,
            "drift": "even",
        }
        fields.update(over)
        return StoredEntry(**fields)

    def test_one_can_be_stored(self, session):
        session.add(self.a_competition())
        session.commit()
        assert session.query(StoredCompetition).count() == 1

    def test_it_holds_its_entries(self, session):
        competition = self.a_competition()
        competition.entries.append(self.an_entry())
        competition.entries.append(self.an_entry(band="All Saints", position=2))
        session.add(competition)
        session.commit()
        assert len(session.query(StoredCompetition).one().entries) == 2

    def test_entries_come_back_in_the_order_announced(self, session):
        competition = self.a_competition()
        competition.entries.append(self.an_entry(band="All Saints", position=2))
        competition.entries.append(self.an_entry(band="St Mary", position=1))
        session.add(competition)
        session.commit()
        # Expired first. Until it reloads, the collection is still in the
        # order it was appended in, which would let this pass without the
        # order_by doing anything.
        session.expire_all()
        bands = [entry.band for entry in session.query(StoredCompetition).one().entries]
        assert bands == ["St Mary", "All Saints"]

    def test_two_bands_can_be_placed_equal(self, session):
        competition = self.a_competition()
        competition.entries.append(self.an_entry(band="St Mary", position=1))
        competition.entries.append(self.an_entry(band="All Saints", position=1))
        session.add(competition)
        session.commit()
        assert len(session.query(StoredEntry).all()) == 2

    def test_the_same_band_cannot_enter_twice(self, session):
        competition = self.a_competition()
        competition.entries.append(self.an_entry())
        competition.entries.append(self.an_entry(position=2))
        session.add(competition)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_the_same_competition_can_run_again_next_year(self, session):
        session.add(self.a_competition())
        session.add(self.a_competition(held_on=date(2024, 5, 4)))
        session.commit()
        assert session.query(StoredCompetition).count() == 2

    def test_it_cannot_run_twice_on_one_day(self, session):
        session.add(self.a_competition())
        session.add(self.a_competition(place="somewhere else"))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_deleting_a_competition_takes_its_entries(self, session):
        competition = self.a_competition()
        competition.entries.append(self.an_entry())
        session.add(competition)
        session.commit()
        session.delete(competition)
        session.commit()
        assert session.query(StoredEntry).count() == 0

    def test_it_reads_back_as_itself(self, session):
        session.add(self.a_competition())
        session.commit()
        stored = session.query(StoredCompetition).one()
        assert "Marchgate" in repr(stored)
