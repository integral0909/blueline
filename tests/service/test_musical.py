"""Ranking what a search turns up on its music."""

from __future__ import annotations

from blueline.service.results import Reason
from blueline.service.searching import most_musical

PLAIN = "Plain Bob Minor"


class TestMostMusical:
    def test_it_finds_something(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=30).unwrap()
        assert report.best

    def test_the_best_comes_first(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=40).unwrap()
        scores = [entry.per_row for entry in report.best]
        assert scores == sorted(scores, reverse=True)

    def test_it_says_how_many_it_tried(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=20).unwrap()
        assert report.considered <= 20

    def test_the_ranking_can_be_cut_short(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=40, how_many=3).unwrap()
        assert len(report.best) <= 3

    def test_every_entry_carries_its_length(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=20).unwrap()
        assert all(entry.length > 0 for entry in report.best)

    def test_every_entry_says_where_its_music_came_from(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=20).unwrap()
        assert all(entry.music for entry in report.best)

    def test_a_narrower_length_finds_less(self, loaded) -> None:
        wide = most_musical(loaded, PLAIN, max_found=40).unwrap()
        narrow = most_musical(loaded, PLAIN, min_length=600, max_found=40).unwrap()
        assert narrow.considered <= wide.considered

    def test_a_longer_minimum_run_scores_less(self, loaded) -> None:
        loose = most_musical(loaded, PLAIN, max_found=20, min_run=4).unwrap()
        tight = most_musical(loaded, PLAIN, max_found=20, min_run=6).unwrap()
        assert tight.best[0].score <= loose.best[0].score

    def test_it_reads_as_a_report(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=20).unwrap()
        assert "callings tried" in report.summary()

    def test_an_entry_reads_as_a_calling(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, max_found=20).unwrap()
        assert "(" in str(report.best[0])

    def test_a_method_nobody_has_stored(self, loaded) -> None:
        result = most_musical(loaded, "Weasel Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_ranking_that_holds_nothing(self, loaded) -> None:
        assert most_musical(loaded, PLAIN, how_many=0).failure.reason is Reason.INVALID

    def test_a_length_nothing_reaches(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, min_length=5000, max_length=5040).unwrap()
        assert report.best == ()
        assert "nothing came round" in report.summary()

    def test_only_the_calls_asked_for_are_used(self, loaded) -> None:
        report = most_musical(loaded, PLAIN, allowed="p-", max_found=20).unwrap()
        assert all(set(entry.calling) <= {"p", "-"} for entry in report.best)

    def test_a_call_the_method_does_not_have(self, loaded) -> None:
        assert most_musical(loaded, PLAIN, allowed="pz").failure.reason is Reason.INVALID
