from blueline.service import proving as touches
from blueline.service.results import Reason
from tests.methods import GRANDSIRE_DOUBLES, PLAIN_BOB_DOUBLES, PLAIN_BOB_MINOR


class TestCallsFor:
    def test_plain_bob_gets_a_fourths_place_bob(self):
        calls = touches.calls_for(PLAIN_BOB_MINOR)
        assert str(calls["-"].change) == "14"
        assert calls["-"].offset == 0

    def test_grandsire_gets_its_own_called_a_change_earlier(self):
        calls = touches.calls_for(GRANDSIRE_DOUBLES)
        assert str(calls["-"].change) == "3"
        assert calls["-"].offset == 1

    def test_both_offer_a_bob_and_a_single(self):
        calls = touches.calls_for(PLAIN_BOB_MINOR)
        assert {"-", "s"} <= set(calls)

    def test_b_works_as_well_as_a_dash(self):
        # Typing a calling full of dashes on a command line is awkward.
        calls = touches.calls_for(PLAIN_BOB_MINOR)
        assert calls["b"] is calls["-"]
        assert calls["."] is calls["p"] if "p" in calls else True

    def test_the_aliases_do_not_invent_calls_a_method_does_not_have(self):
        calls = touches.calls_for(PLAIN_BOB_MINOR)
        assert "p" not in calls


class TestBuild:
    def test_it_builds_a_touch_from_a_calling(self):
        touch = touches.build(PLAIN_BOB_MINOR, "---").unwrap()
        assert touch.leads == 3
        assert touch.length == 36

    def test_a_block_can_be_repeated(self):
        touch = touches.build(PLAIN_BOB_DOUBLES, "ppp-", times=3).unwrap()
        assert touch.leads == 12
        assert touch.length == 120

    def test_repeating_once_leaves_it_alone(self):
        assert touches.build(PLAIN_BOB_MINOR, "---", times=1).unwrap().leads == 3

    def test_a_symbol_it_does_not_know_is_invalid(self):
        assert touches.build(PLAIN_BOB_MINOR, "-x-").failure.reason is Reason.INVALID

    def test_an_empty_calling_is_invalid(self):
        assert touches.build(PLAIN_BOB_MINOR, "  ").failure.reason is Reason.INVALID


class TestReport:
    def test_the_three_bob_touch_comes_round_and_is_true(self):
        touch = touches.build(PLAIN_BOB_MINOR, "---").unwrap()
        report = touches.report_on(touch, "Plain Bob Minor")
        assert report.comes_round
        assert report.is_true
        assert report.is_ringable

    def test_it_carries_the_calling_back(self):
        touch = touches.build(PLAIN_BOB_MINOR, "-p-").unwrap()
        assert touches.report_on(touch, "x").calling == "-p-"

    def test_the_classic_hundred_and_twenty_is_an_extent(self):
        touch = touches.build(PLAIN_BOB_DOUBLES, "ppp-", times=3).unwrap()
        report = touches.report_on(touch, "Plain Bob Doubles")
        assert report.length == 120
        assert report.is_extent
        assert report.extent_length == 120

    def test_a_touch_that_does_not_come_round_says_so(self):
        touch = touches.build(PLAIN_BOB_MINOR, "--").unwrap()
        report = touches.report_on(touch, "x")
        assert not report.comes_round
        assert not report.is_ringable
        assert "does not come round" in report.summary()

    def test_a_false_touch_names_the_repeats(self):
        touch = touches.build(PLAIN_BOB_DOUBLES, "pppp", times=2).unwrap()
        report = touches.report_on(touch, "x")
        assert not report.is_true
        assert report.repeats

    def test_it_caps_the_repeats_it_lists(self):
        touch = touches.build(PLAIN_BOB_DOUBLES, "pppp", times=2).unwrap()
        assert len(touches.report_on(touch, "x").repeats) <= 10

    def test_a_true_touch_summarises_as_true(self):
        touch = touches.build(PLAIN_BOB_MINOR, "---").unwrap()
        assert touches.report_on(touch, "x").summary() == "36 true changes"

    def test_it_counts_the_music(self):
        touch = touches.build(PLAIN_BOB_MINOR, "---").unwrap()
        assert touches.report_on(touch, "x").music.named["rounds"] == 1

    def test_it_says_where_it_finished(self):
        touch = touches.build(PLAIN_BOB_MINOR, "--").unwrap()
        assert touches.report_on(touch, "x").final_row != "123456"


class TestProve:
    def test_it_proves_a_touch_of_a_stored_method(self, loaded):
        report = touches.prove(loaded, "Plain Bob Minor", "---").unwrap()
        assert report.is_ringable
        assert report.title == "Plain Bob Minor"

    def test_it_proves_the_classic_hundred_and_twenty(self, loaded):
        report = touches.prove(loaded, "Plain Bob Doubles", "ppp-", times=3).unwrap()
        assert report.is_extent

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert (
            touches.prove(loaded, "Nowhere Surprise Major", "-").failure.reason is Reason.NOT_FOUND
        )

    def test_a_bad_calling_is_invalid(self, loaded):
        assert touches.prove(loaded, "Plain Bob Minor", "zzz").failure.reason is Reason.INVALID

    def test_ringing_a_block_no_times_is_invalid(self, loaded):
        assert (
            touches.prove(loaded, "Plain Bob Minor", "-", times=0).failure.reason is Reason.INVALID
        )

    def test_grandsire_takes_its_own_calls(self, loaded):
        assert touches.prove(loaded, "Grandsire Doubles", "-p-").ok


class TestPlainCourse:
    def test_it_reports_the_plain_course(self, loaded):
        report = touches.course_of(loaded, "Cambridge Surprise Minor").unwrap()
        assert report.length == 120
        assert report.is_ringable

    def test_it_is_all_plain_leads(self, loaded):
        assert touches.course_of(loaded, "Plain Bob Minor").unwrap().calling == "ppppp"

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert (
            touches.course_of(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND
        )
