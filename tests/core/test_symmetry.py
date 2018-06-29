import pytest

from blueline.core.method import Method
from blueline.core.notation import format_notation, parse_change, parse_notation
from blueline.core.symmetry import (
    describe_symmetry,
    half_lead_change,
    is_double,
    is_palindromic,
    is_rotational,
    mirror_change,
    palindromic_axes,
    reflects_about_change,
    reflects_about_gap,
    rotate,
    symmetric_notation,
)

PLAIN_BOB_MINOR = list(parse_notation("x16x16x16,12", 6))
CAMBRIDGE_MINOR = list(parse_notation("x36x14x12x36x14x56,12", 6))
GRANDSIRE_DOUBLES = list(parse_notation("3.1.5.1.5.1.5.1.5.1", 5))
DOUBLE_NORWICH = list(parse_notation("x14x36x58x18,18", 8))
STEDMAN_DOUBLES = list(parse_notation("3.1.5.3.1.3.1.3.5.1", 5))


class TestMirror:
    def test_turns_seconds_into_the_back_place(self):
        assert str(mirror_change(parse_change("12", 8))) == "78"

    def test_a_cross_mirrors_to_itself(self):
        assert mirror_change(parse_change("x", 8)).is_cross

    def test_a_change_in_the_middle_mirrors_to_itself(self):
        assert mirror_change(parse_change("45", 8)) == parse_change("45", 8)

    def test_mirroring_twice_gives_it_back(self):
        change = parse_change("18", 8)
        assert mirror_change(mirror_change(change)) == change


class TestRotate:
    def test_rotating_by_nothing_leaves_it_alone(self):
        assert rotate(PLAIN_BOB_MINOR, 0) == PLAIN_BOB_MINOR

    def test_rotating_by_the_length_comes_back_round(self):
        assert rotate(PLAIN_BOB_MINOR, len(PLAIN_BOB_MINOR)) == PLAIN_BOB_MINOR

    def test_rotating_moves_the_first_change_to_the_end(self):
        turned = rotate(PLAIN_BOB_MINOR, 1)
        assert turned[-1] == PLAIN_BOB_MINOR[0]

    def test_copes_with_an_empty_lead(self):
        assert rotate([], 3) == []


class TestReflection:
    def test_plain_bob_reflects_about_its_half_lead_change(self):
        assert reflects_about_change(PLAIN_BOB_MINOR, 5)

    def test_plain_bob_reflects_about_its_lead_end_change(self):
        assert reflects_about_change(PLAIN_BOB_MINOR, 11)

    def test_plain_bob_does_not_reflect_anywhere_else(self):
        assert not reflects_about_change(PLAIN_BOB_MINOR, 0)

    def test_grandsire_reflects_about_the_treble_lead(self):
        assert reflects_about_change(GRANDSIRE_DOUBLES, 0)

    def test_an_empty_lead_reflects_about_nothing(self):
        assert not reflects_about_change([], 0)
        assert not reflects_about_gap([], 0)


class TestAxes:
    def test_plain_bob_has_two_axes(self):
        assert palindromic_axes(PLAIN_BOB_MINOR) == (10, 22)

    def test_cambridge_has_two_axes(self):
        assert len(palindromic_axes(CAMBRIDGE_MINOR)) == 2

    def test_an_even_axis_runs_through_a_change(self):
        assert all(axis % 2 == 0 for axis in palindromic_axes(PLAIN_BOB_MINOR))

    def test_the_usual_methods_are_palindromic(self):
        for changes in (PLAIN_BOB_MINOR, CAMBRIDGE_MINOR, GRANDSIRE_DOUBLES, STEDMAN_DOUBLES):
            assert is_palindromic(changes)


class TestRotational:
    def test_double_norwich_is_rotational(self):
        assert is_rotational(DOUBLE_NORWICH)

    def test_plain_bob_is_not(self):
        assert not is_rotational(PLAIN_BOB_MINOR)

    def test_a_lead_of_odd_length_cannot_be_rotational(self):
        assert not is_rotational(PLAIN_BOB_MINOR[:-1])

    def test_an_empty_lead_is_not_rotational(self):
        assert not is_rotational([])


class TestDouble:
    def test_double_norwich_earns_its_name(self):
        assert is_double(DOUBLE_NORWICH)
        assert describe_symmetry(DOUBLE_NORWICH) == "double"

    def test_plain_bob_is_only_palindromic(self):
        assert not is_double(PLAIN_BOB_MINOR)
        assert describe_symmetry(PLAIN_BOB_MINOR) == "palindromic"

    def test_something_with_no_symmetry_says_so(self):
        odd = list(parse_notation("x18x16x12x14", 8))
        assert describe_symmetry(odd) in {"asymmetric", "palindromic", "rotational"}


class TestHalfLead:
    def test_names_the_change_at_the_half_lead(self):
        assert str(half_lead_change(PLAIN_BOB_MINOR)) == "16"

    def test_cambridge_makes_fifths_and_sixths_at_the_half_lead(self):
        assert str(half_lead_change(CAMBRIDGE_MINOR)) == "56"

    def test_there_is_none_for_an_odd_length_lead(self):
        assert half_lead_change(GRANDSIRE_DOUBLES[:-1]) is None

    def test_there_is_none_for_an_empty_lead(self):
        assert half_lead_change([]) is None


class TestSymmetricNotation:
    def test_plain_bob_writes_back_the_way_it_came(self):
        split = symmetric_notation(PLAIN_BOB_MINOR)
        assert split is not None
        half, lead_end = split
        assert f"{format_notation(half)},{format_notation(lead_end)}" == "x16x16x16,12"

    def test_cambridge_writes_back_the_way_it_came(self):
        split = symmetric_notation(CAMBRIDGE_MINOR)
        assert split is not None
        half, lead_end = split
        text = f"{format_notation(half)},{format_notation(lead_end)}"
        assert text == "x36x14x12x36x14x56,12"

    def test_the_split_expands_to_the_same_lead(self):
        split = symmetric_notation(CAMBRIDGE_MINOR)
        assert split is not None
        half, lead_end = split
        text = f"{format_notation(half)},{format_notation(lead_end)}"
        assert list(parse_notation(text, 6)) == CAMBRIDGE_MINOR

    def test_grandsire_will_not_split_that_way(self):
        # Its symmetry is about the treble's lead, not the lead end, so there
        # is no honest half and comma to write.
        assert symmetric_notation(GRANDSIRE_DOUBLES) is None

    def test_refuses_a_lead_too_short_to_split(self):
        assert symmetric_notation(PLAIN_BOB_MINOR[:1]) is None


class TestAgainstRealMethods:
    @pytest.mark.parametrize(
        ("stage", "notation", "expected"),
        [
            (6, "x16x16x16,12", "palindromic"),
            (6, "x36x14x12x36x14x56,12", "palindromic"),
            (8, "x14x36x58x18,18", "double"),
        ],
    )
    def test_symmetry_matches_what_ringers_call_them(self, stage, notation, expected):
        method = Method.from_notation("test", stage, notation)
        assert describe_symmetry(list(method.changes)) == expected
