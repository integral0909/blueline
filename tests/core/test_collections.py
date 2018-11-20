"""Named sets of methods."""

from __future__ import annotations

import pytest

from blueline.core.collections import (
    KNOWN,
    MOST_TITLES,
    STANDARD_EIGHT,
    STANDARD_FOUR,
    Collection,
    CollectionError,
    covered_by,
    fold,
    known,
    missing_from,
    overlap,
)

THREE = Collection(
    name="a practice set",
    titles=frozenset({"Plain Bob Minor", "Cambridge Surprise Minor", "Grandsire Doubles"}),
)


class TestCollection:
    def test_it_counts_what_is_in_it(self) -> None:
        assert len(THREE) == 3

    def test_it_knows_what_it_holds(self) -> None:
        assert "Plain Bob Minor" in THREE

    def test_titles_are_matched_loosely(self) -> None:
        assert "  plain   bob   minor " in THREE

    def test_something_it_does_not_hold(self) -> None:
        assert "Bristol Surprise Major" not in THREE

    def test_something_that_is_not_a_title(self) -> None:
        assert 7 not in THREE

    def test_it_needs_a_name(self) -> None:
        with pytest.raises(CollectionError, match="needs a name"):
            Collection(name="  ")

    def test_it_cannot_hold_a_blank(self) -> None:
        with pytest.raises(CollectionError, match="blank title"):
            Collection(name="x", titles=frozenset({"Plain Bob Minor", "   "}))

    def test_a_method_cannot_be_in_it_twice(self) -> None:
        with pytest.raises(CollectionError, match="twice"):
            Collection(name="x", titles=frozenset({"Plain Bob Minor", "plain bob minor"}))

    def test_a_collection_the_size_of_a_library(self) -> None:
        many = frozenset(f"Method {index} Major" for index in range(MOST_TITLES + 1))
        with pytest.raises(CollectionError, match="is a library"):
            Collection(name="x", titles=many)

    def test_it_prints_in_name_order(self) -> None:
        assert THREE.sorted[0] == "Cambridge Surprise Minor"

    def test_a_summary_counts(self) -> None:
        assert THREE.summary() == "a practice set, 3 methods"

    def test_an_empty_one_says_so(self) -> None:
        assert Collection(name="x").summary() == "x, empty"


class TestChanging:
    def test_one_can_be_added(self) -> None:
        bigger = THREE.with_added("Bristol Surprise Major")
        assert len(bigger) == 4
        assert "Bristol Surprise Major" in bigger

    def test_the_original_is_untouched(self) -> None:
        THREE.with_added("Bristol Surprise Major")
        assert len(THREE) == 3

    def test_adding_one_it_already_has(self) -> None:
        with pytest.raises(CollectionError, match="already in"):
            THREE.with_added("plain bob minor")

    def test_one_can_be_taken_out(self) -> None:
        smaller = THREE.without("Plain Bob Minor")
        assert "Plain Bob Minor" not in smaller

    def test_taking_out_one_it_does_not_have(self) -> None:
        with pytest.raises(CollectionError, match="is not in"):
            THREE.without("Bristol Surprise Major")

    def test_the_note_survives(self) -> None:
        noted = Collection(name="x", titles=frozenset({"Plain Bob Minor"}), note="for Tuesdays")
        assert noted.with_added("Grandsire Doubles").note == "for Tuesdays"


class TestComparing:
    def test_what_two_sets_share(self) -> None:
        shared = overlap(STANDARD_EIGHT, STANDARD_FOUR)
        assert len(shared) == 4

    def test_sharing_nothing(self) -> None:
        assert overlap(THREE, STANDARD_FOUR) == frozenset()

    def test_what_somebody_is_missing(self) -> None:
        left = missing_from(STANDARD_FOUR, {"Cambridge Surprise Major"})
        assert len(left) == 3

    def test_somebody_who_rings_the_lot(self) -> None:
        assert missing_from(STANDARD_FOUR, set(STANDARD_FOUR.titles)) == frozenset()

    def test_how_much_somebody_covers(self) -> None:
        assert covered_by(STANDARD_FOUR, {"Cambridge Surprise Major"}) == 0.25

    def test_covering_none_of_it(self) -> None:
        assert covered_by(STANDARD_FOUR, set()) == 0.0

    def test_covering_all_of_it(self) -> None:
        assert covered_by(STANDARD_FOUR, set(STANDARD_FOUR.titles)) == 1.0

    def test_an_empty_set_is_fully_covered(self) -> None:
        assert covered_by(Collection(name="x"), set()) == 1.0


class TestKnownSets:
    def test_the_standard_eight_has_eight(self) -> None:
        assert len(STANDARD_EIGHT) == 8

    def test_the_standard_four_is_inside_the_eight(self) -> None:
        assert overlap(STANDARD_FOUR, STANDARD_EIGHT) == STANDARD_FOUR.titles

    def test_one_can_be_looked_up(self) -> None:
        assert known("the standard eight") is STANDARD_EIGHT

    def test_names_are_matched_loosely(self) -> None:
        assert known("  THE  Standard  Eight ") is STANDARD_EIGHT

    def test_something_nobody_names(self) -> None:
        with pytest.raises(CollectionError, match="anybody names"):
            known("the weasel four")

    def test_every_known_set_is_named_after_itself(self) -> None:
        for name, collection in KNOWN.items():
            assert fold(collection.name) == name

    def test_they_all_say_what_they_are_for(self) -> None:
        assert all(collection.note for collection in KNOWN.values())
