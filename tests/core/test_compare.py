"""What two methods have in common."""

from __future__ import annotations

import pytest

from blueline.core.compare import CompareError, compare, most_alike, shared_work
from blueline.library.builtin import standard_methods
from tests.methods import (
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    PLAIN_BOB_MAJOR,
    PLAIN_BOB_MINOR,
)

MAJORS = [method for method in standard_methods() if method.stage == 8]
YORKSHIRE = next(method for method in MAJORS if method.name == "Yorkshire")
SUPERLATIVE = next(method for method in MAJORS if method.name == "Superlative")
BRISTOL = next(method for method in MAJORS if method.name == "Bristol")


class TestComparing:
    def test_a_method_against_itself(self) -> None:
        result = compare(CAMBRIDGE_MAJOR, CAMBRIDGE_MAJOR)
        assert result.identical
        assert result.share == 1.0

    def test_it_counts_the_changes_that_agree(self) -> None:
        result = compare(CAMBRIDGE_MAJOR, YORKSHIRE)
        assert 0 < result.same < result.changes

    def test_it_says_where_they_part(self) -> None:
        result = compare(CAMBRIDGE_MAJOR, YORKSHIRE)
        assert result.first_difference is not None
        assert result.first_difference.at > 0

    def test_a_divergence_reads_as_a_place(self) -> None:
        result = compare(CAMBRIDGE_MAJOR, YORKSHIRE)
        assert "against" in str(result.first_difference)

    def test_cambridge_is_more_like_superlative_than_bristol(self) -> None:
        # Which is the reason a band learns them in that order.
        against_superlative = compare(CAMBRIDGE_MAJOR, SUPERLATIVE).share
        against_bristol = compare(CAMBRIDGE_MAJOR, BRISTOL).share
        assert against_superlative > against_bristol

    def test_the_standard_four_share_a_lead_head(self) -> None:
        assert compare(CAMBRIDGE_MAJOR, YORKSHIRE).same_lead_head

    def test_bristol_does_not(self) -> None:
        assert not compare(CAMBRIDGE_MAJOR, BRISTOL).same_lead_head

    def test_a_plain_method_is_a_long_way_off(self) -> None:
        assert compare(CAMBRIDGE_MAJOR, PLAIN_BOB_MAJOR).share < 0.5

    def test_two_stages_cannot_be_compared(self) -> None:
        with pytest.raises(CompareError, match="at 6"):
            compare(CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR)

    def test_a_summary_reads_as_a_share(self) -> None:
        assert "agree on" in compare(CAMBRIDGE_MAJOR, YORKSHIRE).summary()

    def test_a_summary_of_the_same_method(self) -> None:
        assert "the same method" in compare(CAMBRIDGE_MAJOR, CAMBRIDGE_MAJOR).summary()


class TestDifferentLengths:
    def test_leads_of_different_lengths_are_noticed(self) -> None:
        result = compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR)
        assert not result.same_length

    def test_the_extra_changes_all_count_as_differences(self) -> None:
        # Otherwise a short lead that agrees as far as it goes would read as
        # mostly the same method.
        result = compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR)
        assert result.changes == max(len(PLAIN_BOB_MINOR.changes), len(CAMBRIDGE_MINOR.changes))

    def test_it_is_never_identical(self) -> None:
        assert not compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR).identical

    def test_the_summary_says_so(self) -> None:
        assert "different lengths" in compare(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR).summary()


class TestSharedWork:
    def test_the_treble_does_the_same_in_both(self) -> None:
        # Both are treble dodging, so the treble's path is the same and the
        # difference is entirely in the working bells.
        assert shared_work(CAMBRIDGE_MAJOR, YORKSHIRE, 1) == 32

    def test_a_working_bell_does_not(self) -> None:
        assert shared_work(CAMBRIDGE_MAJOR, YORKSHIRE, 2) < 32

    def test_bristol_shares_much_less(self) -> None:
        assert shared_work(CAMBRIDGE_MAJOR, BRISTOL, 2) < shared_work(CAMBRIDGE_MAJOR, YORKSHIRE, 2)

    def test_a_method_against_itself_shares_everything(self) -> None:
        assert shared_work(CAMBRIDGE_MAJOR, CAMBRIDGE_MAJOR, 5) == 32

    def test_two_stages_cannot_be_compared(self) -> None:
        with pytest.raises(CompareError, match="same stage"):
            shared_work(CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR, 2)


class TestMostAlike:
    def test_it_finds_the_nearest(self) -> None:
        nearest = most_alike(CAMBRIDGE_MAJOR, MAJORS)
        assert nearest is not None
        assert nearest.name in {"Superlative", "Lincolnshire"}

    def test_it_does_not_pick_the_method_itself(self) -> None:
        assert most_alike(CAMBRIDGE_MAJOR, MAJORS).name != "Cambridge"

    def test_a_different_stage_is_not_a_candidate(self) -> None:
        assert most_alike(CAMBRIDGE_MAJOR, [CAMBRIDGE_MINOR]) is None

    def test_nothing_to_compare_against(self) -> None:
        assert most_alike(CAMBRIDGE_MAJOR, []) is None

    def test_a_set_holding_only_itself(self) -> None:
        assert most_alike(CAMBRIDGE_MAJOR, [CAMBRIDGE_MAJOR]) is None
