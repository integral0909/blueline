import pytest

from blueline.core.leadheads import (
    LeadHeadGroup,
    group_methods,
    group_of,
    heads_of,
    share_lead_heads,
)
from blueline.core.row import Row
from blueline.core.spliced import lead_heads_agree
from blueline.library import standard_methods
from tests.methods import ALL_METHODS, CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR, method_id

MAJOR = [method for method in standard_methods() if method.stage == 8]
BY_NAME = {method.name: method for method in MAJOR}


class TestHeadsOf:
    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_there_is_one_head_per_lead(self, method):
        assert len(heads_of(method)) == method.leads_in_course

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_course_ends_on_rounds(self, method):
        assert heads_of(method)[-1].is_rounds

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_first_head_is_the_lead_head(self, method):
        assert heads_of(method)[0] == method.lead_head

    def test_no_head_comes_round_twice(self):
        heads = heads_of(CAMBRIDGE_MAJOR)
        assert len(set(heads)) == len(heads)


class TestGroupOf:
    def test_it_carries_the_lead_head(self):
        assert group_of(CAMBRIDGE_MAJOR).head == CAMBRIDGE_MAJOR.lead_head

    def test_it_carries_the_course_length_in_leads(self):
        assert group_of(CAMBRIDGE_MAJOR).order == 7

    def test_it_names_the_places_at_the_lead_end(self):
        assert group_of(CAMBRIDGE_MAJOR).places_at_lead_end == "12"

    def test_bristol_makes_the_back_place(self):
        assert group_of(BY_NAME["Bristol"]).places_at_lead_end == "18"

    def test_it_reads_as_a_line(self):
        text = str(group_of(CAMBRIDGE_MAJOR))
        assert "15738264" in text
        assert "7 leads" in text


class TestShareLeadHeads:
    def test_a_method_shares_with_itself(self):
        assert share_lead_heads(CAMBRIDGE_MAJOR, CAMBRIDGE_MAJOR)

    def test_the_seconds_place_surprise_major_all_share(self):
        together = ["Cambridge", "Yorkshire", "Superlative", "Lincolnshire"]
        first = BY_NAME[together[0]]
        for name in together[1:]:
            assert share_lead_heads(first, BY_NAME[name])

    def test_bristol_does_not_share_with_cambridge(self):
        # Eighths place at the lead end against seconds. No calling moves
        # between them, and comparing the set of rows the course passes
        # through said they did, which was the first version of this.
        assert not share_lead_heads(BY_NAME["Cambridge"], BY_NAME["Bristol"])

    def test_plain_bob_does_not_share_with_cambridge(self):
        assert not share_lead_heads(BY_NAME["Cambridge"], BY_NAME["Plain"])

    def test_two_stages_never_share(self):
        assert not share_lead_heads(CAMBRIDGE_MINOR, CAMBRIDGE_MAJOR)

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_it_agrees_with_what_splicing_uses(self, method):
        for other in ALL_METHODS:
            assert share_lead_heads(method, other) == lead_heads_agree(method, other)


class TestGrouping:
    def test_the_four_seconds_place_methods_come_out_together(self):
        grouped = group_methods(MAJOR)
        assert grouped["15738264"] == [
            "Cambridge 8",
            "Lincolnshire 8",
            "Superlative 8",
            "Yorkshire 8",
        ]

    def test_bristol_is_on_its_own(self):
        assert group_methods(MAJOR)["14263857"] == ["Bristol 8"]

    def test_every_method_lands_in_exactly_one_group(self):
        grouped = group_methods(MAJOR)
        total = sum(len(names) for names in grouped.values())
        assert total == len(MAJOR)

    def test_the_groups_come_back_sorted(self):
        grouped = group_methods(MAJOR)
        assert list(grouped) == sorted(grouped)

    def test_the_names_within_a_group_come_back_sorted(self):
        for names in group_methods(MAJOR).values():
            assert names == sorted(names)

    def test_grouping_nothing_gives_nothing(self):
        assert group_methods([]) == {}

    def test_methods_at_different_stages_never_share_a_group(self):
        grouped = group_methods(standard_methods())
        for head, names in grouped.items():
            stages = {name.rsplit(" ", 1)[1] for name in names}
            assert len(stages) == 1, f"{head} mixes stages {stages}"


class TestGroupShape:
    def test_a_group_can_be_built_by_hand(self):
        made = LeadHeadGroup(
            head=Row.parse("15738264"),
            order=7,
            heads=(Row.parse("15738264"),),
            places_at_lead_end="12",
        )
        assert made.order == 7
