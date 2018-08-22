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
