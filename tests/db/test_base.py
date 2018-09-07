"""The shared repository behaviour, checked once rather than three times."""

from __future__ import annotations

import pytest

from blueline.db.base import Repository
from blueline.db.models import StoredComposition, StoredMethod, StoredPerformance
from blueline.db.repository import (
    CompositionRepository,
    MethodRepository,
    PerformanceRepository,
)
from tests.methods import CAMBRIDGE_MAJOR, PLAIN_BOB_MINOR

EVERY_REPOSITORY = [MethodRepository, CompositionRepository, PerformanceRepository]


class TestShape:
    @pytest.mark.parametrize("kind", EVERY_REPOSITORY, ids=lambda k: k.__name__)
    def test_every_repository_shares_the_base(self, kind):
        assert issubclass(kind, Repository)

    @pytest.mark.parametrize("kind", EVERY_REPOSITORY, ids=lambda k: k.__name__)
    def test_every_repository_names_its_model(self, kind):
        assert kind.model is not None

    def test_they_name_different_models(self):
        models = {kind.model for kind in EVERY_REPOSITORY}
        assert models == {StoredMethod, StoredComposition, StoredPerformance}

    @pytest.mark.parametrize("kind", EVERY_REPOSITORY, ids=lambda k: k.__name__)
    def test_every_repository_takes_a_session_rather_than_opening_one(self, kind, session):
        assert kind(session).session is session


class TestCounting:
    @pytest.mark.parametrize("kind", EVERY_REPOSITORY, ids=lambda k: k.__name__)
    def test_an_empty_table_counts_nothing(self, kind, session):
        assert kind(session).count() == 0

    def test_counting_follows_what_was_added(self, session):
        methods = MethodRepository(session)
        methods.add(PLAIN_BOB_MINOR)
        assert methods.count() == 1
        methods.add(CAMBRIDGE_MAJOR)
        assert methods.count() == 2

    def test_the_counts_do_not_see_each_other(self, session):
        MethodRepository(session).add(PLAIN_BOB_MINOR)
        assert PerformanceRepository(session).count() == 0


class TestById:
    def test_it_finds_a_row_by_its_id(self, session):
        methods = MethodRepository(session)
        stored = methods.add(PLAIN_BOB_MINOR)
        assert methods.get_by_id(stored.id) is stored

    def test_an_id_that_is_not_there_gives_nothing(self, session):
        assert MethodRepository(session).get_by_id(999) is None


class TestAddAndDelete:
    def test_adding_fills_in_the_id(self, session):
        methods = MethodRepository(session)
        assert methods.add(PLAIN_BOB_MINOR).id is not None

    def test_deleting_takes_it_away(self, session):
        methods = MethodRepository(session)
        methods.add(PLAIN_BOB_MINOR)
        methods.remove("Plain Bob Minor")
        session.flush()
        assert methods.count() == 0

    def test_nothing_is_committed_on_its_own(self, session):
        # Where a transaction ends belongs to the caller, or storing a method
        # and its compositions together would be impossible.
        methods = MethodRepository(session)
        methods.add(PLAIN_BOB_MINOR)
        assert session.in_transaction()
