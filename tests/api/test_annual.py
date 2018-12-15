"""A tower's report for the year, over http."""

from __future__ import annotations

import pytest

PLACE = "St Andrew, Marchgate"
EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]


@pytest.fixture()
def rung(seeded):
    def add(length: int, when: str, title: str = "Cambridge Surprise Major") -> None:
        seeded.post(
            "/performances",
            json={
                "title": title,
                "stage": 8,
                "length": length,
                "rang_on": when,
                "place": PLACE,
                "ringers": EIGHT,
                "conductor": "Hana",
            },
        )

    add(5024, "2023-04-09")
    add(1280, "2023-11-12")
    add(1280, "2023-12-25", "Yorkshire Surprise Major")
    add(5056, "2022-04-17")
    return seeded


class TestReport:
    def test_it_answers(self, rung):
        response = rung.get(f"/towers/{PLACE}/year/2023")
        assert response.status_code == 200

    def test_it_counts_the_peals(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/2023").json()["peals"] == 1

    def test_it_counts_the_quarters(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/2023").json()["quarters"] == 2

    def test_last_year_is_left_out(self, rung):
        body = rung.get(f"/towers/{PLACE}/year/2023").json()
        assert body["performances"] == 3

    def test_it_notices_the_occasions(self, rung):
        body = rung.get(f"/towers/{PLACE}/year/2023").json()
        assert "Easter Sunday" in body["occasions_rung"]

    def test_it_names_the_busiest_ringers(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/2023").json()["top_ringers"]

    def test_the_leaderboards_can_be_cut_short(self, rung):
        body = rung.get(f"/towers/{PLACE}/year/2023", params={"top": 2}).json()
        assert len(body["top_ringers"]) <= 2

    def test_a_quiet_year(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/2019").json()["quiet"] is True

    def test_it_summarises(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/2023").json()["summary"]

    def test_a_year_before_anybody_rang(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/1200").status_code == 422

    def test_a_leaderboard_of_nothing(self, rung):
        response = rung.get(f"/towers/{PLACE}/year/2023", params={"top": 0})
        assert response.status_code == 422

    def test_the_year_route_is_not_read_as_a_place(self, rung):
        assert rung.get(f"/towers/{PLACE}/year/2023").status_code == 200
