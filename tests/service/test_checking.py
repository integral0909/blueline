"""Looking over the library for things that have gone wrong."""

from __future__ import annotations

import pytest

from blueline.core.collections import Collection
from blueline.core.ringers import Ringer
from blueline.db.repositories import CollectionRepository, CompositionRepository
from blueline.service.checking import NOTE, PROBLEM, Finding, check
from blueline.service.compositions import store


@pytest.fixture()
def compositions(loaded) -> CompositionRepository:
    return CompositionRepository(loaded.session)


@pytest.fixture()
def collections(loaded) -> CollectionRepository:
    return CollectionRepository(loaded.session)


def run(loaded, compositions, collections, ringers, **over):
    return check(loaded, compositions, collections, ringers, **over).unwrap()


class TestACleanLibrary:
    def test_the_standard_set_is_clean(self, loaded, compositions, collections, ringers) -> None:
        report = run(loaded, compositions, collections, ringers)
        assert report.clean

    def test_it_says_how_much_it_looked_at(
        self, loaded, compositions, collections, ringers
    ) -> None:
        report = run(loaded, compositions, collections, ringers)
        assert report.checked == loaded.count()

    def test_a_summary_of_nothing_wrong(self, loaded, compositions, collections, ringers) -> None:
        report = run(loaded, compositions, collections, ringers)
        assert "nothing to report" in report.summary()


class TestMethods:
    def test_a_stored_classification_that_disagrees(
        self, loaded, compositions, collections, ringers
    ) -> None:
        stored = loaded.get("Cambridge Surprise Minor")
        stored.classification = "Bob"
        loaded.session.flush()
        report = run(loaded, compositions, collections, ringers)
        assert any("reads as Surprise" in each.detail for each in report.problems)

    def test_notation_that_will_not_parse(self, loaded, compositions, collections, ringers) -> None:
        stored = loaded.get("Plain Bob Minor")
        stored.notation = "x1x1x1"
        loaded.session.flush()
        report = run(loaded, compositions, collections, ringers)
        assert report.problems

    def test_two_methods_with_the_same_notation(
        self, loaded, compositions, collections, ringers
    ) -> None:
        from tests.methods import PLAIN_BOB_MINOR

        loaded.add(PLAIN_BOB_MINOR, name="Twin")
        report = run(loaded, compositions, collections, ringers)
        assert any("same notation" in each.detail for each in report.notes)

    def test_that_is_a_note_rather_than_a_problem(
        self, loaded, compositions, collections, ringers
    ) -> None:
        from tests.methods import PLAIN_BOB_MINOR

        loaded.add(PLAIN_BOB_MINOR, name="Twin")
        report = run(loaded, compositions, collections, ringers)
        assert report.clean


class TestCollections:
    def test_a_set_naming_a_method_nobody_has(
        self, loaded, compositions, collections, ringers
    ) -> None:
        collections.add(Collection(name="Odd", titles=frozenset({"Weasel Surprise Major"})))
        report = run(loaded, compositions, collections, ringers)
        assert any("does not hold" in each.detail for each in report.notes)

    def test_an_empty_set(self, loaded, compositions, collections, ringers) -> None:
        collections.add(Collection(name="Empty"))
        report = run(loaded, compositions, collections, ringers)
        assert any("is empty" in each.detail for each in report.notes)

    def test_a_set_the_library_holds_is_not_reported(
        self, loaded, compositions, collections, ringers
    ) -> None:
        collections.add(Collection(name="Fine", titles=frozenset({"Plain Bob Minor"})))
        report = run(loaded, compositions, collections, ringers)
        assert not any(each.subject == "Fine" for each in report.findings)


class TestRingers:
    def test_a_ringer_who_rings_something_unknown(
        self, loaded, compositions, collections, ringers
    ) -> None:
        ringers.add(
            Ringer(name="Ann", can_ring=frozenset({"Weasel Surprise Major"}), learning=frozenset())
        )
        report = run(loaded, compositions, collections, ringers)
        assert any(each.subject == "Ann" for each in report.notes)

    def test_a_ringer_the_library_agrees_with(
        self, loaded, compositions, collections, ringers
    ) -> None:
        ringers.add(
            Ringer(name="Ann", can_ring=frozenset({"Plain Bob Minor"}), learning=frozenset())
        )
        report = run(loaded, compositions, collections, ringers)
        assert not any(each.subject == "Ann" for each in report.findings)


class TestCompositions:
    def test_they_are_left_alone_unless_asked(
        self, loaded, compositions, collections, ringers
    ) -> None:
        store(compositions, loaded, "A 60", "Plain Bob Minor", "---")
        loaded.get("Plain Bob Minor").notation = "x16x16x16x36,12"
        loaded.session.flush()
        report = run(loaded, compositions, collections, ringers)
        assert not any(each.subject == "A 60" for each in report.findings)

    def test_a_thorough_pass_proves_them_again(
        self, loaded, compositions, collections, ringers
    ) -> None:
        store(compositions, loaded, "A 60", "Plain Bob Minor", "---")
        loaded.get("Plain Bob Minor").notation = "x16x16x16x36,12"
        loaded.session.flush()
        report = run(loaded, compositions, collections, ringers, thorough=True)
        assert any(each.subject == "A 60" for each in report.findings)

    def test_a_composition_that_still_proves_is_quiet(
        self, loaded, compositions, collections, ringers
    ) -> None:
        store(compositions, loaded, "A 60", "Plain Bob Minor", "---")
        report = run(loaded, compositions, collections, ringers, thorough=True)
        assert not any(each.subject == "A 60" for each in report.findings)

    def test_the_thorough_pass_counts_them(
        self, loaded, compositions, collections, ringers
    ) -> None:
        store(compositions, loaded, "A 60", "Plain Bob Minor", "---")
        quick = run(loaded, compositions, collections, ringers).checked
        slow = run(loaded, compositions, collections, ringers, thorough=True).checked
        assert slow > quick


class TestFindings:
    def test_a_problem_says_so(self) -> None:
        assert Finding(PROBLEM, "x", "y").is_problem

    def test_a_note_does_not(self) -> None:
        assert not Finding(NOTE, "x", "y").is_problem

    def test_one_reads_as_a_line(self) -> None:
        assert str(Finding(PROBLEM, "Cambridge", "gone")) == "problem: Cambridge: gone"

    def test_problems_come_before_notes(self, loaded, compositions, collections, ringers) -> None:
        collections.add(Collection(name="Empty"))
        stored = loaded.get("Cambridge Surprise Minor")
        stored.classification = "Bob"
        loaded.session.flush()
        report = run(loaded, compositions, collections, ringers)
        levels = [each.level for each in report.findings]
        assert levels.index(PROBLEM) < levels.index(NOTE)

    def test_a_summary_counts_both(self, loaded, compositions, collections, ringers) -> None:
        collections.add(Collection(name="Empty"))
        report = run(loaded, compositions, collections, ringers)
        assert "worth a look" in report.summary()

    def test_nothing_is_changed_by_looking(
        self, loaded, compositions, collections, ringers
    ) -> None:
        stored = loaded.get("Cambridge Surprise Minor")
        stored.classification = "Bob"
        loaded.session.flush()
        run(loaded, compositions, collections, ringers)
        assert loaded.get("Cambridge Surprise Minor").classification == "Bob"
