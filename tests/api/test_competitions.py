"""Competitions over http."""

from __future__ import annotations

from typing import List


def steady(blows: int, gap: float = 0.2) -> List[float]:
    return [round(index * gap, 4) for index in range(blows)]


def ragged(blows: int, at: int, error: float = 0.15) -> List[float]:
    return [
        round(time + (error if index > at else 0.0), 4) for index, time in enumerate(steady(blows))
    ]


def an_entry(band="St Mary", position=1, **over) -> dict:
    body = {"band": band, "position": position, "faults": 12, "percentage": 97.5}
    body.update(over)
    return body


def a_sheet(**over) -> dict:
    body = {
        "name": "Marchgate District Striking",
        "held_on": "2023-05-06",
        "stage": 6,
        "place": "St Andrew, Marchgate",
        "judge": "F Ahman",
        "entries": [an_entry(), an_entry("All Saints", 2)],
    }
    body.update(over)
    return body


class TestRecording:
    def test_a_sheet_can_be_written_up(self, client):
        response = client.post("/competitions", json=a_sheet())
        assert response.status_code == 201
        assert response.json()["bands"] == 2

    def test_it_names_the_winner(self, client):
        assert client.post("/competitions", json=a_sheet()).json()["winner"] == "St Mary"

    def test_entries_come_back_in_order(self, client):
        body = client.post("/competitions", json=a_sheet()).json()
        assert [entry["band"] for entry in body["entries"]] == ["St Mary", "All Saints"]

    def test_the_same_one_twice_is_a_conflict(self, client):
        client.post("/competitions", json=a_sheet())
        assert client.post("/competitions", json=a_sheet()).status_code == 409

    def test_a_band_entering_twice_is_refused(self, client):
        body = a_sheet(entries=[an_entry(), an_entry(position=2)])
        assert client.post("/competitions", json=body).status_code == 422

    def test_a_sheet_with_nobody_on_it_is_refused(self, client):
        assert client.post("/competitions", json=a_sheet(entries=[])).status_code == 422

    def test_a_position_of_zero_is_refused(self, client):
        body = a_sheet(entries=[an_entry(position=0)])
        assert client.post("/competitions", json=body).status_code == 422


class TestJudging:
    def a_recording(self, **over) -> dict:
        body = {
            "name": "Marchgate District Striking",
            "held_on": "2023-05-06",
            "stage": 6,
            "attempts": {"St Mary": ragged(48, 10), "All Saints": steady(48)},
        }
        body.update(over)
        return body

    def test_the_marking_decides_the_order(self, client):
        body = client.post("/competitions/judged", json=self.a_recording()).json()
        assert body["entries"][0]["band"] == "All Saints"

    def test_it_is_stored(self, client):
        client.post("/competitions/judged", json=self.a_recording())
        assert client.get("/competitions").json()["count"] == 1

    def test_a_band_with_one_blow_is_refused(self, client):
        body = self.a_recording(attempts={"St Mary": [0.0]})
        assert client.post("/competitions/judged", json=body).status_code == 422

    def test_no_bands_is_refused(self, client):
        assert (
            client.post("/competitions/judged", json=self.a_recording(attempts={})).status_code
            == 422
        )


class TestReadingBack:
    def stock(self, client):
        client.post("/competitions", json=a_sheet(held_on="2022-05-07"))
        client.post("/competitions", json=a_sheet())
        client.post(
            "/competitions",
            json=a_sheet(name="County Final", held_on="2023-06-10", stage=8),
        )

    def test_everything_is_listed(self, client):
        self.stock(client)
        assert client.get("/competitions").json()["count"] == 3

    def test_listing_by_name(self, client):
        self.stock(client)
        assert client.get("/competitions", params={"name": "County"}).json()["count"] == 1

    def test_listing_by_band(self, client):
        self.stock(client)
        assert client.get("/competitions", params={"band": "All Saints"}).json()["count"] == 3

    def test_one_can_be_fetched(self, client):
        made = client.post("/competitions", json=a_sheet()).json()
        assert client.get(f"/competitions/{made['id']}").json()["name"] == made["name"]

    def test_one_that_is_not_there(self, client):
        assert client.get("/competitions/404").status_code == 404

    def test_one_can_be_deleted(self, client):
        made = client.post("/competitions", json=a_sheet()).json()
        assert client.delete(f"/competitions/{made['id']}").status_code == 204
        assert client.get("/competitions").json()["count"] == 0

    def test_deleting_one_that_is_not_there(self, client):
        assert client.delete("/competitions/404").status_code == 404


class TestBandProgress:
    def test_it_lists_the_placings(self, client):
        client.post("/competitions", json=a_sheet(held_on="2022-05-07"))
        client.post("/competitions", json=a_sheet())
        body = client.get("/competitions/bands/St Mary").json()
        assert body["entered"] == 2

    def test_a_band_nobody_has_seen(self, client):
        body = client.get("/competitions/bands/St Swithin").json()
        assert body["entered"] == 0
        assert body["improving"] is None

    def test_the_band_route_is_not_read_as_an_id(self, client):
        assert client.get("/competitions/bands/St Mary").status_code == 200
