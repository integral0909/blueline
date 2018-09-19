import pytest

from blueline.analysis import analyse
from blueline.core.method import Method
from blueline.core.symmetry import symmetric_notation
from blueline.core.variations import (
    describe_relation,
    is_same_method,
    mirror_of,
    mirrored_notation,
    reverse_of,
    reversed_notation,
    rotated_notation,
    rotation_of,
    with_lead_end,
)
from tests.methods import (
    ALL_METHODS,
    CAMBRIDGE_MAJOR,
    CAMBRIDGE_MINOR,
    GRANDSIRE_DOUBLES,
    PLAIN_BOB_MINOR,
    method_id,
)


class TestReversed:
    def test_it_keeps_the_lead_end_where_it_is(self):
        changes = reversed_notation(PLAIN_BOB_MINOR.changes)
        assert changes[-1] == PLAIN_BOB_MINOR.changes[-1]

    def test_it_keeps_the_lead_the_same_length(self):
        assert len(reversed_notation(CAMBRIDGE_MINOR.changes)) == CAMBRIDGE_MINOR.lead_length

    def test_reversing_twice_gives_it_back(self):
        once = reversed_notation(CAMBRIDGE_MINOR.changes)
        assert reversed_notation(tuple(once)) == list(CAMBRIDGE_MINOR.changes)

    def test_an_empty_lead_reverses_to_nothing(self):
        assert reversed_notation(()) == []

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_a_method_symmetric_about_its_lead_end_is_its_own_reverse(self, method):
        # Which methods those are is exactly the ones that can be written as
        # half a lead, a comma and a lead end change. Grandsire cannot, because
        # its symmetry is about the treble's lead, and it is not its own
        # reverse.
        if symmetric_notation(list(method.changes)) is None:
            pytest.skip(f"{method.name} does not reflect about its lead end")
        assert reverse_of(method).changes == method.changes

    def test_grandsire_is_not_its_own_reverse(self):
        assert symmetric_notation(list(GRANDSIRE_DOUBLES.changes)) is None
        assert reverse_of(GRANDSIRE_DOUBLES).changes != GRANDSIRE_DOUBLES.changes


class TestMirrored:
    def test_seconds_becomes_the_back_place(self):
        changes = mirrored_notation(PLAIN_BOB_MINOR.changes)
        assert str(changes[-1]) == "56"

    def test_it_keeps_the_lead_the_same_length(self):
        assert len(mirrored_notation(CAMBRIDGE_MAJOR.changes)) == CAMBRIDGE_MAJOR.lead_length

    def test_mirroring_twice_gives_it_back(self):
        once = mirrored_notation(CAMBRIDGE_MINOR.changes)
        assert mirrored_notation(tuple(once)) == list(CAMBRIDGE_MINOR.changes)

    def test_a_cross_mirrors_to_itself(self):
        changes = mirrored_notation(PLAIN_BOB_MINOR.changes)
        assert changes[0].is_cross

    @pytest.mark.parametrize("method", ALL_METHODS, ids=method_id)
    def test_the_result_is_a_real_method(self, method):
        mirrored = mirror_of(method)
        assert mirrored.stage == method.stage
        assert mirrored.lead_length == method.lead_length


class TestRotated:
    def test_it_is_reversed_and_mirrored_at_once(self):
        both = mirrored_notation(tuple(reversed_notation(CAMBRIDGE_MINOR.changes)))
        assert rotated_notation(CAMBRIDGE_MINOR.changes) == both

    def test_for_a_palindromic_method_it_is_just_the_mirror(self):
        assert rotated_notation(PLAIN_BOB_MINOR.changes) == mirrored_notation(
            PLAIN_BOB_MINOR.changes
        )


class TestNaming:
    def test_a_reverse_is_named_reverse(self):
        assert reverse_of(CAMBRIDGE_MINOR).name == "Reverse Cambridge"

    def test_a_mirror_is_named_mirror(self):
        assert mirror_of(CAMBRIDGE_MINOR).name == "Mirror Cambridge"

    def test_a_rotation_is_named_double(self):
        assert rotation_of(CAMBRIDGE_MINOR).name == "Double Cambridge"

    def test_a_name_can_be_given_instead(self):
        assert mirror_of(CAMBRIDGE_MINOR, name="Primrose").name == "Primrose"


class TestWithLeadEnd:
    def test_it_swaps_the_last_change(self):
        changed = with_lead_end(CAMBRIDGE_MINOR, "16")
        assert str(changed.changes[-1]) == "16"

    def test_the_rest_of_the_lead_is_untouched(self):
        changed = with_lead_end(CAMBRIDGE_MINOR, "16")
        assert changed.changes[:-1] == CAMBRIDGE_MINOR.changes[:-1]

    def test_the_result_still_rings_a_true_course(self):
        assert analyse(with_lead_end(CAMBRIDGE_MINOR, "16")).course_is_true

    def test_it_keeps_the_name_unless_told_otherwise(self):
        assert with_lead_end(CAMBRIDGE_MINOR, "16").name == "Cambridge"

    def test_a_change_that_does_not_work_is_refused(self):
        from blueline.errors import NotationError

        with pytest.raises(NotationError):
            with_lead_end(PLAIN_BOB_MINOR, "13")


class TestRelations:
    def test_a_method_is_the_same_as_itself(self):
        assert describe_relation(CAMBRIDGE_MINOR, CAMBRIDGE_MINOR) == "the same method"

    def test_two_stages_are_not_related(self):
        assert describe_relation(CAMBRIDGE_MINOR, CAMBRIDGE_MAJOR) is None

    def test_a_lead_end_swap_is_named(self):
        changed = with_lead_end(CAMBRIDGE_MINOR, "16")
        relation = describe_relation(CAMBRIDGE_MINOR, changed)
        assert "12 against 16" in relation

    def test_a_turned_over_method_is_named(self):
        assert describe_relation(PLAIN_BOB_MINOR, mirror_of(PLAIN_BOB_MINOR)) == "turned over"

    def test_two_unrelated_methods_are_not_related(self):
        assert describe_relation(PLAIN_BOB_MINOR, CAMBRIDGE_MINOR) is None

    def test_is_same_method_ignores_the_name(self):
        renamed = Method(name="Something else", stage=6, changes=CAMBRIDGE_MINOR.changes)
        assert is_same_method(CAMBRIDGE_MINOR, renamed)

    def test_is_same_method_notices_a_different_stage(self):
        assert not is_same_method(CAMBRIDGE_MINOR, CAMBRIDGE_MAJOR)
