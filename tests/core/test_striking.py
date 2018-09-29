
from typing import List

import pytest

from blueline.core.striking import (
    FAULT_THRESHOLD,
    Fault,
    Judgement,
    StrikingError,
    compare,
    gaps_between,
    judge,
)
from blueline.errors import BluelineError


def even(blows: int, gap: float = 0.2, start: float = 0.0) -> List[float]:
    """Perfectly even striking, which nobody has ever managed."""
    return [start + index * gap for index in range(blows)]


class TestGaps:
    def test_it_measures_between_blows(self):
        assert gaps_between([0.0, 0.2, 0.4]) == pytest.approx([0.2, 0.2])

    def test_one_blow_has_no_gaps(self):
        assert gaps_between([0.0]) == []

    def test_nothing_has_no_gaps(self):
        assert gaps_between([]) == []

    def test_there_is_one_fewer_gap_than_blows(self):
        assert len(gaps_between(even(20))) == 19


class TestJudge:
    def test_even_striking_has_no_faults(self):
        assert judge(even(48), stage=8).fault_count == 0

    def test_even_striking_scores_a_hundred(self):
        assert judge(even(48), stage=8).percentage == 100.0

    def test_a_late_blow_is_a_fault(self):
        times = even(24)
        times[10] -= 0.1
        assert judge(times, stage=8).fault_count > 0

    def test_it_says_which_way_the_fault_went(self):
        times = even(24)
        times[10] += 0.1
        found = judge(times, stage=8).faults
        assert any(fault.was_early for fault in found) or any(
            not fault.was_early for fault in found
        )

    def test_a_small_wobble_is_not_a_fault(self):
        times = even(24)
        times[10] += 0.2 * (FAULT_THRESHOLD / 2)
        assert judge(times, stage=8).fault_count == 0

    def test_a_slower_band_ringing_evenly_is_not_penalised(self):
        # The ideal gap is the average one. Judging against somebody else's
        # rhythm would call a steady slow band badly struck.
        assert judge(even(48, gap=0.5), stage=8).fault_count == 0

    def test_it_counts_the_rows(self):
        assert judge(even(48), stage=8).rows == 6

    def test_it_counts_the_blows(self):
        assert judge(even(48), stage=8).blows == 48

    def test_faults_per_row_follows_the_count(self):
        judged = judge(even(48), stage=8)
        assert judged.per_row == judged.fault_count / judged.rows

    def test_even_striking_has_no_spread(self):
        assert judge(even(48), stage=8).spread == pytest.approx(0.0)

    def test_ragged_striking_has_some(self):
        times = [0.0, 0.1, 0.4, 0.5, 0.9, 1.0, 1.5]
        assert judge(times, stage=8).spread > 0

    def test_too_few_blows_is_refused(self):
        with pytest.raises(StrikingError, match="two blows"):
            judge([0.0], stage=8)

    def test_no_bells_is_refused(self):
        with pytest.raises(StrikingError, match="one bell"):
            judge(even(10), stage=0)

    def test_blows_out_of_order_are_refused(self):
        with pytest.raises(StrikingError, match="in order"):
            judge([1.0, 0.0], stage=8)

    def test_a_striking_error_is_a_blueline_error(self):
        assert issubclass(StrikingError, BluelineError)

    def test_the_threshold_can_be_tightened(self):
        times = even(24)
        times[10] += 0.01
        assert judge(times, stage=8, threshold=0.01).fault_count > 0
        assert judge(times, stage=8, threshold=0.5).fault_count == 0


class TestSummary:
    def test_it_counts_the_faults_and_the_rows(self):
        summary = judge(even(48), stage=8).summary()
        assert "0 faults" in summary
        assert "6 rows" in summary

    def test_it_quotes_a_percentage(self):
        assert "100.0% clean" in judge(even(48), stage=8).summary()


class TestFault:
    def test_an_early_blow_says_so(self):
        assert Fault(row=3, place=5, error=-0.2).was_early

    def test_a_late_one_does_not(self):
        assert not Fault(row=3, place=5, error=0.2).was_early

    def test_it_reads_as_a_line(self):
        assert str(Fault(row=3, place=5, error=-0.2)) == "row 3, place 5, 20% early"


class TestCompare:
    def test_the_cleaner_one_wins(self):
        good = judge(even(48), stage=8)
        ragged = judge([0.0, 0.1, 0.4, 0.5, 0.9, 1.0, 1.5, 1.6], stage=8)
        assert compare(good, ragged) == "the first"
        assert compare(ragged, good) == "the second"

    def test_two_alike_are_much_the_same(self):
        judged = judge(even(48), stage=8)
        assert compare(judged, judged) == "much the same"


class TestEmptyJudgement:
    def test_no_blows_scores_a_hundred_rather_than_dividing_by_nothing(self):
        made = Judgement(rows=0, blows=0, faults=(), spread=0.0)
        assert made.percentage == 100.0
        assert made.per_row == 0.0
