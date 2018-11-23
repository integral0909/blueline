"""Named sets of methods in the database."""

from __future__ import annotations

import pytest

from blueline.core.collections import STANDARD_EIGHT, Collection
from blueline.db.repositories import CollectionRepository, to_collection
from blueline.errors import LibraryError

PRACTICE = Collection(
    name="Tuesday practice",
    titles=frozenset({"Plain Bob Minor", "Cambridge Surprise Minor"}),
    note="what we are working on",
)


@pytest.fixture()
def collections(session) -> CollectionRepository:
    return CollectionRepository(session)


class TestStoring:
    def test_one_goes_in(self, collections) -> None:
        collections.add(PRACTICE)
        assert collections.count() == 1

    def test_it_reads_back_as_the_core_type(self, collections) -> None:
        stored = collections.add(PRACTICE)
        assert to_collection(stored) == PRACTICE

    def test_the_note_survives(self, collections) -> None:
        stored = collections.add(PRACTICE)
        assert to_collection(stored).note == "what we are working on"

    def test_a_big_one_goes_in(self, collections) -> None:
        stored = collections.add(STANDARD_EIGHT)
        assert len(to_collection(stored)) == 8

    def test_the_same_name_twice_is_refused(self, collections) -> None:
        collections.add(PRACTICE)
        with pytest.raises(LibraryError, match="already stored"):
            collections.add(PRACTICE)

    def test_an_empty_one_goes_in(self, collections) -> None:
        stored = collections.add(Collection(name="empty"))
        assert len(to_collection(stored)) == 0


class TestChanging:
    def test_saving_a_new_one_adds_it(self, collections) -> None:
        collections.save(PRACTICE)
        assert collections.count() == 1

    def test_saving_over_one_replaces_its_methods(self, collections) -> None:
        collections.add(PRACTICE)
        collections.save(PRACTICE.with_added("Grandsire Doubles"))
        assert len(to_collection(collections.get("Tuesday practice"))) == 3

    def test_saving_does_not_make_a_second(self, collections) -> None:
        collections.add(PRACTICE)
        collections.save(PRACTICE.with_added("Grandsire Doubles"))
        assert collections.count() == 1

    def test_one_can_be_removed(self, collections) -> None:
        collections.add(PRACTICE)
        collections.remove("Tuesday practice")
        assert collections.count() == 0

    def test_removing_one_that_is_not_there(self, collections) -> None:
        with pytest.raises(LibraryError, match="no collection called"):
            collections.remove("Nothing")


class TestFinding:
    @pytest.fixture()
    def stocked(self, collections):
        collections.add(PRACTICE)
        collections.add(STANDARD_EIGHT)
        return collections

    def test_by_name(self, stocked) -> None:
        assert stocked.find("tuesday practice") is not None

    def test_a_name_nobody_used(self, stocked) -> None:
        assert stocked.find("Wednesday") is None

    def test_everything_comes_back_in_name_order(self, stocked) -> None:
        names = [stored.name for stored in stocked.all()]
        assert names == sorted(names)

    def test_they_come_back_as_the_core_type(self, stocked) -> None:
        assert all(isinstance(each, Collection) for each in stocked.sets())

    def test_which_sets_hold_a_method(self, stocked) -> None:
        found = stocked.holding("Cambridge Surprise Minor")
        assert [stored.name for stored in found] == ["Tuesday practice"]

    def test_a_method_in_two_sets(self, stocked) -> None:
        stocked.add(Collection(name="another", titles=frozenset({"Plain Bob Minor"})))
        assert len(stocked.holding("Plain Bob Minor")) == 2

    def test_a_method_nothing_holds(self, stocked) -> None:
        assert stocked.holding("Weasel Surprise Major") == []
