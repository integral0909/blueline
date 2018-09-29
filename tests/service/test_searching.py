from blueline.service import proving
from blueline.service import searching as touches
from blueline.service.results import Reason


class TestSearch:
    def test_it_finds_callings(self, loaded):
        report = touches.search(loaded, "Plain Bob Minor", max_found=3).unwrap()
        assert report.found
        assert report.title == "Plain Bob Minor"

    def test_the_plain_course_comes_first(self, loaded):
        report = touches.search(loaded, "Plain Bob Minor", max_found=3).unwrap()
        assert report.found[0].calling == "ppppp"

    def test_everything_it_finds_proves_true(self, loaded):
        report = touches.search(loaded, "Plain Bob Doubles", max_found=4).unwrap()
        for entry in report.found:
            proved = proving.prove(loaded, "Plain Bob Doubles", entry.calling).unwrap()
            assert proved.is_ringable

    def test_it_honours_a_minimum_length(self, loaded):
        report = touches.search(loaded, "Plain Bob Doubles", min_length=100, max_found=3).unwrap()
        assert all(entry.length >= 100 for entry in report.found)

    def test_it_says_which_calls_it_used(self, loaded):
        report = touches.search(loaded, "Plain Bob Minor", allowed="p-", max_found=2).unwrap()
        assert report.looked_at == "p-"

    def test_it_says_whether_it_finished(self, loaded):
        report = touches.search(loaded, "Plain Bob Minor", max_found=2).unwrap()
        assert isinstance(report.exhausted, bool)
        assert "callings" in report.summary()

    def test_a_call_the_method_does_not_have_is_invalid(self, loaded):
        result = touches.search(loaded, "Plain Bob Minor", allowed="pz")
        assert result.failure.reason is Reason.INVALID

    def test_a_backwards_length_range_is_invalid(self, loaded):
        result = touches.search(loaded, "Plain Bob Minor", min_length=500, max_length=100)
        assert result.failure.reason is Reason.INVALID

    def test_asking_for_nothing_is_invalid(self, loaded):
        assert (
            touches.search(loaded, "Plain Bob Minor", max_found=0).failure.reason is Reason.INVALID
        )

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert touches.search(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND


class TestForLength:
    def test_it_finds_a_touch_at_the_length(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Doubles", 120, max_found=1).unwrap()
        assert report.reachable
        assert report.found
        assert report.found[0].length == 120

    def test_it_says_which_method_and_target(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Doubles", 120, max_found=1).unwrap()
        assert report.title == "Plain Bob Doubles"
        assert report.target == "120"

    def test_a_length_past_the_extent_is_unreachable(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Minor", 1260).unwrap()
        assert not report.reachable
        assert "only 720 rows" in report.why_not

    def test_a_length_that_does_not_divide_into_leads_is_unreachable(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Major", 1250).unwrap()
        assert not report.reachable
        assert "16 changes to a lead" in report.why_not

    def test_an_unreachable_target_says_so_in_the_summary(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Minor", 1260).unwrap()
        assert "cannot be rung" in report.summary()

    def test_a_tolerance_can_bring_it_into_range(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Major", 1250, tolerance=2).unwrap()
        assert report.reachable

    def test_the_summary_counts_what_it_found(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Doubles", 120, max_found=1).unwrap()
        assert "calling" in report.summary()

    def test_a_length_of_nothing_is_invalid(self, loaded):
        assert touches.for_length(loaded, "Plain Bob Minor", 0).failure.reason is Reason.INVALID

    def test_asking_for_no_results_is_invalid(self, loaded):
        result = touches.for_length(loaded, "Plain Bob Minor", 60, max_found=0)
        assert result.failure.reason is Reason.INVALID

    def test_a_call_it_does_not_have_is_invalid(self, loaded):
        result = touches.for_length(loaded, "Plain Bob Minor", 60, allowed="pz")
        assert result.failure.reason is Reason.INVALID

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = touches.for_length(loaded, "Nowhere Surprise Major", 120)
        assert result.failure.reason is Reason.NOT_FOUND

    def test_everything_it_finds_proves_true(self, loaded):
        report = touches.for_length(loaded, "Plain Bob Doubles", 120, max_found=2).unwrap()
        for entry in report.found:
            proved = proving.prove(loaded, "Plain Bob Doubles", entry.calling).unwrap()
            assert proved.is_ringable
