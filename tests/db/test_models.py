from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from blueline.db.models import (
    Base,
    StoredComposition,
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
        for name, table in Base.metadata.tables.items():
            assert "created_at" in table.c, f"{name} does not say when"

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
