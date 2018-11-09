"""Compositions over http."""

from __future__ import annotations

PLAIN = "Plain Bob Minor"
BOBS = "---"


def a_composition(**over) -> dict:
    body = {"title": "A 60", "method": PLAIN, "calling": BOBS, "composer": "F Ahman"}
    body.update(over)
    return body


class TestStoring:
    def test_a_touch_can_be_kept(self, seeded):
        response = seeded.post("/compositions", json=a_composition())
        assert response.status_code == 201
        assert response.json()["title"] == "A 60"

    def test_it_is_proved_on_the_way_in(self, seeded):
        body = seeded.post("/compositions", json=a_composition()).json()
        assert body["is_true"] is True
        assert body["length"] > 0

    def test_the_composer_comes_back(self, seeded):
        assert seeded.post("/compositions", json=a_composition()).json()["composer"] == "F Ahman"

    def test_a_method_nobody_has_stored(self, seeded):
        body = a_composition(method="Weasel Surprise Major")
        assert seeded.post("/compositions", json=body).status_code == 404

    def test_a_calling_that_does_not_come_round(self, seeded):
        assert seeded.post("/compositions", json=a_composition(calling="-")).status_code == 422

    def test_a_blank_title(self, seeded):
        assert seeded.post("/compositions", json=a_composition(title="  ")).status_code == 422


class TestReadingBack:
    def test_the_longest_come_back(self, seeded):
        seeded.post("/compositions", json=a_composition())
        assert seeded.get("/compositions").json()["count"] == 1

    def test_everything_for_a_method(self, seeded):
        seeded.post("/compositions", json=a_composition())
        seeded.post("/compositions", json=a_composition(title="Another 60"))
        body = seeded.get("/compositions", params={"method": PLAIN}).json()
        assert body["count"] == 2

    def test_a_method_with_nothing_written_for_it(self, seeded):
        body = seeded.get("/compositions", params={"method": "Cambridge Surprise Minor"}).json()
        assert body["count"] == 0

    def test_a_method_nobody_has_stored(self, seeded):
        response = seeded.get("/compositions", params={"method": "Weasel Surprise Major"})
        assert response.status_code == 404

    def test_the_list_can_be_cut_short(self, seeded):
        seeded.post("/compositions", json=a_composition())
        seeded.post("/compositions", json=a_composition(title="Another 60"))
        assert seeded.get("/compositions", params={"limit": 1}).json()["count"] == 1

    def test_one_can_be_fetched(self, seeded):
        made = seeded.post("/compositions", json=a_composition()).json()
        assert seeded.get(f"/compositions/{made['id']}").json()["title"] == "A 60"

    def test_one_that_is_not_there(self, seeded):
        assert seeded.get("/compositions/404").status_code == 404

    def test_it_says_whether_it_still_proves_the_same(self, seeded):
        body = seeded.post("/compositions", json=a_composition()).json()
        assert body["still_true"] is True

    def test_one_can_be_deleted(self, seeded):
        made = seeded.post("/compositions", json=a_composition()).json()
        assert seeded.delete(f"/compositions/{made['id']}").status_code == 204
        assert seeded.get("/compositions").json()["count"] == 0

    def test_deleting_one_that_is_not_there(self, seeded):
        assert seeded.delete("/compositions/404").status_code == 404
