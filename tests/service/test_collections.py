"""What a band can do with a named set of methods."""

from __future__ import annotations

import pytest

from blueline.core.ringers import Ringer
from blueline.db.repositories import CollectionRepository
from blueline.service.collections import (
    add_to,
    coverage,
    fetch,
    forget,
    keep,
    listing,
    take_out,
)
from blueline.service.results import Reason

MINOR = ["Plain Bob Minor", "Cambridge Surprise Minor"]


@pytest.fixture()
def collections(loaded) -> CollectionRepository:
    return CollectionRepository(loaded.session)


@pytest.fixture()
def band(ringers):
    ringers.add(Ringer(name="Ann", can_ring=frozenset({"Plain Bob Minor"}), learning=frozenset()))
    ringers.add(
        Ringer(
            name="Bob",
            can_ring=frozenset({"Plain Bob Minor", "Cambridge Surprise Minor"}),
            learning=frozenset(),
        )
    )
    return ringers


class TestKeeping:
    def test_a_set_can_be_written_down(self, collections, loaded) -> None:
        view = keep(collections, loaded, "Tuesday", MINOR).unwrap()
        assert view.size == 2

    def test_it_says_what_the_library_holds(self, collections, loaded) -> None:
        view = keep(collections, loaded, "Tuesday", [*MINOR, "Weasel Surprise Major"]).unwrap()
        assert view.not_stored == ("Weasel Surprise Major",)

    def test_it_ranks_what_is_in_it(self, collections, loaded) -> None:
        view = keep(collections, loaded, "Tuesday", MINOR).unwrap()
        assert view.difficulties[0].title == "Plain Bob Minor"

    def test_it_names_the_hardest(self, collections, loaded) -> None:
        view = keep(collections, loaded, "Tuesday", MINOR).unwrap()
        assert view.hardest.title == "Cambridge Surprise Minor"

    def test_a_nameless_set_is_refused(self, collections, loaded) -> None:
        assert keep(collections, loaded, "  ", MINOR).failure.reason is Reason.INVALID

    def test_the_same_name_twice_is_a_conflict(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        result = keep(collections, loaded, "Tuesday", MINOR)
        assert result.failure.reason is Reason.ALREADY_EXISTS

    def test_a_note_can_be_given(self, collections, loaded) -> None:
        view = keep(collections, loaded, "Tuesday", MINOR, note="working on").unwrap()
        assert view.note == "working on"

    def test_a_summary_says_how_many_are_held(self, collections, loaded) -> None:
        view = keep(collections, loaded, "Tuesday", MINOR).unwrap()
        assert "2 in the library" in view.summary()


class TestSplicing:
    def test_methods_with_the_same_lead_heads_splice(self, collections, loaded) -> None:
        four = ["Cambridge Surprise Major", "Yorkshire Surprise Major"]
        view = keep(collections, loaded, "spliceable", four).unwrap()
        assert view.splices is True

    def test_methods_that_do_not_say_which_pair(self, collections, loaded) -> None:
        mixed = ["Cambridge Surprise Major", "Bristol Surprise Major"]
        view = keep(collections, loaded, "mixed", mixed).unwrap()
        assert view.splices is False
        assert "lead heads" in view.why_not

    def test_one_method_says_nothing(self, collections, loaded) -> None:
        view = keep(collections, loaded, "one", ["Plain Bob Minor"]).unwrap()
        assert view.splices is None
        assert "too few" in view.why_not

    def test_an_empty_set_says_nothing(self, collections, loaded) -> None:
        view = keep(collections, loaded, "empty", []).unwrap()
        assert view.splices is None


class TestReadingBack:
    def test_one_can_be_fetched(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        assert fetch(collections, loaded, "tuesday").unwrap().size == 2

    def test_a_set_everybody_names_needs_no_storing(self, collections, loaded) -> None:
        view = fetch(collections, loaded, "the standard eight").unwrap()
        assert view.size == 8

    def test_a_name_nobody_uses(self, collections, loaded) -> None:
        assert fetch(collections, loaded, "the weasel four").failure.reason is Reason.NOT_FOUND

    def test_everything_is_listed(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        assert len(listing(collections, loaded).unwrap()) == 4

    def test_the_known_sets_can_be_left_out(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        assert len(listing(collections, loaded, include_known=False).unwrap()) == 1

    def test_a_stored_set_hides_the_known_one_of_the_same_name(self, collections, loaded) -> None:
        keep(collections, loaded, "the standard eight", MINOR)
        found = listing(collections, loaded).unwrap()
        eights = [view for view in found if view.name.lower() == "the standard eight"]
        assert len(eights) == 1
        assert eights[0].size == 2


class TestChanging:
    def test_a_method_can_be_added(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        view = add_to(collections, loaded, "Tuesday", "Grandsire Doubles").unwrap()
        assert view.size == 3

    def test_adding_one_it_has(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        result = add_to(collections, loaded, "Tuesday", "Plain Bob Minor")
        assert result.failure.reason is Reason.ALREADY_EXISTS

    def test_a_method_can_be_taken_out(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        view = take_out(collections, loaded, "Tuesday", "Plain Bob Minor").unwrap()
        assert view.size == 1

    def test_taking_out_one_it_does_not_have(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        result = take_out(collections, loaded, "Tuesday", "Bristol Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_known_set_cannot_be_changed(self, collections, loaded) -> None:
        result = add_to(collections, loaded, "the standard eight", "Plain Bob Minor")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_one_can_be_forgotten(self, collections, loaded) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        assert forget(collections, "Tuesday").ok
        assert len(listing(collections, loaded, include_known=False).unwrap()) == 0

    def test_forgetting_one_that_is_not_there(self, collections) -> None:
        assert forget(collections, "Nothing").failure.reason is Reason.NOT_FOUND


class TestCoverage:
    def test_what_one_ringer_covers(self, collections, loaded, band) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        view = coverage(collections, band, "Tuesday", who="Ann").unwrap()
        assert view.rings == 1
        assert view.share == 0.5

    def test_it_says_what_is_left(self, collections, loaded, band) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        view = coverage(collections, band, "Tuesday", who="Ann").unwrap()
        assert view.missing == ("Cambridge Surprise Minor",)

    def test_the_whole_band_between_them(self, collections, loaded, band) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        view = coverage(collections, band, "Tuesday").unwrap()
        assert view.share == 1.0

    def test_a_ringer_nobody_has_heard_of(self, collections, loaded, band) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        result = coverage(collections, band, "Tuesday", who="Nobody")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_set_nobody_names(self, collections, band) -> None:
        assert coverage(collections, band, "the weasel four").failure.reason is Reason.NOT_FOUND

    def test_a_known_set_can_be_measured(self, collections, loaded, band) -> None:
        view = coverage(collections, band, "the standard eight").unwrap()
        assert view.size == 8
        assert view.rings == 0

    def test_a_summary_reads_as_a_share(self, collections, loaded, band) -> None:
        keep(collections, loaded, "Tuesday", MINOR)
        assert "1 of 2" in coverage(collections, band, "Tuesday", who="Ann").unwrap().summary()
