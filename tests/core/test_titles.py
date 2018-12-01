"""Comparing titles, and keeping sets of them."""

from __future__ import annotations

import pytest

from blueline.core.titles import (
    as_lines,
    fold,
    from_lines,
    holds,
    in_order,
    same_title,
    without,
)

THREE = frozenset({"Plain Bob Minor", "Cambridge Surprise Minor", "Grandsire Doubles"})


class TestFold:
    def test_case_does_not_matter(self) -> None:
        assert fold("Plain Bob Minor") == fold("plain bob minor")

    def test_surrounding_space_does_not(self) -> None:
        assert fold("  Plain Bob Minor  ") == fold("Plain Bob Minor")

    def test_doubled_space_does_not(self) -> None:
        # Which comes off a paste as often as anything.
        assert fold("Cambridge  Surprise Major") == fold("Cambridge Surprise Major")

    def test_two_different_methods_do_not_fold_together(self) -> None:
        assert fold("Cambridge Surprise Major") != fold("Cambridge Surprise Minor")

    def test_same_title_uses_it(self) -> None:
        assert same_title("  PLAIN  bob minor ", "Plain Bob Minor")


class TestHolds:
    def test_it_finds_one(self) -> None:
        assert holds(THREE, "plain bob minor")

    def test_something_that_is_not_there(self) -> None:
        assert not holds(THREE, "Bristol Surprise Major")

    def test_an_empty_set_holds_nothing(self) -> None:
        assert not holds(frozenset(), "Plain Bob Minor")


class TestWithout:
    def test_it_takes_one_out(self) -> None:
        assert len(without(THREE, "PLAIN bob minor")) == 2

    def test_taking_out_one_that_is_not_there(self) -> None:
        assert len(without(THREE, "Bristol Surprise Major")) == 3

    def test_the_spelling_that_stays_is_the_stored_one(self) -> None:
        left = without(THREE, "plain bob minor")
        assert "Cambridge Surprise Minor" in left


class TestOrder:
    def test_it_sorts_the_way_it_compares(self) -> None:
        assert in_order(THREE)[0] == "Cambridge Surprise Minor"

    def test_case_does_not_change_the_order(self) -> None:
        assert in_order({"b Major", "A Minor"}) == ("A Minor", "b Major")

    def test_nothing_sorts_to_nothing(self) -> None:
        assert in_order(frozenset()) == ()


class TestLines:
    def test_a_set_becomes_a_column(self) -> None:
        assert as_lines({"B", "A"}) == "A\nB"

    def test_it_reads_back(self) -> None:
        assert from_lines(as_lines(THREE)) == THREE

    def test_blank_lines_are_dropped(self) -> None:
        assert from_lines("A\n\n  \nB\n") == frozenset({"A", "B"})

    def test_lines_are_trimmed(self) -> None:
        assert from_lines("  A  \n") == frozenset({"A"})

    def test_nothing_stored_reads_as_nothing(self) -> None:
        assert from_lines("") == frozenset()

    def test_an_empty_set_stores_as_nothing(self) -> None:
        assert as_lines(frozenset()) == ""

    @pytest.mark.parametrize(
        "titles",
        [THREE, frozenset({"One Major"}), frozenset()],
    )
    def test_it_round_trips(self, titles) -> None:
        assert from_lines(as_lines(titles)) == titles


class TestNobodyElseFolds:
    """Two modules with a private fold is how they end up disagreeing."""

    def test_ringers_uses_the_shared_one(self) -> None:
        import blueline.core.ringers as module

        assert "_fold" not in vars(module)

    def test_collections_uses_the_shared_one(self) -> None:
        import blueline.core.collections as module

        assert module.fold is fold
