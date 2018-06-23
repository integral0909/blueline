import pytest

from blueline.core.stage import (
    MAX_STAGE,
    MIN_STAGE,
    StageError,
    bell_number,
    bell_symbol,
    check_stage,
    is_odd_stage,
    rounds_string,
    stage_from_name,
    stage_name,
)


class TestCheckStage:
    def test_accepts_a_stage_we_can_ring(self):
        assert check_stage(8) == 8

    def test_accepts_both_ends_of_the_range(self):
        assert check_stage(MIN_STAGE) == MIN_STAGE
        assert check_stage(MAX_STAGE) == MAX_STAGE

    def test_refuses_anything_smaller_than_singles(self):
        with pytest.raises(StageError):
            check_stage(2)

    def test_refuses_more_bells_than_we_have_symbols_for(self):
        with pytest.raises(StageError):
            check_stage(MAX_STAGE + 1)


class TestStageName:
    @pytest.mark.parametrize(
        ("stage", "name"),
        [
            (4, "Minimus"),
            (5, "Doubles"),
            (6, "Minor"),
            (7, "Triples"),
            (8, "Major"),
            (9, "Caters"),
            (10, "Royal"),
            (11, "Cinques"),
            (12, "Maximus"),
        ],
    )
    def test_names_the_stages_ringers_name(self, stage, name):
        assert stage_name(stage) == name

    def test_every_stage_in_range_has_a_name(self):
        for stage in range(MIN_STAGE, MAX_STAGE + 1):
            assert stage_name(stage)

    def test_refuses_a_stage_out_of_range(self):
        with pytest.raises(StageError):
            stage_name(99)


class TestOddStages:
    def test_the_odd_stages_have_a_covering_tenor(self):
        assert is_odd_stage(5)
        assert is_odd_stage(7)
        assert is_odd_stage(11)

    def test_the_even_stages_do_not(self):
        assert not is_odd_stage(6)
        assert not is_odd_stage(8)
        assert not is_odd_stage(12)


class TestBellSymbols:
    def test_the_first_nine_are_digits(self):
        assert bell_symbol(1) == "1"
        assert bell_symbol(9) == "9"

    def test_the_tenth_is_nought_rather_than_ten(self):
        assert bell_symbol(10) == "0"

    def test_the_eleventh_and_twelfth_are_letters(self):
        assert bell_symbol(11) == "E"
        assert bell_symbol(12) == "T"

    def test_it_runs_on_past_twelve(self):
        assert bell_symbol(13) == "A"
        assert bell_symbol(16) == "D"

    def test_refuses_a_bell_it_cannot_write(self):
        with pytest.raises(StageError):
            bell_symbol(0)
        with pytest.raises(StageError):
            bell_symbol(MAX_STAGE + 1)

    def test_reads_a_symbol_back_to_a_bell(self):
        assert bell_number("1") == 1
        assert bell_number("0") == 10
        assert bell_number("T") == 12

    def test_reads_a_lower_case_symbol(self):
        assert bell_number("e") == 11
        assert bell_number("t") == 12

    def test_refuses_something_that_is_not_a_bell(self):
        with pytest.raises(StageError):
            bell_number("Z")

    def test_refuses_more_than_one_character(self):
        with pytest.raises(StageError):
            bell_number("12")

    def test_symbols_and_numbers_go_round_trip(self):
        for bell in range(1, MAX_STAGE + 1):
            assert bell_number(bell_symbol(bell)) == bell


class TestRounds:
    def test_rounds_on_eight_is_the_bells_in_order(self):
        assert rounds_string(8) == "12345678"

    def test_rounds_on_twelve_uses_the_letters(self):
        assert rounds_string(12) == "1234567890ET"

    def test_rounds_is_as_long_as_the_stage(self):
        for stage in range(MIN_STAGE, MAX_STAGE + 1):
            assert len(rounds_string(stage)) == stage


class TestStageFromName:
    def test_reads_a_name_back_to_a_stage(self):
        assert stage_from_name("Major") == 8

    def test_does_not_mind_the_case_or_stray_space(self):
        assert stage_from_name("  royal ") == 10

    def test_refuses_a_name_that_is_not_a_stage(self):
        with pytest.raises(StageError):
            stage_from_name("Octuples")

    def test_names_and_stages_go_round_trip(self):
        for stage in range(MIN_STAGE, MAX_STAGE + 1):
            assert stage_from_name(stage_name(stage)) == stage
