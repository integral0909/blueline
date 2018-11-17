"""What to learn next, over http."""

from __future__ import annotations

import pytest


@pytest.fixture()
def band(seeded):
    seeded.post("/ringers", json={"name": "Ann", "can_ring": ["Plain Bob Doubles"]})
    seeded.post(
        "/ringers",
        json={"name": "Bob", "can_ring": ["Plain Bob Doubles", "Plain Bob Minor"]},
    )
    return seeded


class TestOrder:
    def test_the_library_comes_back_in_order(self, seeded):
        scores = [each["score"] for each in seeded.get("/learning/order").json()["items"]]
        assert scores == sorted(scores)

    def test_it_can_be_narrowed_to_a_stage(self, seeded):
        items = seeded.get("/learning/order", params={"stage": 6}).json()["items"]
        assert all(each["stage"] == 6 for each in items)

    def test_it_pages(self, seeded):
        body = seeded.get("/learning/order", params={"limit": 3}).json()
        assert body["count"] == 3

    def test_a_stage_nobody_rings(self, seeded):
        assert seeded.get("/learning/order", params={"stage": 2}).status_code == 422


class TestHowHard:
    def test_it_scores_a_method(self, seeded):
        body = seeded.get("/learning/methods/Cambridge Surprise Minor").json()
        assert body["score"] > 0

    def test_it_puts_it_in_a_band(self, seeded):
        assert seeded.get("/learning/methods/Plain Bob Doubles").json()["band"] == "learner"

    def test_it_says_why(self, seeded):
        assert seeded.get("/learning/methods/Cambridge Surprise Minor").json()["reasons"]

    def test_a_method_nobody_has_stored(self, seeded):
        assert seeded.get("/learning/methods/Weasel Surprise Major").status_code == 404


class TestAdvice:
    def test_it_advises_a_ringer(self, band):
        body = band.get("/learning/ringers/Ann").json()
        assert body["ringer"] == "Ann"
        assert body["fill_gaps"]

    def test_it_skips_what_they_ring(self, band):
        body = band.get("/learning/ringers/Ann").json()
        assert all(each["title"] != "Plain Bob Doubles" for each in body["fill_gaps"])

    def test_it_names_a_step_up(self, band):
        assert band.get("/learning/ringers/Bob").json()["step_up"] is not None

    def test_it_summarises(self, band):
        assert band.get("/learning/ringers/Ann").json()["summary"]

    def test_a_ringer_nobody_has_heard_of(self, band):
        assert band.get("/learning/ringers/Nobody").status_code == 404

    def test_too_many_suggestions_is_refused(self, band):
        response = band.get("/learning/ringers/Ann", params={"how_many": 99})
        assert response.status_code == 422


class TestTheBand:
    def test_it_suggests_for_everybody(self, band):
        items = band.get("/learning/band").json()["items"]
        assert all(each["title"] != "Plain Bob Doubles" for each in items)

    def test_nobody_on_the_books(self, seeded):
        assert seeded.get("/learning/band").status_code == 404

    def test_the_band_route_is_not_read_as_a_method(self, band):
        assert band.get("/learning/band").status_code == 200
