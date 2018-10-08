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
        assert any("8 Hana (c)" in line for line in view.board)

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


class TestStatistics:
    def test_an_empty_store_totals_nothing(self, performances):
        totals = service.statistics(performances).unwrap()
        assert totals.performances == 0
        assert totals.summary() == "nothing rung"

    def test_it_counts_what_is_there(self, performances, repository):
        record(performances, repository)
        record(performances, repository, length=1250, title="Yorkshire Surprise Major")
        totals = service.statistics(performances).unwrap()
        assert totals.performances == 2
        assert totals.peals == 1
        assert totals.quarters == 1

    def test_it_totals_the_changes(self, performances, repository):
        record(performances, repository)
        record(performances, repository, length=1250)
        assert service.statistics(performances).unwrap().changes == 6274

    def test_it_can_be_narrowed_to_a_place(self, performances, repository):
        record(performances, repository)
        record(performances, repository, place="St Mary, Ashcombe")
        totals = service.statistics(performances, place="Ashcombe").unwrap()
        assert totals.performances == 1

    def test_it_can_be_narrowed_to_a_ringer(self, performances, repository):
        record(performances, repository)
        record(
            performances,
            repository,
            ringers=["Ivy", "Jed", "Kit", "Lex", "Mo", "Nell", "Opal", "Pia"],
            conductor="Pia",
        )
        assert service.statistics(performances, ringer="Ann").unwrap().performances == 1

    def test_it_counts_the_places(self, performances, repository):
        record(performances, repository)
        record(performances, repository, place="St Mary, Ashcombe")
        assert service.statistics(performances).unwrap().places == 2

    def test_it_finds_the_commonest_method(self, performances, repository):
        record(performances, repository)
        record(performances, repository)
        record(performances, repository, title="Yorkshire Surprise Major")
        assert service.statistics(performances).unwrap().most_rung_method() == (
            "Cambridge Surprise Major",
            2,
        )


class TestLeaderboards:
    def test_the_top_ringers_come_back_most_first(self, performances, repository):
        record(performances, repository)
        record(
            performances,
            repository,
            ringers=["Ann", "Ivy", "Jed", "Kit", "Lex", "Mo", "Nell", "Opal"],
            conductor="Ann",
        )
        board = service.top_ringers(performances).unwrap()
        assert board[0] == ("Ann", 2)

    def test_it_can_be_capped(self, performances, repository):
        record(performances, repository)
        assert len(service.top_ringers(performances, top=3).unwrap()) == 3

    def test_the_top_methods_come_back_most_first(self, performances, repository):
        record(performances, repository)
        record(performances, repository)
        record(performances, repository, title="Yorkshire Surprise Major")
        board = service.top_methods(performances).unwrap()
        assert board[0] == ("Cambridge Surprise Major", 2)

    def test_an_empty_store_has_an_empty_board(self, performances):
        assert service.top_ringers(performances).unwrap() == []


class TestTowerLink:
    def _towers(self, repository):
        from blueline.db.repository import TowerRepository
        from blueline.service import towers as tower_service

        store = TowerRepository(repository.session)
        tower_service.add(store, "St Andrew, Marchgate", 8, "23-1-14")
        tower_service.add(store, "St Mary, Ashcombe", 6, "8-0-0")
        return store

    def test_it_links_the_tower_when_the_place_matches(self, performances, repository):
        towers = self._towers(repository)
        view = record(performances, repository, towers=towers).unwrap()
        assert view.tower == "St Andrew, Marchgate"

    def test_a_place_with_no_tower_is_left_unlinked(self, performances, repository):
        towers = self._towers(repository)
        view = record(performances, repository, place="Somewhere else", towers=towers).unwrap()
        assert view.tower is None

    def test_no_tower_store_at_all_still_works(self, performances, repository):
        assert record(performances, repository).unwrap().tower is None

    def test_a_tower_too_small_for_the_stage_is_refused(self, performances, repository):
        towers = self._towers(repository)
        result = record(
            performances,
            repository,
            place="St Mary, Ashcombe",
            stage=8,
            towers=towers,
        )
        assert result.failure.reason is Reason.INVALID
        assert "cannot ring 8" in result.failure.detail

    def test_nothing_is_stored_when_the_tower_refuses(self, performances, repository):
        towers = self._towers(repository)
        record(performances, repository, place="St Mary, Ashcombe", stage=8, towers=towers)
        assert performances.count() == 0

    def test_a_tower_big_enough_is_accepted(self, performances, repository):
        towers = self._towers(repository)
        result = record(
            performances,
            repository,
            place="St Mary, Ashcombe",
            stage=6,
            length=720,
            ringers=["Ann", "Bob", "Cara", "Dan", "Eve", "Finn"],
            conductor="Ann",
            towers=towers,
        )
        assert result.ok
        assert result.unwrap().tower == "St Mary, Ashcombe"


class TestSpeed:
    def test_the_default_is_thirty(self, performances, repository):
        view = record(performances, repository).unwrap()
        assert 150 < view.duration_minutes < 180

    def test_a_faster_band_takes_less_time(self, performances, repository):
        quick = record(performances, repository, peal_speed=40.0).unwrap()
        slow = record(performances, repository, peal_speed=20.0).unwrap()
        assert quick.duration_minutes < slow.duration_minutes

    def test_a_speed_of_nothing_is_invalid(self, performances, repository):
        result = record(performances, repository, peal_speed=0)
        assert result.failure.reason is Reason.INVALID

    def test_a_negative_speed_is_invalid(self, performances, repository):
        assert not record(performances, repository, peal_speed=-5).ok

    def test_nothing_is_stored_when_the_speed_is_refused(self, performances, repository):
        record(performances, repository, peal_speed=0)
        assert performances.count() == 0
