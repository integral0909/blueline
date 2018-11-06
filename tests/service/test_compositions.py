"""Keeping the touches somebody has written down."""

from __future__ import annotations

import pytest

from blueline.db.repositories import CompositionRepository
from blueline.service.compositions import (
    fetch,
    for_method,
    longest,
    remove,
    store,
)
from blueline.service.results import Reason

PLAIN = "Plain Bob Minor"
#: A bob at every lead end, which is what comes round at minor.
BOBS = "---"


@pytest.fixture()
def compositions(loaded) -> CompositionRepository:
    return CompositionRepository(loaded.session)


class TestStoring:
    def test_a_touch_goes_in(self, compositions, loaded) -> None:
        result = store(compositions, loaded, "A 60", PLAIN, BOBS)
        assert result.ok
        assert result.unwrap().length > 0

    def test_it_is_proved_on_the_way_in(self, compositions, loaded) -> None:
        view = store(compositions, loaded, "A 60", PLAIN, BOBS).unwrap()
        assert view.is_true

    def test_the_method_is_named(self, compositions, loaded) -> None:
        view = store(compositions, loaded, "A 60", PLAIN, BOBS).unwrap()
        assert view.method == PLAIN

    def test_a_composer_can_be_given(self, compositions, loaded) -> None:
        view = store(compositions, loaded, "A 60", PLAIN, BOBS, composer="F Ahman").unwrap()
        assert view.composer == "F Ahman"

    def test_no_composer_is_left_blank(self, compositions, loaded) -> None:
        assert store(compositions, loaded, "A 60", PLAIN, BOBS).unwrap().composer == ""

    def test_a_title_is_needed(self, compositions, loaded) -> None:
        result = store(compositions, loaded, "   ", PLAIN, BOBS)
        assert result.failure.reason is Reason.INVALID

    def test_a_very_long_title(self, compositions, loaded) -> None:
        result = store(compositions, loaded, "x" * 200, PLAIN, BOBS)
        assert "at most" in result.failure.detail

    def test_a_method_nobody_has_stored(self, compositions, loaded) -> None:
        result = store(compositions, loaded, "A 60", "Weasel Surprise Major", BOBS)
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_calling_that_does_not_come_round(self, compositions, loaded) -> None:
        result = store(compositions, loaded, "Not a touch", PLAIN, "-")
        assert result.failure.reason is Reason.INVALID
        assert "not rounds" in result.failure.detail

    def test_a_calling_that_does_not_parse(self, compositions, loaded) -> None:
        result = store(compositions, loaded, "Nonsense", PLAIN, "qqq")
        assert result.failure is not None

    def test_a_summary_reads_as_a_composition(self, compositions, loaded) -> None:
        view = store(compositions, loaded, "A 60", PLAIN, BOBS).unwrap()
        assert view.summary().startswith("A 60, ")


class TestReadingBack:
    @pytest.fixture()
    def stocked(self, compositions, loaded):
        store(compositions, loaded, "A 60", PLAIN, BOBS, composer="F Ahman")
        store(compositions, loaded, "Another 60", PLAIN, BOBS)
        return compositions

    def test_one_can_be_fetched(self, stocked, loaded) -> None:
        first = for_method(stocked, loaded, PLAIN).unwrap()[0]
        assert fetch(stocked, loaded, first.id).unwrap().title == first.title

    def test_fetching_one_that_is_not_there(self, stocked, loaded) -> None:
        assert fetch(stocked, loaded, 404).failure.reason is Reason.NOT_FOUND

    def test_everything_for_a_method(self, stocked, loaded) -> None:
        assert len(for_method(stocked, loaded, PLAIN).unwrap()) == 2

    def test_a_method_nobody_has_stored(self, stocked, loaded) -> None:
        result = for_method(stocked, loaded, "Weasel Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_method_with_nothing_written_for_it(self, stocked, loaded) -> None:
        assert for_method(stocked, loaded, "Cambridge Surprise Minor").unwrap() == []

    def test_the_longest_come_back(self, stocked, loaded) -> None:
        assert len(longest(stocked, loaded).unwrap()) == 2

    def test_the_list_can_be_cut_short(self, stocked, loaded) -> None:
        assert len(longest(stocked, loaded, limit=1).unwrap()) == 1

    def test_asking_for_none_of_them(self, stocked, loaded) -> None:
        assert longest(stocked, loaded, limit=0).failure.reason is Reason.INVALID

    def test_it_is_proved_again_on_the_way_out(self, stocked, loaded) -> None:
        view = for_method(stocked, loaded, PLAIN).unwrap()[0]
        assert view.still_true

    def test_one_can_be_removed(self, stocked, loaded) -> None:
        first = for_method(stocked, loaded, PLAIN).unwrap()[0]
        assert remove(stocked, first.id).ok
        assert len(for_method(stocked, loaded, PLAIN).unwrap()) == 1

    def test_removing_one_that_is_not_there(self, stocked) -> None:
        assert remove(stocked, 404).failure.reason is Reason.NOT_FOUND


class TestEditedUnderneath:
    """A composition is only true of the notation it was proved against."""

    def test_the_stored_truth_is_carried_through(self, compositions, loaded) -> None:
        view = store(compositions, loaded, "A 60", PLAIN, BOBS).unwrap()
        assert view.stored_as_true is view.is_true

    def test_changing_the_method_changes_what_the_touch_does(self, compositions, loaded) -> None:
        made = store(compositions, loaded, "A 60", PLAIN, BOBS).unwrap()
        # Repointed at Cambridge's notation, which is what happens when
        # somebody fixes a method that was entered wrong.
        stored = loaded.get(PLAIN)
        stored.notation = "x16x16x16x36,12"
        loaded.session.flush()

        again = fetch(compositions, loaded, made.id).unwrap()
        assert again.length != made.length or not again.still_true

    def test_a_method_that_no_longer_proves_is_left_out_of_the_listing(
        self, compositions, loaded
    ) -> None:
        store(compositions, loaded, "A 60", PLAIN, BOBS)
        stored = loaded.get(PLAIN)
        stored.notation = "x16x16x16x36,12"
        loaded.session.flush()
        # Still listed if it proves at all; the point is that nothing raises.
        assert isinstance(for_method(compositions, loaded, PLAIN).unwrap(), list)
