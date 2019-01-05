"""Everything about one method, in one answer."""

from __future__ import annotations

import pytest

from blueline.core.collections import Collection
from blueline.db.repositories import CollectionRepository, CompositionRepository
from blueline.service.compositions import store
from blueline.service.dossier import compile_dossier
from blueline.service.results import Reason

CAMBRIDGE = "Cambridge Surprise Minor"


@pytest.fixture()
def compositions(loaded) -> CompositionRepository:
    return CompositionRepository(loaded.session)


@pytest.fixture()
def collections(loaded) -> CollectionRepository:
    return CollectionRepository(loaded.session)


def make(loaded, compositions, collections, title=CAMBRIDGE, **over):
    return compile_dossier(loaded, compositions, collections, title, **over)


class TestCompiling:
    def test_it_answers(self, loaded, compositions, collections) -> None:
        assert make(loaded, compositions, collections).ok

    def test_it_carries_the_analysis(self, loaded, compositions, collections) -> None:
        found = make(loaded, compositions, collections).unwrap()
        assert found.report.lead_length == 24

    def test_it_carries_a_line(self, loaded, compositions, collections) -> None:
        found = make(loaded, compositions, collections).unwrap()
        assert found.line.grid

    def test_the_bell_can_be_chosen(self, loaded, compositions, collections) -> None:
        found = make(loaded, compositions, collections, bell=3).unwrap()
        assert found.line.bell == 3

    def test_it_carries_the_place_bells(self, loaded, compositions, collections) -> None:
        assert make(loaded, compositions, collections).unwrap().place_bells

    def test_it_carries_the_falseness(self, loaded, compositions, collections) -> None:
        assert make(loaded, compositions, collections).unwrap().falseness is not None

    def test_the_falseness_is_capped(self, loaded, compositions, collections) -> None:
        found = make(loaded, compositions, collections, most_falseness=2).unwrap()
        assert len(found.falseness) <= 2

    def test_it_carries_the_handbell_pairs(self, loaded, compositions, collections) -> None:
        assert make(loaded, compositions, collections).unwrap().handbells

    def test_it_carries_the_calling_positions(self, loaded, compositions, collections) -> None:
        assert make(loaded, compositions, collections).unwrap().positions

    def test_it_carries_how_hard_it_is(self, loaded, compositions, collections) -> None:
        found = make(loaded, compositions, collections).unwrap()
        assert found.difficulty.band

    def test_a_summary_reads_as_a_method(self, loaded, compositions, collections) -> None:
        assert CAMBRIDGE in make(loaded, compositions, collections).unwrap().summary()

    def test_the_title_is_the_stored_one(self, loaded, compositions, collections) -> None:
        found = make(loaded, compositions, collections, title="cambridge surprise minor")
        assert found.unwrap().title == CAMBRIDGE


class TestWhatIsWrittenForIt:
    def test_nothing_written_yet(self, loaded, compositions, collections) -> None:
        assert make(loaded, compositions, collections).unwrap().compositions == ()

    def test_a_stored_composition_shows_up(self, loaded, compositions, collections) -> None:
        store(compositions, loaded, "A 60", "Plain Bob Minor", "---")
        found = make(loaded, compositions, collections, title="Plain Bob Minor").unwrap()
        assert len(found.compositions) == 1

    def test_a_set_it_is_in_shows_up(self, loaded, compositions, collections) -> None:
        collections.add(Collection(name="Tuesday", titles=frozenset({CAMBRIDGE})))
        assert make(loaded, compositions, collections).unwrap().in_sets == ("Tuesday",)

    def test_a_set_it_is_not_in_does_not(self, loaded, compositions, collections) -> None:
        collections.add(Collection(name="Tuesday", titles=frozenset({"Plain Bob Minor"})))
        assert make(loaded, compositions, collections).unwrap().in_sets == ()


class TestRefusing:
    def test_a_method_nobody_has_stored(self, loaded, compositions, collections) -> None:
        result = make(loaded, compositions, collections, title="Weasel Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_bell_that_is_not_ringing(self, loaded, compositions, collections) -> None:
        result = make(loaded, compositions, collections, bell=9)
        assert result.failure.reason is Reason.INVALID

    def test_no_falseness_at_all(self, loaded, compositions, collections) -> None:
        result = make(loaded, compositions, collections, most_falseness=0)
        assert result.failure.reason is Reason.INVALID


class TestAgreesWithTheParts:
    """Two ways of working the same thing out would eventually disagree."""

    def test_the_line_matches_the_line_endpoint(self, loaded, compositions, collections) -> None:
        from blueline.service.analysing import line

        found = make(loaded, compositions, collections).unwrap()
        assert found.line == line(loaded, CAMBRIDGE, 2).unwrap()

    def test_the_falseness_matches(self, loaded, compositions, collections) -> None:
        from blueline.service.analysing import falseness

        found = make(loaded, compositions, collections).unwrap()
        assert list(found.falseness) == falseness(loaded, CAMBRIDGE, limit=12).unwrap()

    def test_the_positions_match(self, loaded, compositions, collections) -> None:
        from blueline.service.calls import positions

        found = make(loaded, compositions, collections).unwrap()
        assert list(found.positions) == positions(loaded, CAMBRIDGE).unwrap()
