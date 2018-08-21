from blueline.service import spliced
from blueline.service.results import Reason

GROUP = [
    "Cambridge Surprise Major",
    "Yorkshire Surprise Major",
    "Superlative Surprise Major",
    "Lincolnshire Surprise Major",
]


class TestGather:
    def test_it_finds_the_methods(self, loaded):
        found = spliced.gather(loaded, GROUP).unwrap()
        assert sorted(found) == ["Cambridge", "Lincolnshire", "Superlative", "Yorkshire"]

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = spliced.gather(loaded, ["Nowhere Surprise Major"])
        assert result.failure.reason is Reason.NOT_FOUND

    def test_two_methods_sharing_an_initial_are_refused(self, loaded):
        result = spliced.gather(loaded, ["Cambridge Surprise Major", "Cambridge Surprise Minor"])
        assert result.failure.reason is Reason.INVALID
        assert "initial" in result.failure.detail

    def test_asking_for_nothing_is_invalid(self, loaded):
        assert spliced.gather(loaded, []).failure.reason is Reason.INVALID


class TestSplice:
    def test_seven_leads_of_the_group_come_round_true(self, loaded):
        report = spliced.splice(loaded, GROUP, "CYSLCYS").unwrap()
        assert report.is_ringable
        assert report.length == 7 * 32

    def test_it_names_the_methods_used(self, loaded):
        report = spliced.splice(loaded, GROUP, "CYC").unwrap()
        assert report.methods_used == ("Cambridge", "Yorkshire")

    def test_it_carries_the_order_back(self, loaded):
        assert spliced.splice(loaded, GROUP, "CYSL").unwrap().order == "CYSL"

    def test_a_calling_can_be_given(self, loaded):
        report = spliced.splice(loaded, GROUP, "CYSL", calling="p-pp").unwrap()
        assert report.calling == "p-pp"

    def test_a_touch_that_does_not_come_round_says_so(self, loaded):
        report = spliced.splice(loaded, GROUP, "CY").unwrap()
        assert not report.comes_round
        assert "does not come round" in report.summary()

    def test_a_true_touch_summarises_as_true(self, loaded):
        report = spliced.splice(loaded, GROUP, "CYSLCYS").unwrap()
        assert "true changes" in report.summary()
        assert "4 methods" in report.summary()

    def test_methods_that_do_not_splice_are_refused_up_front(self, loaded):
        result = spliced.splice(loaded, [*GROUP, "Bristol Surprise Major"], "CYSLB")
        assert result.failure.reason is Reason.INVALID
        assert "lead heads differ" in result.failure.detail

    def test_splicing_across_stages_is_refused(self, loaded):
        result = spliced.splice(loaded, ["Cambridge Surprise Major", "London Surprise Minor"], "CL")
        assert result.failure.reason is Reason.INVALID
        assert "stages" in result.failure.detail

    def test_an_initial_it_does_not_know_is_invalid(self, loaded):
        result = spliced.splice(loaded, GROUP, "CZ")
        assert result.failure.reason is Reason.INVALID

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = spliced.splice(loaded, ["Nowhere Surprise Major"], "N")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_it_counts_the_music(self, loaded):
        report = spliced.splice(loaded, GROUP, "CYSLCYS").unwrap()
        assert report.music.named["rounds"] == 1

    def test_one_method_spliced_with_itself_is_its_plain_course(self, loaded):
        report = spliced.splice(loaded, ["Cambridge Surprise Major"], "CCCCCCC").unwrap()
        assert report.is_ringable
        assert report.length == 224
