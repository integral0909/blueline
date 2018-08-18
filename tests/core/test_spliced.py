import pytest

from blueline.analysis import analyse
from blueline.core.calls import plain_bob_calls
from blueline.core.row import Row
from blueline.core.spliced import (
    Leg,
    Spliced,
    build_spliced,
    lead_heads_agree,
    spliceable,
)
from blueline.core.truth import prove
from blueline.errors import TouchError
from blueline.library import standard_methods
from tests.methods import CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR, PLAIN_BOB_MAJOR

PB8 = plain_bob_calls(8)

#: The Surprise Major methods that verifiably share a lead head.
GROUP = {
    method.name: method
    for method in standard_methods()
    if method.stage == 8 and str(method.lead_head) == "15738264"
}


class TestGroup:
    def test_four_of_the_standard_methods_share_a_lead_head(self):
        assert sorted(GROUP) == ["Cambridge", "Lincolnshire", "Superlative", "Yorkshire"]

    def test_they_are_all_surprise(self):
        for method in GROUP.values():
            assert str(analyse(method).classification) == "Surprise"


class TestLeadHeadsAgree:
    def test_a_method_agrees_with_itself(self):
        assert lead_heads_agree(CAMBRIDGE_MAJOR, CAMBRIDGE_MAJOR)

    def test_the_group_all_agree(self):
        methods = list(GROUP.values())
        for other in methods[1:]:
            assert lead_heads_agree(methods[0], other)

    def test_different_stages_never_agree(self):
        assert not lead_heads_agree(CAMBRIDGE_MINOR, CAMBRIDGE_MAJOR)

    def test_a_method_with_another_lead_end_does_not_agree(self):
        assert not lead_heads_agree(CAMBRIDGE_MAJOR, PLAIN_BOB_MAJOR)

    def test_it_reports_the_pairs_that_will_not_splice(self):
        assert spliceable(list(GROUP.values())) == []

    def test_a_mismatched_pair_is_reported(self):
        bad = spliceable([CAMBRIDGE_MAJOR, PLAIN_BOB_MAJOR])
        assert bad == [("Cambridge", "Plain")]


class TestBuilding:
    def test_it_builds_from_initials(self):
        touch = build_spliced(GROUP, "CYSL")
        assert touch.order == "CYSL"
        assert touch.leads == 4

    def test_the_length_is_the_leads_added_up(self):
        touch = build_spliced(GROUP, "CYSL")
        assert touch.length == 4 * 32

    def test_it_names_the_methods_it_used(self):
        touch = build_spliced(GROUP, "CYC")
        assert touch.methods_used() == ["Cambridge", "Yorkshire"]

    def test_a_calling_runs_alongside_the_order(self):
        touch = build_spliced(GROUP, "CYSL", PB8, "p-p-")
        assert touch.calling == "p-p-"

    def test_a_short_calling_leaves_the_rest_plain(self):
        touch = build_spliced(GROUP, "CYSL", PB8, "-")
        assert touch.calling == "-ppp"

    def test_no_calling_at_all_is_all_plain(self):
        assert build_spliced(GROUP, "CY").calling == "pp"

    def test_an_initial_it_does_not_know_is_refused(self):
        with pytest.raises(TouchError, match="beginning with"):
            build_spliced(GROUP, "CZ")

    def test_a_call_it_does_not_know_is_refused(self):
        with pytest.raises(TouchError, match="no call"):
            build_spliced(GROUP, "CY", PB8, "pz")

    def test_it_does_not_mind_lower_case_initials(self):
        assert build_spliced(GROUP, "cy").order == "CY"


class TestSpliced:
    def test_it_refuses_an_empty_touch(self):
        with pytest.raises(TouchError, match="at least one"):
            Spliced(legs=())

    def test_it_refuses_a_splice_across_stages(self):
        with pytest.raises(TouchError, match="across stages"):
            Spliced(legs=(Leg(CAMBRIDGE_MAJOR), Leg(CAMBRIDGE_MINOR)))

    def test_it_carries_the_stage(self):
        assert build_spliced(GROUP, "CY").stage == 8

    def test_there_is_one_more_row_than_the_touch_is_long(self):
        touch = build_spliced(GROUP, "CYSL")
        assert len(touch.rows()) == touch.length + 1

    def test_it_refuses_a_start_from_another_stage(self):
        with pytest.raises(TouchError):
            build_spliced(GROUP, "CY").rows(Row.rounds(6))

    def test_a_lead_of_each_is_the_same_length_as_ringing_them_apart(self):
        touch = build_spliced(GROUP, "CY")
        assert touch.length == GROUP["Cambridge"].lead_length + GROUP["Yorkshire"].lead_length


class TestRinging:
    def test_seven_plain_leads_of_the_group_come_round(self):
        # They share Plain Bob lead heads, so seven leads brings it back
        # however the methods are mixed up.
        touch = build_spliced(GROUP, "CYSLCYS")
        assert touch.comes_round()

    def test_and_it_is_true(self):
        touch = build_spliced(GROUP, "CYSLCYS")
        assert prove(touch.rows()[:-1]).is_true

    def test_a_different_order_also_comes_round(self):
        assert build_spliced(GROUP, "LSYCLSY").comes_round()

    def test_fewer_leads_do_not_come_round(self):
        assert not build_spliced(GROUP, "CYSL").comes_round()

    def test_the_plain_course_of_one_method_still_works_spliced(self):
        touch = build_spliced(GROUP, "CCCCCCC")
        assert touch.comes_round()
        assert prove(touch.rows()[:-1]).is_true
