"""Performances as reports."""

from __future__ import annotations

EIGHT = ["Ann", "Bob", "Cara", "Dan", "Eve", "Finn", "Gus", "Hana"]


def a_performance(**over) -> dict:
    body = {
        "title": "Cambridge Surprise Major",
        "stage": 8,
        "length": 5024,
        "rang_on": "2023-03-18",
        "place": "St Andrew, Marchgate",
        "ringers": EIGHT,
        "conductor": "Hana",
        "composer": "F Ahman",
    }
    body.update(over)
    return body


class TestWritingOne:
    def test_it_comes_back_as_text(self, seeded):
        made = seeded.post("/performances", json=a_performance()).json()
        response = seeded.get(f"/performances/{made['id']}/report")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

    def test_the_place_is_at_the_top(self, seeded):
        made = seeded.post("/performances", json=a_performance()).json()
        text = seeded.get(f"/performances/{made['id']}/report").text
        assert text.splitlines()[0] == "St Andrew, Marchgate"

    def test_the_band_is_listed(self, seeded):
        made = seeded.post("/performances", json=a_performance()).json()
        text = seeded.get(f"/performances/{made['id']}/report").text
        assert all(name in text for name in EIGHT)

    def test_the_conductor_is_marked(self, seeded):
        made = seeded.post("/performances", json=a_performance()).json()
        assert "Hana (C)" in seeded.get(f"/performances/{made['id']}/report").text

    def test_one_that_is_not_there(self, seeded):
        assert seeded.get("/performances/404/report").status_code == 404


class TestPastingOneIn:
    def report_for(self, client) -> str:
        made = client.post("/performances", json=a_performance()).json()
        return client.get(f"/performances/{made['id']}/report").text

    def test_a_report_can_be_filed(self, seeded):
        text = self.report_for(seeded)
        response = seeded.post("/performances/report", json={"report": text, "stage": 8})
        assert response.status_code == 201
        assert response.json()["length"] == 5024

    def test_it_round_trips(self, seeded):
        text = self.report_for(seeded)
        body = seeded.post("/performances/report", json={"report": text, "stage": 8}).json()
        assert body["title"] == "Cambridge Surprise Major"
        assert body["place"] == "St Andrew, Marchgate"

    def test_the_composer_survives(self, seeded):
        text = self.report_for(seeded)
        body = seeded.post("/performances/report", json={"report": text, "stage": 8}).json()
        assert body["composer"] == "F Ahman"

    def test_it_is_stored(self, seeded):
        text = self.report_for(seeded)
        seeded.post("/performances/report", json={"report": text, "stage": 8})
        assert seeded.get("/performances").json()["total"] == 2

    def test_a_report_it_cannot_read(self, seeded):
        response = seeded.post(
            "/performances/report", json={"report": "a lovely evening", "stage": 8}
        )
        assert response.status_code == 422

    def test_a_stage_the_band_cannot_ring(self, seeded):
        text = self.report_for(seeded)
        response = seeded.post("/performances/report", json={"report": text, "stage": 6})
        assert response.status_code == 422

    def test_the_route_is_not_read_as_an_id(self, seeded):
        text = self.report_for(seeded)
        response = seeded.post("/performances/report", json={"report": text, "stage": 8})
        assert response.status_code != 404
