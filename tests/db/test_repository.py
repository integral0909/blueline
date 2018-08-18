import pytest

from blueline.db.repository import CompositionRepository, MethodRepository, to_method, to_stored
from blueline.errors import LibraryError
from blueline.library.builtin import standard_methods
from tests.methods import CAMBRIDGE_MAJOR, CAMBRIDGE_MINOR, PLAIN_BOB_MINOR


@pytest.fixture()
def methods(session) -> MethodRepository:
    return MethodRepository(session)


@pytest.fixture()
def compositions(session) -> CompositionRepository:
    return CompositionRepository(session)


class TestConversion:
    def test_it_works_out_the_title(self):
        assert to_stored(CAMBRIDGE_MAJOR).title == "Cambridge Surprise Major"

    def test_it_keeps_the_bare_name_apart_from_the_title(self):
        stored = to_stored(CAMBRIDGE_MAJOR)
        assert stored.name == "Cambridge"
        assert stored.classification == "Surprise"

    def test_a_method_survives_the_round_trip(self):
        rebuilt = to_method(to_stored(CAMBRIDGE_MINOR))
        assert rebuilt.changes == CAMBRIDGE_MINOR.changes
        assert rebuilt.stage == CAMBRIDGE_MINOR.stage

    def test_the_name_can_be_overridden(self):
        assert to_stored(CAMBRIDGE_MINOR, name="Primrose").title == "Primrose Surprise Minor"


class TestAdding:
    def test_a_method_can_be_added_and_found(self, methods):
        methods.add(CAMBRIDGE_MAJOR)
        assert methods.get("Cambridge Surprise Major").stage == 8

    def test_it_gets_an_id_straight_away(self, methods):
        assert methods.add(PLAIN_BOB_MINOR).id is not None

    def test_the_same_method_twice_is_refused(self, methods):
        methods.add(CAMBRIDGE_MAJOR)
        with pytest.raises(LibraryError, match="already"):
            methods.add(CAMBRIDGE_MAJOR)

    def test_lookup_ignores_case_and_space(self, methods):
        methods.add(CAMBRIDGE_MAJOR)
        assert methods.get("  cambridge surprise major ")

    def test_find_gives_nothing_rather_than_raising(self, methods):
        assert methods.find("Nowhere Surprise Major") is None

    def test_get_names_what_was_asked_for(self, methods):
        with pytest.raises(LibraryError, match="Nowhere"):
            methods.get("Nowhere Surprise Major")

    def test_the_whole_standard_set_goes_in(self, methods):
        for method in standard_methods():
            methods.add(method)
        assert methods.count() == len(standard_methods())


class TestSearch:
    @pytest.fixture()
    def loaded(self, methods):
        for method in standard_methods():
            methods.add(method)
        return methods

    def test_it_finds_by_name(self, loaded):
        found = loaded.search(name="cambridge")
        assert [stored.title for stored in found] == [
            "Cambridge Surprise Minor",
            "Cambridge Surprise Major",
        ]

    def test_it_finds_by_stage(self, loaded):
        assert all(stored.stage == 8 for stored in loaded.search(stage=8))

    def test_it_finds_by_class(self, loaded):
        found = loaded.search(classification="surprise", stage=8)
        assert len(found) == 5

    def test_results_come_back_by_stage_then_title(self, loaded):
        keys = [(stored.stage, stored.title) for stored in loaded.all()]
        assert keys == sorted(keys)

    def test_a_search_matching_nothing_gives_nothing(self, loaded):
        assert loaded.search(name="nowhere") == []

    def test_it_lists_the_stages_it_holds(self, loaded):
        assert loaded.stages() == [5, 6, 7, 8, 9]

    def test_an_empty_repository_holds_nothing(self, methods):
        assert methods.count() == 0
        assert methods.all() == []
        assert methods.stages() == []


class TestRemoving:
    def test_a_method_can_be_removed(self, methods, session):
        methods.add(CAMBRIDGE_MAJOR)
        methods.remove("Cambridge Surprise Major")
        session.flush()
        assert methods.find("Cambridge Surprise Major") is None

    def test_removing_something_that_is_not_there_complains(self, methods):
        with pytest.raises(LibraryError):
            methods.remove("Nowhere Surprise Major")


class TestCompositions:
    def test_a_composition_can_be_stored_against_a_method(self, methods, compositions):
        stored = methods.add(CAMBRIDGE_MAJOR)
        compositions.add(stored, title="1250", calling="-p-", length=1250, is_true=True)
        assert compositions.count() == 1

    def test_they_come_back_for_their_method(self, methods, compositions):
        stored = methods.add(CAMBRIDGE_MAJOR)
        compositions.add(stored, title="1250", calling="-", length=1250, is_true=True)
        compositions.add(stored, title="5024", calling="-p", length=5024, is_true=True)
        found = compositions.for_method(stored)
        assert [c.title for c in found] == ["5024", "1250"]

    def test_a_method_with_none_has_none(self, methods, compositions):
        stored = methods.add(PLAIN_BOB_MINOR)
        assert compositions.for_method(stored) == []

    def test_the_longest_come_back_first(self, methods, compositions):
        stored = methods.add(CAMBRIDGE_MAJOR)
        for length in (720, 5040, 1250):
            compositions.add(stored, title=str(length), calling="-", length=length, is_true=True)
        assert [c.length for c in compositions.longest()] == [5040, 1250, 720]

    def test_the_longest_list_can_be_capped(self, methods, compositions):
        stored = methods.add(CAMBRIDGE_MAJOR)
        for length in (720, 5040, 1250):
            compositions.add(stored, title=str(length), calling="-", length=length, is_true=True)
        assert len(compositions.longest(limit=2)) == 2

    def test_a_composer_may_be_left_off(self, methods, compositions):
        stored = methods.add(CAMBRIDGE_MAJOR)
        made = compositions.add(stored, title="x", calling="-", length=224, is_true=False)
        assert made.composer is None

    def test_titles_and_callings_are_trimmed(self, methods, compositions):
        stored = methods.add(CAMBRIDGE_MAJOR)
        made = compositions.add(
            stored, title="  1250  ", calling=" -p- ", length=1250, is_true=True
        )
        assert made.title == "1250"
        assert made.calling == "-p-"
