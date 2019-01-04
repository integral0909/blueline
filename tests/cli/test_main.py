from blueline.cli.main import EXIT_FOR, app
from blueline.service.results import Reason

CAMBRIDGE = "x38x14x1258x36x14x58x16x78,12"


class TestExitCodes:
    def test_every_reason_has_a_code(self):
        for reason in Reason:
            assert reason in EXIT_FOR

    def test_they_are_all_different(self):
        assert len(set(EXIT_FOR.values())) == len(EXIT_FOR)

    def test_none_of_them_mean_success(self):
        assert 0 not in EXIT_FOR.values()


class TestAnalyse:
    def test_it_analyses_notation(self, runner, library):
        result = runner.invoke(app, ["analyse", CAMBRIDGE, "-s", "8", "-n", "Cambridge"])
        assert result.exit_code == 0
        assert "Cambridge Surprise Major" in result.stdout

    def test_it_shows_the_shape(self, runner, library):
        result = runner.invoke(app, ["analyse", CAMBRIDGE, "-s", "8", "-n", "Cambridge"])
        assert "224" in result.stdout

    def test_bad_notation_exits_with_the_invalid_code(self, runner, library):
        result = runner.invoke(app, ["analyse", "x1x1", "-s", "5"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_it_stores_nothing(self, runner, library):
        runner.invoke(app, ["analyse", CAMBRIDGE, "-s", "8", "-n", "Cambridge"])
        listed = runner.invoke(app, ["list"])
        assert "0 methods" in listed.stdout


class TestSeed:
    def test_it_loads_the_standard_set(self, runner, library):
        result = runner.invoke(app, ["seed"])
        assert result.exit_code == 0
        assert "15 added" in result.stdout

    def test_running_it_twice_adds_nothing(self, runner, library):
        runner.invoke(app, ["seed"])
        again = runner.invoke(app, ["seed"])
        assert "0 added" in again.stdout


class TestList:
    def test_it_lists_what_is_there(self, runner, seeded):
        result = runner.invoke(app, ["list"])
        assert "15 methods" in result.stdout

    def test_it_filters_by_name(self, runner, seeded):
        result = runner.invoke(app, ["list", "-n", "cambridge"])
        assert "2 methods" in result.stdout

    def test_it_filters_by_stage(self, runner, seeded):
        # The table truncates titles to fit eighty columns, so the count is
        # what this can honestly assert on.
        result = runner.invoke(app, ["list", "-s", "8"])
        assert "7 methods" in result.stdout

    def test_an_empty_library_says_nothing_is_there(self, runner, library):
        assert "0 methods" in runner.invoke(app, ["list"]).stdout


class TestShow:
    def test_it_shows_a_stored_method(self, runner, seeded):
        result = runner.invoke(app, ["show", "Plain Bob Minor"])
        assert result.exit_code == 0
        assert "135264" in result.stdout

    def test_something_missing_exits_with_the_not_found_code(self, runner, seeded):
        result = runner.invoke(app, ["show", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestAddAndRemove:
    def test_a_method_can_be_added(self, runner, library):
        result = runner.invoke(app, ["add", "x16x16x16,12", "-s", "6", "-n", "Plain"])
        assert result.exit_code == 0
        assert "stored Plain Bob Minor" in result.stdout

    def test_it_is_there_afterwards(self, runner, library):
        runner.invoke(app, ["add", "x16x16x16,12", "-s", "6", "-n", "Plain"])
        assert "1 methods" in runner.invoke(app, ["list"]).stdout

    def test_adding_it_twice_exits_with_the_conflict_code(self, runner, library):
        runner.invoke(app, ["add", "x16x16x16,12", "-s", "6", "-n", "Plain"])
        again = runner.invoke(app, ["add", "x16x16x16,12", "-s", "6", "-n", "Plain"])
        assert again.exit_code == EXIT_FOR[Reason.ALREADY_EXISTS]

    def test_a_method_can_be_removed(self, runner, seeded):
        result = runner.invoke(app, ["remove", "Plain Bob Minor"])
        assert result.exit_code == 0
        assert "removed Plain Bob Minor" in result.stdout

    def test_removing_something_missing_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["remove", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestLine:
    def test_it_draws_a_line(self, runner, seeded):
        result = runner.invoke(app, ["line", "Plain Bob Minor", "2"])
        assert result.exit_code == 0
        assert "1*3456" in result.stdout

    def test_it_describes_the_work(self, runner, seeded):
        result = runner.invoke(app, ["line", "Plain Bob Minor", "1"])
        assert "1 to 6 up" in result.stdout

    def test_a_bell_that_is_not_there_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["line", "Plain Bob Minor", "9"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]


class TestFalseness:
    def test_it_lists_false_course_heads(self, runner, seeded):
        result = runner.invoke(app, ["falseness", "Cambridge Surprise Major", "-l", "3"])
        assert result.exit_code == 0
        assert "false course heads" in result.stdout


class TestPlaceBells:
    def test_plain_bob_major_runs_two_four_six_eight_seven_five_three(self, runner, seeded):
        result = runner.invoke(app, ["place-bells", "Plain Bob Major"])
        assert "2468753" in result.stdout


class TestProve:
    def test_the_three_bob_touch(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "---"])
        assert result.exit_code == 0
        assert "36" in result.stdout

    def test_it_says_a_touch_comes_round(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "---"])
        assert "comes round" in result.stdout

    def test_the_classic_hundred_and_twenty_is_an_extent(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Doubles", "ppp-", "-t", "3"])
        assert "extent" in result.stdout

    def test_a_touch_that_does_not_come_round_says_where_it_got_to(self, runner, seeded):
        # Written bb rather than --, because a bare -- is the shell's own end
        # of options marker and never reaches the command. That is the whole
        # reason b is accepted for a bob.
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "bb"])
        assert result.exit_code == 0
        assert "no," in result.stdout

    def test_a_calling_of_dashes_gets_through(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "---"])
        assert result.exit_code == 0
        assert "36" in result.stdout

    def test_b_and_a_dash_ring_the_same_touch(self, runner, seeded):
        with_dashes = runner.invoke(app, ["prove", "Plain Bob Minor", "---"])
        with_bees = runner.invoke(app, ["prove", "Plain Bob Minor", "bbb"])
        assert with_dashes.stdout == with_bees.stdout

    def test_a_calling_it_cannot_read_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "zzz"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Nowhere Surprise Major", "-"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestCourse:
    def test_it_reports_the_plain_course(self, runner, seeded):
        result = runner.invoke(app, ["course", "Cambridge Surprise Minor"])
        assert result.exit_code == 0
        assert "120" in result.stdout

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["course", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestSearch:
    def test_it_finds_callings(self, runner, seeded):
        result = runner.invoke(app, ["search", "Plain Bob Minor", "-l", "3"])
        assert result.exit_code == 0
        assert "ppppp" in result.stdout

    def test_it_says_whether_it_finished(self, runner, seeded):
        result = runner.invoke(app, ["search", "Plain Bob Minor", "-l", "3"])
        assert "callings" in result.stdout

    def test_the_calls_can_be_restricted(self, runner, seeded):
        result = runner.invoke(app, ["search", "Plain Bob Minor", "--calls", "p", "-l", "2"])
        assert result.exit_code == 0
        assert "ppppp" in result.stdout

    def test_a_call_it_does_not_have_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["search", "Plain Bob Minor", "--calls", "pz"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["search", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestImportExport:
    def test_it_exports_json_to_the_screen(self, runner, seeded):
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 0
        assert '"format"' in result.stdout

    def test_it_exports_the_line_format(self, runner, seeded):
        result = runner.invoke(app, ["export", "-f", "lines"])
        assert result.exit_code == 0
        assert "Cambridge" in result.stdout

    def test_it_exports_one_stage(self, runner, seeded, tmp_path):
        out = tmp_path / "six.txt"
        result = runner.invoke(app, ["export", str(out), "-f", "lines", "-s", "6"])
        assert result.exit_code == 0
        body = [line for line in out.read_text().splitlines() if not line.startswith("#")]
        assert all(line.split(",")[1].strip() == "6" for line in body)

    def test_it_writes_to_a_file(self, runner, seeded, tmp_path):
        out = tmp_path / "all.json"
        result = runner.invoke(app, ["export", str(out)])
        assert result.exit_code == 0
        assert "wrote" in result.stdout
        assert out.exists()

    def test_a_format_it_does_not_know_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["export", "-f", "xml"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_it_imports_a_file(self, runner, library, tmp_path):
        source = tmp_path / "few.txt"
        source.write_text("Plain, 6, x16x16x16,12\nCambridge, 6, x36x14x12x36x14x56,12\n")
        result = runner.invoke(app, ["import", str(source)])
        assert result.exit_code == 0
        assert "2 added" in result.stdout

    def test_the_methods_are_there_afterwards(self, runner, library, tmp_path):
        source = tmp_path / "one.txt"
        source.write_text("Plain, 6, x16x16x16,12\n")
        runner.invoke(app, ["import", str(source)])
        assert "1 methods" in runner.invoke(app, ["list"]).stdout

    def test_a_bad_line_is_reported_and_the_rest_go_in(self, runner, library, tmp_path):
        source = tmp_path / "mixed.txt"
        source.write_text("Plain, 6, x16x16x16,12\nrubbish\n")
        result = runner.invoke(app, ["import", str(source)])
        assert "1 added" in result.stdout
        assert "could not be read" in result.stdout

    def test_a_file_that_is_not_there_is_refused_by_the_parser(self, runner, library, tmp_path):
        result = runner.invoke(app, ["import", str(tmp_path / "nothing.txt")])
        assert result.exit_code != 0

    def test_a_round_trip_through_a_file_keeps_everything(self, runner, seeded, tmp_path):
        out = tmp_path / "all.json"
        runner.invoke(app, ["export", str(out)])
        runner.invoke(app, ["remove", "Plain Bob Minor"])
        result = runner.invoke(app, ["import", str(out)])
        assert "1 added" in result.stdout


class TestSplice:
    GROUP = [
        "-m",
        "Cambridge Surprise Major",
        "-m",
        "Yorkshire Surprise Major",
        "-m",
        "Superlative Surprise Major",
        "-m",
        "Lincolnshire Surprise Major",
    ]

    def test_seven_leads_come_round_true(self, runner, seeded):
        result = runner.invoke(app, ["splice", "CYSLCYS", *self.GROUP])
        assert result.exit_code == 0
        assert "224" in result.stdout

    def test_it_lists_the_methods_used(self, runner, seeded):
        result = runner.invoke(app, ["splice", "CYC", *self.GROUP])
        assert "Cambridge" in result.stdout
        assert "Yorkshire" in result.stdout

    def test_a_calling_can_be_given(self, runner, seeded):
        result = runner.invoke(app, ["splice", "CYSL", *self.GROUP, "-c", "p-pp"])
        assert result.exit_code == 0
        assert "p-pp" in result.stdout

    def test_methods_that_do_not_splice_exit_invalid(self, runner, seeded):
        args = [*self.GROUP, "-m", "Bristol Surprise Major"]
        result = runner.invoke(app, ["splice", "CYSLB", *args])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["splice", "N", "-m", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestLineWork:
    def test_it_counts_the_work(self, runner, seeded):
        result = runner.invoke(app, ["line", "Cambridge Surprise Minor", "1"])
        assert result.exit_code == 0
        assert "dodges" in result.stdout

    def test_a_plain_treble_has_no_dodges_to_report(self, runner, seeded):
        result = runner.invoke(app, ["line", "Plain Bob Minor", "1"])
        assert "dodges" not in result.stdout


class TestLineWorkDetail:
    def test_it_names_each_kind_of_work_it_found(self, runner, seeded):
        result = runner.invoke(app, ["line", "Cambridge Surprise Minor", "1"])
        for word in ("leads", "lies", "dodges"):
            assert word in result.stdout

    def test_a_bell_with_no_work_of_a_kind_does_not_mention_it(self, runner, seeded):
        result = runner.invoke(app, ["line", "Plain Bob Minor", "1"])
        assert "dodges" not in result.stdout

    def test_the_counts_match_what_the_service_says(self, runner, seeded):
        from blueline.api import deps
        from blueline.db.repositories import MethodRepository
        from blueline.service import analysis as service

        with deps.get_factory()() as session:
            view = service.line(MethodRepository(session), "Cambridge Surprise Minor", 1).unwrap()
        result = runner.invoke(app, ["line", "Cambridge Surprise Minor", "1"])
        assert f"{len(view.work['dodges'])} dodges" in result.stdout


class TestEarlyRounds:
    def test_a_touch_that_comes_round_early_says_so(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "---", "-t", "2"])
        assert result.exit_code == 0
        assert "comes round early" in result.stdout

    def test_it_names_the_lead(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "---", "-t", "2"])
        assert "lead 3" in result.stdout

    def test_a_touch_that_runs_to_the_end_says_nothing(self, runner, seeded):
        result = runner.invoke(app, ["prove", "Plain Bob Minor", "---"])
        assert "comes round early" not in result.stdout

    def test_a_splice_reports_it_as_well(self, runner, seeded):
        args = [
            "-m",
            "Cambridge Surprise Major",
            "-m",
            "Yorkshire Surprise Major",
        ]
        result = runner.invoke(app, ["splice", "CYCYCYCCYCYCYC", *args])
        assert result.exit_code == 0
        assert "comes round early" in result.stdout


class TestSpliceLeadLength:
    def test_a_splice_of_one_method_matches_proving_it(self, runner, seeded):
        spliced = runner.invoke(app, ["splice", "CCCCCCC", "-m", "Cambridge Surprise Major"])
        assert spliced.exit_code == 0
        assert "224" in spliced.stdout


class TestPerformances:
    EIGHT = [
        "-r",
        "Ann",
        "-r",
        "Bob",
        "-r",
        "Cara",
        "-r",
        "Dan",
        "-r",
        "Eve",
        "-r",
        "Finn",
        "-r",
        "Gus",
        "-r",
        "Hana",
    ]

    def _rang(self, runner, **over):
        args = [
            "rang",
            over.get("title", "Cambridge Surprise Major"),
            *self.EIGHT,
            "-s",
            str(over.get("stage", 8)),
            "-l",
            str(over.get("length", 5024)),
            "--on",
            over.get("on", "2023-03-18"),
            "-p",
            over.get("place", "St Andrew, Marchgate"),
            "-c",
            over.get("conductor", "Hana"),
        ]
        return runner.invoke(app, args)

    def test_it_writes_one_up(self, runner, seeded):
        result = self._rang(runner)
        assert result.exit_code == 0
        assert "St Andrew, Marchgate" in result.stdout
        assert "18 March 2023" in result.stdout

    def test_the_board_lists_the_band(self, runner, seeded):
        result = self._rang(runner)
        assert "1 Ann" in result.stdout
        assert "8 Hana (c)" in result.stdout

    def test_it_is_listed_afterwards(self, runner, seeded):
        self._rang(runner)
        listed = runner.invoke(app, ["rung"])
        assert "1 performances" in listed.stdout

    def test_a_bad_date_exits_invalid(self, runner, seeded):
        result = self._rang(runner, on="last tuesday")
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_a_band_too_small_for_the_stage_exits_invalid(self, runner, seeded):
        result = self._rang(runner, stage=12)
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_listing_filters_by_place(self, runner, seeded):
        self._rang(runner)
        self._rang(runner, place="St Mary, Ashcombe")
        found = runner.invoke(app, ["rung", "-p", "Ashcombe"])
        assert "1 performances" in found.stdout

    def test_listing_filters_by_ringer(self, runner, seeded):
        self._rang(runner)
        assert "1 performances" in runner.invoke(app, ["rung", "-r", "Hana"]).stdout

    def test_an_empty_store_lists_nothing(self, runner, seeded):
        assert "0 performances" in runner.invoke(app, ["rung"]).stdout


class TestTotals:
    def test_an_empty_store_says_nothing_was_rung(self, runner, seeded):
        result = runner.invoke(app, ["totals"])
        assert result.exit_code == 0
        assert "nothing rung" in result.stdout

    def test_it_counts_what_is_there(self, runner, seeded):
        TestPerformances()._rang(runner)
        result = runner.invoke(app, ["totals"])
        assert "performances" in result.stdout
        assert "5024" in result.stdout

    def test_it_lists_the_methods(self, runner, seeded):
        TestPerformances()._rang(runner)
        result = runner.invoke(app, ["totals"])
        assert "methods" in result.stdout

    def test_it_lists_the_ringers(self, runner, seeded):
        TestPerformances()._rang(runner)
        result = runner.invoke(app, ["totals"])
        assert "ringers" in result.stdout
        assert "Ann" in result.stdout

    def test_it_can_be_narrowed_to_a_place(self, runner, seeded):
        TestPerformances()._rang(runner)
        TestPerformances()._rang(runner, place="St Mary, Ashcombe")
        result = runner.invoke(app, ["totals", "-p", "Ashcombe"])
        assert result.exit_code == 0

    def test_an_empty_store_lists_no_leaderboards(self, runner, seeded):
        result = runner.invoke(app, ["totals"])
        assert "Ann" not in result.stdout


class TestHandbells:
    def test_it_lists_the_pairs(self, runner, seeded):
        result = runner.invoke(app, ["handbells", "Cambridge Surprise Major"])
        assert result.exit_code == 0
        for pair in ("1-2", "3-4", "5-6", "7-8"):
            assert pair in result.stdout

    def test_it_counts_the_crossings(self, runner, seeded):
        result = runner.invoke(app, ["handbells", "Cambridge Surprise Major"])
        assert "crossings" in result.stdout

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["handbells", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestForLength:
    def test_it_finds_a_touch_at_the_length(self, runner, seeded):
        result = runner.invoke(app, ["for-length", "Plain Bob Doubles", "120", "-l", "1"])
        assert result.exit_code == 0
        assert "120" in result.stdout

    def test_a_length_past_the_extent_says_why(self, runner, seeded):
        result = runner.invoke(app, ["for-length", "Plain Bob Minor", "1260"])
        assert result.exit_code == 0
        assert "cannot be rung" in result.stdout
        assert "720" in result.stdout

    def test_a_length_that_does_not_divide_says_why(self, runner, seeded):
        result = runner.invoke(app, ["for-length", "Plain Bob Major", "1250"])
        assert "does not divide" in result.stdout

    def test_a_tolerance_can_bring_it_into_range(self, runner, seeded):
        result = runner.invoke(app, ["for-length", "Plain Bob Major", "1250", "-g", "2", "-l", "1"])
        assert result.exit_code == 0
        assert "cannot be rung" not in result.stdout

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["for-length", "Nowhere Surprise Major", "120"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestVariations:
    def test_it_reverses_a_method(self, runner, seeded):
        result = runner.invoke(app, ["vary", "Cambridge Surprise Minor", "reverse"])
        assert result.exit_code == 0
        assert "Reverse Cambridge" in result.stdout

    def test_a_variation_it_does_not_know_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["vary", "Plain Bob Minor", "sideways"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_it_swaps_a_lead_end(self, runner, seeded):
        result = runner.invoke(app, ["lead-end", "Cambridge Surprise Minor", "16"])
        assert result.exit_code == 0
        assert "16" in result.stdout

    def test_it_relates_two_methods(self, runner, seeded):
        result = runner.invoke(app, ["relation", "Plain Bob Minor", "Plain Bob Minor"])
        assert "the same method" in result.stdout

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["vary", "Nowhere Surprise Major", "reverse"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestLeadHeadGroups:
    def test_it_lists_the_groups(self, runner, seeded):
        result = runner.invoke(app, ["groups", "-s", "8"])
        assert result.exit_code == 0
        assert "lead head groups" in result.stdout

    def test_it_shows_the_lead_end_places(self, runner, seeded):
        result = runner.invoke(app, ["groups", "-s", "8"])
        assert "12" in result.stdout
        assert "18" in result.stdout

    def test_an_empty_library_has_no_groups(self, runner, library):
        assert "0 lead head groups" in runner.invoke(app, ["groups"]).stdout

    def test_it_finds_what_shares_a_composition(self, runner, seeded):
        result = runner.invoke(app, ["same-compositions", "Cambridge Surprise Major"])
        assert result.exit_code == 0
        assert "Yorkshire 8" in result.stdout

    def test_a_method_on_its_own_lists_nothing(self, runner, seeded):
        result = runner.invoke(app, ["same-compositions", "Bristol Surprise Major"])
        assert result.exit_code == 0
        assert result.stdout.strip() == ""

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["same-compositions", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestCallingPositions:
    def test_it_names_the_positions(self, runner, seeded):
        result = runner.invoke(app, ["positions", "Plain Bob Major"])
        assert result.exit_code == 0
        assert "Home" in result.stdout
        assert "Wrong" in result.stdout

    def test_it_proves_a_touch_called_by_position(self, runner, seeded):
        result = runner.invoke(app, ["call", "Plain Bob Major", "Wrong", "Home", "Home"])
        assert result.exit_code == 0
        assert "14" in result.stdout

    def test_calling_nothing_is_the_plain_course(self, runner, seeded):
        result = runner.invoke(app, ["call", "Plain Bob Major"])
        assert result.exit_code == 0
        assert "112" in result.stdout

    def test_a_position_it_does_not_know_exits_invalid(self, runner, seeded):
        result = runner.invoke(app, ["call", "Plain Bob Major", "Sideways"])
        assert result.exit_code == EXIT_FOR[Reason.INVALID]

    def test_a_method_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["positions", "Nowhere Surprise Major"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestBoard:
    def test_it_lays_a_performance_out(self, runner, seeded):
        TestPerformances()._rang(runner)
        result = runner.invoke(app, ["board", "1"])
        assert result.exit_code == 0
        assert "St Andrew, Marchgate" in result.stdout

    def test_it_lists_the_band(self, runner, seeded):
        TestPerformances()._rang(runner)
        assert "Hana (c)" in runner.invoke(app, ["board", "1"]).stdout

    def test_one_that_is_not_there_exits_not_found(self, runner, seeded):
        result = runner.invoke(app, ["board", "999"])
        assert result.exit_code == EXIT_FOR[Reason.NOT_FOUND]


class TestMusical:
    def test_it_ranks_what_it_finds(self, runner, seeded) -> None:
        result = runner.invoke(app, ["musical", "Plain Bob Minor", "--wide", "30", "-n", "5"])
        assert result.exit_code == 0
        assert "callings tried" in result.stdout

    def test_a_method_nobody_has_stored(self, runner, seeded) -> None:
        assert runner.invoke(app, ["musical", "Weasel Major"]).exit_code != 0


class TestCard:
    def test_a_printed_calling_is_rung_through(self, runner, seeded) -> None:
        result = runner.invoke(app, ["card", "Plain Bob Major", "W H"])
        assert result.exit_code == 0
        assert "W H" in result.stdout

    def test_it_says_what_it_read(self, runner, seeded) -> None:
        result = runner.invoke(app, ["card", "Plain Bob Major", "W H H"])
        assert "W 2H" in result.stdout

    def test_something_that_is_not_a_position(self, runner, seeded) -> None:
        assert runner.invoke(app, ["card", "Plain Bob Major", "W ?? H"]).exit_code != 0

    def test_a_method_nobody_has_stored(self, runner, seeded) -> None:
        assert runner.invoke(app, ["card", "Weasel Major", "W H"]).exit_code != 0
