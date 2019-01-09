"""Whether the indexes are actually used.

An index nothing chooses is a write cost with no read to pay for it. Sqlite
will tell you what it plans to do, so the plan is worth asserting on rather
than assuming.

These read the plan rather than timing anything. A timing test on a table with
fifteen rows in it measures nothing but the machine it ran on.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from blueline.db.models import (
    Base,
    StoredCompetition,
    StoredEntry,
    StoredMethod,
    StoredPerformance,
)


def plan(session, query) -> str:
    """What sqlite says it will do, as one string.

    A Query carries the select underneath it, and that is the thing that
    compiles: asking the Query itself gets the ORM wrapper instead.
    """
    compiled = query.statement.compile(session.bind, compile_kwargs={"literal_binds": True})
    rows = session.execute(text("EXPLAIN QUERY PLAN " + str(compiled))).fetchall()
    return " ".join(str(cell) for row in rows for cell in row)


class TestIndexesExist:
    def test_the_name_is_indexed(self) -> None:
        indexes = {index.name for index in Base.metadata.tables["methods"].indexes}
        assert "ix_methods_name" in indexes

    def test_the_classification_is_indexed(self) -> None:
        indexes = {index.name for index in Base.metadata.tables["methods"].indexes}
        assert "ix_methods_classification" in indexes

    def test_entries_are_indexed_by_competition_and_position(self) -> None:
        indexes = {index.name for index in Base.metadata.tables["entries"].indexes}
        assert "ix_entries_position" in indexes

    def test_the_entries_index_covers_both_columns(self) -> None:
        index = next(
            each
            for each in Base.metadata.tables["entries"].indexes
            if each.name == "ix_entries_position"
        )
        assert [column.name for column in index.columns] == ["competition_id", "position"]

    @pytest.mark.parametrize(
        "table",
        ["methods", "performances", "towers", "ringers", "competitions", "collections"],
    )
    def test_every_table_a_listing_reads_has_an_index(self, table) -> None:
        assert Base.metadata.tables[table].indexes


class TestPlans:
    def test_finding_a_method_by_stage_uses_an_index(self, session) -> None:
        statement = session.query(StoredMethod).filter(StoredMethod.stage == 8)
        assert "USING INDEX" in plan(session, statement).upper()

    def test_narrowing_by_classification_uses_one(self, session) -> None:
        statement = session.query(StoredMethod).filter(StoredMethod.classification == "Surprise")
        assert "USING INDEX" in plan(session, statement).upper()

    def test_a_performance_by_place_uses_one(self, session) -> None:
        statement = session.query(StoredPerformance).filter(StoredPerformance.place == "St Andrew")
        assert "USING INDEX" in plan(session, statement).upper()

    def test_ordering_performances_by_date_uses_one(self, session) -> None:
        statement = session.query(StoredPerformance).order_by(StoredPerformance.rang_on.desc())
        assert "USING INDEX" in plan(session, statement).upper()

    def test_a_competitions_entries_use_the_pair(self, session) -> None:
        statement = (
            session.query(StoredEntry)
            .filter(StoredEntry.competition_id == 1)
            .order_by(StoredEntry.position)
        )
        assert "IX_ENTRIES_POSITION" in plan(session, statement).upper()

    def test_a_competition_by_name_and_date_uses_one(self, session) -> None:
        statement = session.query(StoredCompetition).filter(StoredCompetition.name == "District")
        assert "USING INDEX" in plan(session, statement).upper()

    def test_a_search_that_cannot_use_one_still_answers(self, session) -> None:
        # A leading wildcard cannot use an index and is not expected to. The
        # point of saying so here is that nobody later adds an index hoping it
        # will and quietly pays for it.
        statement = session.query(StoredMethod).filter(StoredMethod.notation.like("%16%"))
        assert "SCAN" in plan(session, statement).upper()
