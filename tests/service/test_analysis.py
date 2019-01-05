from blueline.service import analysing as service
from blueline.service.results import Reason


class TestLine:
    def test_it_gives_the_treble_line(self, loaded):
        view = service.line(loaded, "Plain Bob Minor", 1).unwrap()
        assert view.places[:4] == (1, 2, 3, 4)
        assert "1 to 6 up" in view.described

    def test_the_grid_marks_the_bell(self, loaded):
        view = service.line(loaded, "Plain Bob Minor", 2).unwrap()
        assert view.grid[0] == "1*3456"

    def test_the_grid_is_a_line_per_row(self, loaded):
        view = service.line(loaded, "Cambridge Surprise Minor", 3).unwrap()
        assert len(view.grid) == 25

    def test_a_bell_that_is_not_there_is_invalid(self, loaded):
        assert service.line(loaded, "Plain Bob Minor", 9).failure.reason is Reason.INVALID

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert service.line(loaded, "Nowhere Surprise Major", 1).failure.reason is Reason.NOT_FOUND


class TestLineWork:
    def test_it_says_what_the_bell_does(self, loaded):
        view = service.line(loaded, "Plain Bob Minor", 1).unwrap()
        assert set(view.work) == {"leads", "lies", "dodges", "places"}

    def test_the_treble_in_plain_bob_does_not_dodge(self, loaded):
        view = service.line(loaded, "Plain Bob Minor", 1).unwrap()
        assert view.work["dodges"] == []

    def test_the_treble_in_cambridge_dodges_six_times(self, loaded):
        view = service.line(loaded, "Cambridge Surprise Minor", 1).unwrap()
        assert len(view.work["dodges"]) == 6

    def test_the_treble_leads_twice_in_a_plain_lead(self, loaded):
        view = service.line(loaded, "Plain Bob Minor", 1).unwrap()
        assert len(view.work["leads"]) == 2

    def test_every_working_bell_does_something(self, loaded):
        for bell in range(2, 7):
            view = service.line(loaded, "Cambridge Surprise Minor", bell).unwrap()
            assert any(view.work.values())


