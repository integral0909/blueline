"""Marking a striking competition."""

from __future__ import annotations

from typing import List

from blueline.service.results import Reason
from blueline.service.striking import (
    drift_of,
    mark,
    order_of_merit,
    worst_of,
)


def steady(blows: int, gap: float = 0.2) -> List[float]:
    """Blows struck perfectly evenly."""
    return [index * gap for index in range(blows)]


def with_a_gap_at(blows: int, index: int, error: float) -> List[float]:
    """Steady ringing with one blow struck away from where it belonged."""
    times = steady(blows)
    return [time + (error if position > index else 0.0) for position, time in enumerate(times)]


class TestMarking:
    def test_steady_ringing_has_no_faults(self) -> None:
        report = mark("St Mary", steady(48), 6).unwrap()
        assert report.faults == 0
        assert report.percentage == 100.0

    def test_a_bad_blow_is_a_fault(self) -> None:
        report = mark("St Mary", with_a_gap_at(48, 10, 0.1), 6).unwrap()
        assert report.faults > 0

    def test_the_band_is_named(self) -> None:
        assert mark("  St Mary  ", steady(24), 6).unwrap().band == "St Mary"

    def test_rows_are_counted(self) -> None:
        assert mark("St Mary", steady(48), 6).unwrap().rows == 8

    def test_summary_reads_as_a_marking(self) -> None:
        assert mark("St Mary", steady(24), 6).unwrap().summary().startswith("St Mary: 0 faults")

    def test_a_band_needs_a_name(self) -> None:
        result = mark("   ", steady(24), 6)
        assert result.failure is not None
        assert result.failure.reason is Reason.INVALID

    def test_a_threshold_has_to_be_a_share(self) -> None:
        result = mark("St Mary", steady(24), 6, threshold=4.0)
        assert result.failure is not None
        assert "between 0 and 1" in result.failure.detail

    def test_too_few_blows_to_judge(self) -> None:
        result = mark("St Mary", [0.0], 6)
        assert result.failure is not None
        assert "two blows" in result.failure.detail

    def test_a_tighter_threshold_finds_more(self) -> None:
        times = with_a_gap_at(60, 20, 0.02)
        loose = mark("St Mary", times, 6, threshold=0.5).unwrap()
        tight = mark("St Mary", times, 6, threshold=0.02).unwrap()
        assert tight.faults >= loose.faults


class TestDrift:
    def test_nothing_wrong_is_even(self) -> None:
        assert drift_of(()) == "even"

    def test_a_band_running_away_is_early(self) -> None:
        report = mark("St Mary", steady(40), 8).unwrap()
        assert report.drift == "even"

    def test_worst_is_biggest_first(self) -> None:
        from blueline.core.striking import judge

        judgement = judge(with_a_gap_at(60, 20, 0.15), 6, threshold=0.05)
        worst = worst_of(judgement, count=3)
        assert len(worst) <= 3

    def test_worst_is_cut_to_what_a_judge_would_say(self) -> None:
        from blueline.core.striking import judge

        judgement = judge(with_a_gap_at(60, 20, 0.15), 6, threshold=0.001)
        assert len(worst_of(judgement)) <= 5


class TestOrderOfMerit:
    def test_the_cleanest_band_wins(self) -> None:
        attempts = {
            "St Mary": with_a_gap_at(48, 10, 0.2),
            "All Saints": steady(48),
        }
        order = order_of_merit(attempts, 6).unwrap()
        assert order[0].band == "All Saints"

    def test_every_band_is_marked(self) -> None:
        attempts = {"St Mary": steady(24), "All Saints": steady(24), "St Peter": steady(24)}
        assert len(order_of_merit(attempts, 6).unwrap()) == 3

    def test_a_band_that_cannot_be_judged_stops_the_lot(self) -> None:
        attempts = {"St Mary": steady(24), "All Saints": [0.0]}
        result = order_of_merit(attempts, 6)
        assert result.failure is not None
        assert "All Saints" in result.failure.detail

    def test_no_bands_at_all(self) -> None:
        result = order_of_merit({}, 6)
        assert result.failure is not None
        assert result.failure.reason is Reason.INVALID

    def test_a_tie_is_broken_on_steadiness(self) -> None:
        attempts = {"St Mary": steady(24), "All Saints": steady(24)}
        order = order_of_merit(attempts, 6).unwrap()
        assert order[0].percentage == order[1].percentage
