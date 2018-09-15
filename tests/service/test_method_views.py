"""The view types on their own, without a database anywhere near them."""

from __future__ import annotations

from blueline.service.method_views import HandbellView, ImportReport, LineView


class TestImportReport:
    def test_it_totals_both_halves(self):
        report = ImportReport(added=("a", "b"), skipped=("c",), problems=())
        assert report.total == 3

    def test_problems_are_not_counted_in_the_total(self):
        # A record that could not be read was never a method, so it is not one
        # of the ones looked at.
        report = ImportReport(added=("a",), skipped=(), problems=("line 3 is nonsense",))
        assert report.total == 1

    def test_a_clean_import_says_what_it_added(self):
        assert ImportReport(added=("a",), skipped=(), problems=()).summary() == "1 added"

    def test_it_mentions_what_was_already_there(self):
        report = ImportReport(added=(), skipped=("a", "b"), problems=())
        assert "2 already there" in report.summary()

    def test_it_mentions_what_it_could_not_read(self):
        report = ImportReport(added=(), skipped=(), problems=("bad",))
        assert "1 could not be read" in report.summary()

    def test_it_leaves_out_what_there_is_none_of(self):
        summary = ImportReport(added=("a",), skipped=(), problems=()).summary()
        assert "already there" not in summary
        assert "could not be read" not in summary


class TestLineView:
    def test_it_holds_what_a_ringer_needs(self):
        view = LineView(
            bell=2,
            places=(2, 1, 1, 2),
            described="2 to 1 down, 2 blows in 1",
            grid=("1*3456",),
            work={"leads": [1, 2], "lies": [], "dodges": [], "places": [2]},
        )
        assert view.bell == 2
        assert view.work["leads"] == [1, 2]

    def test_the_places_and_the_grid_are_separate_things(self):
        view = LineView(bell=1, places=(1, 2), described="", grid=("12", "21"), work={})
        assert len(view.places) == 2
        assert len(view.grid) == 2


class TestHandbellView:
    def a_view(self, **over) -> HandbellView:
        fields = {
            "pair": "1-2",
            "bells": (1, 2),
            "crossings": (3, 9),
            "together": (0, 1, 11),
        }
        fields.update(over)
        return HandbellView(**fields)

    def test_it_counts_the_crossings(self):
        assert "2 crossings" in self.a_view().summary()

    def test_one_crossing_reads_as_singular(self):
        assert "1 crossing," in self.a_view(crossings=(3,)).summary()

    def test_it_counts_how_often_they_are_together(self):
        assert "together 3 times" in self.a_view().summary()

    def test_a_pair_that_never_crosses_says_nought(self):
        assert "0 crossings" in self.a_view(crossings=()).summary()

    def test_it_names_the_pair(self):
        assert self.a_view(pair="5-6").summary().startswith("5-6:")


class TestSeparation:
    def test_the_views_do_not_drag_in_the_service(self):
        # The api converters and the command line renderers import these and
        # neither wants the service functions.
        import blueline.service.method_views as views

        assert not hasattr(views, "fetch")
        assert not hasattr(views, "search")
