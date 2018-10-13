"""Judging striking over http."""

from __future__ import annotations

from typing import List

def steady(blows: int, gap: float = 0.2) -> List[float]:
    return [round(index * gap, 4) for index in range(blows)]


def ragged(blows: int, at: int, error: float = 0.15) -> List[float]:
    times = steady(blows)
    return [round(time + (error if index > at else 0.0), 4) for index, time in enumerate(times)]


def an_attempt(**over) -> dict:
    body = {"band": "St Mary", "stage": 6, "times": steady(48)}
    body.update(over)
    return body


class TestMarking:
    def test_a_clean_attempt(self, client):
        response = client.post("/striking/mark", json=an_attempt())
        assert response.status_code == 200
        assert response.json()["faults"] == 0

    def test_the_band_comes_back(self, client):
        body = client.post("/striking/mark", json=an_attempt()).json()
        assert body["band"] == "St Mary"

    def test_a_ragged_attempt_has_faults(self, client):
        body = client.post("/striking/mark", json=an_attempt(times=ragged(48, 10))).json()
        assert body["faults"] > 0

    def test_the_percentage_is_rounded(self, client):
        body = client.post("/striking/mark", json=an_attempt(times=ragged(60, 20))).json()
        assert body["percentage"] == round(body["percentage"], 2)

    def test_the_worst_are_listed(self, client):
        body = client.post(
            "/striking/mark", json=an_attempt(times=ragged(60, 20), threshold=0.01)
        ).json()
        assert len(body["worst"]) <= 5

    def test_drift_is_reported(self, client):
        body = client.post("/striking/mark", json=an_attempt()).json()
        assert body["drift"] in {"even", "early", "late", "unsteady"}

    def test_one_blow_is_refused(self, client):
        response = client.post("/striking/mark", json=an_attempt(times=[0.0]))
        assert response.status_code == 422

    def test_blows_out_of_order_are_refused(self, client):
        response = client.post("/striking/mark", json=an_attempt(times=[0.0, 0.4, 0.2]))
        assert response.status_code == 422

    def test_a_nameless_band_is_refused(self, client):
        response = client.post("/striking/mark", json=an_attempt(band="   "))
        assert response.status_code == 422

    def test_a_threshold_over_one_is_refused(self, client):
        response = client.post("/striking/mark", json=an_attempt(threshold=2.0))
        assert response.status_code == 422


class TestCompetition:
    def a_competition(self, **over) -> dict:
        body = {
            "stage": 6,
            "attempts": {"St Mary": ragged(48, 10), "All Saints": steady(48)},
        }
        body.update(over)
        return body

    def test_bands_come_back_in_order(self, client):
        body = client.post("/striking/order", json=self.a_competition()).json()
        assert body["order"][0]["band"] == "All Saints"

    def test_the_count_is_reported(self, client):
        body = client.post("/striking/order", json=self.a_competition()).json()
        assert body["bands"] == 2

    def test_the_stage_comes_back(self, client):
        body = client.post("/striking/order", json=self.a_competition()).json()
        assert body["stage"] == 6

    def test_no_bands_is_refused(self, client):
        response = client.post("/striking/order", json=self.a_competition(attempts={}))
        assert response.status_code == 422

    def test_a_band_with_one_blow_is_refused(self, client):
        response = client.post(
            "/striking/order", json=self.a_competition(attempts={"St Mary": [0.0]})
        )
        assert response.status_code == 422
