import pytest

from blueline.db.repositories import MethodRepository
from blueline.db.seed import SeedReport, seed_standard
from blueline.errors import LibraryError
from blueline.library import standard_methods


@pytest.fixture()
def repository(session) -> MethodRepository:
    return MethodRepository(session)


class TestSeeding:
    def test_it_loads_the_whole_standard_set(self, repository):
        report = seed_standard(repository)
        assert len(report.added) == len(standard_methods())
        assert repository.count() == len(standard_methods())

    def test_it_names_what_it_added(self, repository):
        assert "Cambridge Surprise Major" in seed_standard(repository).added

    def test_nothing_is_skipped_on_a_fresh_database(self, repository):
        assert seed_standard(repository).skipped == ()

    def test_seeding_twice_adds_nothing_the_second_time(self, repository):
        seed_standard(repository)
        again = seed_standard(repository)
        assert again.added == ()
        assert len(again.skipped) == len(standard_methods())

    def test_seeding_twice_leaves_the_count_alone(self, repository):
        seed_standard(repository)
        seed_standard(repository)
        assert repository.count() == len(standard_methods())

    def test_it_leaves_methods_somebody_added_alone(self, repository):
        from tests.methods import NO_HUNT_BELL

        repository.add(NO_HUNT_BELL)
        seed_standard(repository)
        assert repository.count() == len(standard_methods()) + 1

    def test_it_can_be_told_to_complain_instead(self, repository):
        seed_standard(repository)
        with pytest.raises(LibraryError):
            seed_standard(repository, skip_existing=False)


class TestReport:
    def test_it_totals_both_halves(self):
        report = SeedReport(added=("a", "b"), skipped=("c",))
        assert report.total == 3

    def test_it_reads_as_a_summary(self):
        assert str(SeedReport(added=("a",), skipped=())) == "1 added, 0 already there"


class TestSearchingTheSeededSet:
    @pytest.fixture()
    def loaded(self, repository):
        seed_standard(repository)
        return repository

    def test_the_cambridge_methods_are_findable(self, loaded):
        found = loaded.search(name="cambridge")
        assert [stored.title for stored in found] == [
            "Cambridge Surprise Minor",
            "Cambridge Surprise Major",
        ]

    def test_the_six_surprise_major_methods_are_there(self, loaded):
        assert len(loaded.search(classification="Surprise", stage=8)) == 5

    def test_it_covers_five_stages(self, loaded):
        assert loaded.stages() == [5, 6, 7, 8, 9]
