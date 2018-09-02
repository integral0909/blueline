from datetime import date

from blueline.service import performances as service
from blueline.service.results import Reason

EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]


def record(perf_repo, method_repo, **over):
    fields = {
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": "2023-03-18",
        "place": "St Andrew, Marchgate",
        "ringers": EIGHT,
        "conductor": "Hana",
        "composer": "F Ahman",
    }
    fields.update(over)
    return service.record(perf_repo, method_repo, **fields)


class TestParseDate:
    def test_it_reads_an_ordinary_date(self):
        assert service.parse_date("2023-03-18").unwrap() == date(2023, 3, 18)

    def test_it_does_not_mind_stray_space(self):
        assert service.parse_date("  2023-03-18 ").ok

    def test_something_that_is_not_a_date_is_invalid(self):
        result = service.parse_date("last tuesday")
        assert result.failure.reason is Reason.INVALID
        assert "2023-03-18" in result.failure.detail

    def test_a_date_that_does_not_exist_is_invalid(self):
        assert not service.parse_date("2023-02-30").ok


class TestMakeBand:
    def test_it_builds_a_band(self):
        assert service.make_band(EIGHT, "Hana").unwrap().conductor == 8

    def test_a_repeated_name_is_invalid(self):
        result = service.make_band(["Ann", "Ann", "Cara", "Dan"])
        assert result.failure.reason is Reason.INVALID

    def test_a_conductor_who_is_not_there_is_invalid(self):
        assert not service.make_band(EIGHT, "Nobody").ok

    def test_a_band_too_small_to_ring_anything_is_invalid(self):
        assert not service.make_band(["Ann", "Bob"]).ok


class TestRecord:
    def test_it_writes_up_a_performance(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert view.length == 5024
        assert view.conductor == "Hana"

    def test_it_is_stored(self, performances, repository):
        record(performances, repository)
        assert performances.count() == 1

    def test_it_links_to_the_method_where_the_library_has_it(self, performances, loaded):
        view = record(performances, loaded).unwrap()
        stored = performances.get(view.id)
        assert stored.method is not None

    def test_it_records_a_method_the_library_has_never_heard_of(self, performances, repository):
        view = record(performances, repository, title="Nowhere Surprise Major").unwrap()
        assert performances.get(view.id).method is None

    def test_a_bad_date_is_invalid(self, performances, repository):
        result = record(performances, repository, rang_on="last tuesday")
        assert result.failure.reason is Reason.INVALID

    def test_a_bad_band_is_invalid(self, performances, repository):
        result = record(performances, repository, ringers=["Ann", "Ann", "Cara", "Dan"])
        assert result.failure.reason is Reason.INVALID

    def test_a_band_too_small_for_the_stage_is_invalid(self, performances, repository):
        result = record(performances, repository, stage=12)
        assert result.failure.reason is Reason.INVALID

    def test_a_length_of_nothing_is_invalid(self, performances, repository):
        assert not record(performances, repository, length=0).ok

    def test_nothing_is_stored_when_it_is_refused(self, performances, repository):
        record(performances, repository, rang_on="nonsense")
        assert performances.count() == 0


class TestView:
    def test_it_says_what_the_length_counts_as(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert view.counts_as == "peal"
        assert view.is_peal

    def test_a_quarter_says_so(self, performances, repository):
        view = record(performances, repository, length=1250).unwrap()
        assert view.counts_as == "quarter peal"
        assert not view.is_peal

    def test_it_notices_a_covering_tenor(self, performances, repository):
        view = record(performances, repository, stage=7, length=5040).unwrap()
        assert view.has_covering_tenor

    def test_it_carries_the_band(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert list(view.ringers) == EIGHT

    def test_it_carries_the_board(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert "8 Hana (c)" in view.board

    def test_the_summary_reads_as_a_line(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert view.summary() == (
            "5024 Cambridge Surprise Major at St Andrew, Marchgate on 18 March 2023"
        )


class TestFetchAndSearch:
    def test_it_fetches_one_back(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert service.fetch(performances, view.id).unwrap().length == 5024

    def test_one_that_is_not_there_is_not_found(self, performances):
        assert service.fetch(performances, 999).failure.reason is Reason.NOT_FOUND

    def test_it_searches_by_ringer(self, performances, repository):
        record(performances, repository)
        record(performances, repository, place="St Mary, Ashcombe", ringers=EIGHT[::-1])
        found = service.search(performances, ringer="Ann").unwrap()
        assert len(found) == 2

    def test_it_searches_by_place(self, performances, repository):
        record(performances, repository)
        record(performances, repository, place="St Mary, Ashcombe")
        assert len(service.search(performances, place="Ashcombe").unwrap()) == 1

    def test_a_search_matching_nothing_succeeds_with_nothing(self, performances, repository):
        record(performances, repository)
        assert service.search(performances, place="Nowhere").unwrap() == []