class TestFalseness:
    def test_it_gives_the_worst_first(self, loaded):
        found = service.falseness(loaded, "Cambridge Surprise Major").unwrap()
        assert found[0].clashes >= found[-1].clashes

    def test_it_caps_the_list(self, loaded):
        assert len(service.falseness(loaded, "Cambridge Surprise Major", limit=5).unwrap()) == 5

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert (
            service.falseness(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND
        )


class TestPlaceBells:
    def test_plain_bob_major_runs_two_four_six_eight_seven_five_three(self, loaded):
        assert service.place_bells(loaded, "Plain Bob Major").unwrap() == [2, 4, 6, 8, 7, 5, 3]

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert (
            service.place_bells(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND
        )


class TestHandbells:
    def test_it_gives_a_view_per_pair(self, loaded):
        views = service.handbells(loaded, "Cambridge Surprise Major").unwrap()
        assert [view.pair for view in views] == ["1-2", "3-4", "5-6", "7-8"]

    def test_minor_pairs_up_three_ways(self, loaded):
        views = service.handbells(loaded, "Cambridge Surprise Minor").unwrap()
        assert len(views) == 3

    def test_an_odd_stage_leaves_the_tenor_out(self, loaded):
        views = service.handbells(loaded, "Grandsire Triples").unwrap()
        assert [view.pair for view in views] == ["1-2", "3-4", "5-6"]

    def test_every_pair_has_its_bells(self, loaded):
        views = service.handbells(loaded, "Cambridge Surprise Major").unwrap()
        assert views[0].bells == (1, 2)

    def test_a_pair_crosses_somewhere(self, loaded):
        views = service.handbells(loaded, "Cambridge Surprise Major").unwrap()
        assert any(view.crossings for view in views)

    def test_a_pair_is_together_somewhere(self, loaded):
        views = service.handbells(loaded, "Cambridge Surprise Major").unwrap()
        assert all(view.together for view in views)

    def test_the_summary_counts_both(self, loaded):
        view = service.handbells(loaded, "Cambridge Surprise Major").unwrap()[0]
        assert "crossings" in view.summary()
        assert "together" in view.summary()

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert (
            service.handbells(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND
        )


class TestVariations:
    def test_it_reverses_a_method(self, loaded):
        report = service.vary(loaded, "Cambridge Surprise Minor", "reverse").unwrap()
        assert report.title.name == "Reverse Cambridge"

    def test_it_turns_a_method_over(self, loaded):
        report = service.vary(loaded, "Plain Bob Minor", "mirror").unwrap()
        assert report.notation.endswith("56")

    def test_it_doubles_a_method(self, loaded):
        assert service.vary(loaded, "Plain Bob Minor", "double").ok

    def test_a_name_can_be_given(self, loaded):
        report = service.vary(loaded, "Cambridge Surprise Minor", "mirror", name="Primrose")
        assert report.unwrap().title.name == "Primrose"

    def test_nothing_is_stored(self, loaded):
        before = loaded.count()
        service.vary(loaded, "Cambridge Surprise Minor", "reverse")
        assert loaded.count() == before

    def test_a_variation_it_does_not_know_is_invalid(self, loaded):
        result = service.vary(loaded, "Plain Bob Minor", "upside down")
        assert result.failure.reason is Reason.INVALID
        assert "reverse" in result.failure.detail

    def test_the_kind_ignores_case_and_space(self, loaded):
        assert service.vary(loaded, "Plain Bob Minor", "  REVERSE ").ok

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = service.vary(loaded, "Nowhere Surprise Major", "reverse")
        assert result.failure.reason is Reason.NOT_FOUND


class TestRelate:
    def test_a_method_is_the_same_as_itself(self, loaded):
        relation = service.relate(loaded, "Plain Bob Minor", "Plain Bob Minor").unwrap()
        assert relation == "the same method"

    def test_two_unrelated_methods_are_not_related(self, loaded):
        relation = service.relate(loaded, "Plain Bob Minor", "Cambridge Surprise Minor")
        assert relation.unwrap() == "not related"

    def test_two_stages_are_not_related(self, loaded):
        relation = service.relate(loaded, "Plain Bob Minor", "Plain Bob Major")
        assert relation.unwrap() == "not related"

    def test_a_first_method_that_is_not_there_is_not_found(self, loaded):
        result = service.relate(loaded, "Nowhere Surprise Major", "Plain Bob Minor")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_a_second_method_that_is_not_there_is_not_found(self, loaded):
        result = service.relate(loaded, "Plain Bob Minor", "Nowhere Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND


class TestChangeLeadEnd:
    def test_it_swaps_the_lead_end(self, loaded):
        report = service.change_lead_end(loaded, "Cambridge Surprise Minor", "16").unwrap()
        assert report.notation.endswith("16")

    def test_the_result_still_rings_a_true_course(self, loaded):
        report = service.change_lead_end(loaded, "Cambridge Surprise Minor", "16").unwrap()
        assert report.course_is_true

    def test_a_name_can_be_given(self, loaded):
        report = service.change_lead_end(loaded, "Cambridge Surprise Minor", "16", name="Primrose")
        assert report.unwrap().title.name == "Primrose"

    def test_a_change_that_does_not_work_is_invalid(self, loaded):
        result = service.change_lead_end(loaded, "Plain Bob Minor", "13")
        assert result.failure.reason is Reason.INVALID

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = service.change_lead_end(loaded, "Nowhere Surprise Major", "16")
        assert result.failure.reason is Reason.NOT_FOUND

    def test_nothing_is_stored(self, loaded):
        before = loaded.count()
        service.change_lead_end(loaded, "Cambridge Surprise Minor", "16")
        assert loaded.count() == before


class TestLeadHeadGroups:
    def test_it_groups_the_stored_methods(self, loaded):
        views = service.lead_head_groups(loaded, stage=8).unwrap()
        together = next(view for view in views if len(view.titles) > 1)
        assert together.titles == (
            "Cambridge 8",
            "Lincolnshire 8",
            "Superlative 8",
            "Yorkshire 8",
        )

    def test_bristol_is_on_its_own(self, loaded):
        views = service.lead_head_groups(loaded, stage=8).unwrap()
        alone = [view for view in views if view.titles == ("Bristol 8",)]
        assert alone

    def test_every_method_lands_in_a_group(self, loaded):
        views = service.lead_head_groups(loaded, stage=8).unwrap()
        total = sum(len(view.titles) for view in views)
        assert total == len(loaded.search(stage=8))

    def test_it_carries_the_lead_end_places(self, loaded):
        views = service.lead_head_groups(loaded, stage=8).unwrap()
        assert {view.places_at_lead_end for view in views} >= {"12", "18"}

    def test_it_carries_the_course_length(self, loaded):
        views = service.lead_head_groups(loaded, stage=8).unwrap()
        assert all(view.order == 7 for view in views)

    def test_the_summary_counts_the_methods(self, loaded):
        views = service.lead_head_groups(loaded, stage=8).unwrap()
        assert "methods" in views[0].summary() or "method" in views[0].summary()

    def test_without_a_stage_it_covers_everything(self, loaded):
        views = service.lead_head_groups(loaded).unwrap()
        total = sum(len(view.titles) for view in views)
        assert total == loaded.count()

    def test_an_empty_library_has_no_groups(self, repository):
        assert service.lead_head_groups(repository).unwrap() == []


class TestTakesTheSameCompositions:
    def test_it_finds_the_others_in_the_group(self, loaded):
        found = service.takes_the_same_compositions(loaded, "Cambridge Surprise Major").unwrap()
        assert found == ["Lincolnshire 8", "Superlative 8", "Yorkshire 8"]

    def test_it_leaves_the_method_itself_out(self, loaded):
        found = service.takes_the_same_compositions(loaded, "Cambridge Surprise Major").unwrap()
        assert "Cambridge 8" not in found

    def test_a_method_on_its_own_finds_nothing(self, loaded):
        assert service.takes_the_same_compositions(loaded, "Bristol Surprise Major").unwrap() == []

    def test_it_does_not_cross_stages(self, loaded):
        found = service.takes_the_same_compositions(loaded, "Cambridge Surprise Minor").unwrap()
        assert all(title.endswith(" 6") for title in found)

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = service.takes_the_same_compositions(loaded, "Nowhere Surprise Major")
        assert result.failure.reason is Reason.NOT_FOUND
