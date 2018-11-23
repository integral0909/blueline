"""Named sets of methods, over http."""

from __future__ import annotations

MINOR = ["Plain Bob Minor", "Cambridge Surprise Minor"]


def a_set(**over) -> dict:
    body = {"name": "Tuesday", "titles": MINOR, "note": "working on"}
    body.update(over)
    return body


class TestKeeping:
    def test_a_set_can_be_written_down(self, seeded):
        response = seeded.post("/collections", json=a_set())
        assert response.status_code == 201
        assert response.json()["size"] == 2

    def test_it_says_what_the_library_holds(self, seeded):
        body = a_set(titles=[*MINOR, "Weasel Surprise Major"])
        assert seeded.post("/collections", json=body).json()["not_stored"] == [
            "Weasel Surprise Major"
        ]

    def test_it_ranks_what_is_in_it(self, seeded):
        body = seeded.post("/collections", json=a_set()).json()
        assert body["difficulties"][0]["title"] == "Plain Bob Minor"

    def test_it_says_whether_they_splice(self, seeded):
        body = seeded.post("/collections", json=a_set()).json()
        assert body["splices"] in {True, False}

    def test_the_same_name_twice_is_a_conflict(self, seeded):
        seeded.post("/collections", json=a_set())
        assert seeded.post("/collections", json=a_set()).status_code == 409

    def test_a_nameless_set_is_refused(self, seeded):
        assert seeded.post("/collections", json=a_set(name="  ")).status_code == 422

    def test_a_whole_library_pasted_in_is_refused(self, seeded):
        body = a_set(titles=[f"Method {index} Major" for index in range(500)])
        assert seeded.post("/collections", json=body).status_code == 422


class TestReadingBack:
    def test_everything_is_listed(self, seeded):
        seeded.post("/collections", json=a_set())
        assert seeded.get("/collections").json()["total"] == 4

    def test_the_named_sets_can_be_left_out(self, seeded):
        seeded.post("/collections", json=a_set())
        body = seeded.get("/collections", params={"include_known": False}).json()
        assert body["total"] == 1

    def test_one_can_be_fetched(self, seeded):
        seeded.post("/collections", json=a_set())
        assert seeded.get("/collections/Tuesday").json()["size"] == 2

    def test_a_set_everybody_names_needs_no_storing(self, seeded):
        assert seeded.get("/collections/the standard eight").json()["size"] == 8

    def test_a_name_nobody_uses(self, seeded):
        assert seeded.get("/collections/the weasel four").status_code == 404


class TestChanging:
    def test_a_method_can_be_added(self, seeded):
        seeded.post("/collections", json=a_set())
        response = seeded.post("/collections/Tuesday/methods", json={"title": "Grandsire Doubles"})
        assert response.json()["size"] == 3

    def test_adding_one_it_has(self, seeded):
        seeded.post("/collections", json=a_set())
        response = seeded.post("/collections/Tuesday/methods", json={"title": "Plain Bob Minor"})
        assert response.status_code == 409

    def test_a_method_can_be_taken_out(self, seeded):
        seeded.post("/collections", json=a_set())
        response = seeded.delete("/collections/Tuesday/methods/Plain Bob Minor")
        assert response.json()["size"] == 1

    def test_taking_out_one_it_does_not_have(self, seeded):
        seeded.post("/collections", json=a_set())
        response = seeded.delete("/collections/Tuesday/methods/Bristol Surprise Major")
        assert response.status_code == 404

    def test_one_can_be_forgotten(self, seeded):
        seeded.post("/collections", json=a_set())
        assert seeded.delete("/collections/Tuesday").status_code == 204

    def test_forgetting_one_that_is_not_there(self, seeded):
        assert seeded.delete("/collections/Nothing").status_code == 404


class TestCoverage:
    def band(self, client):
        client.post("/ringers", json={"name": "Ann", "can_ring": ["Plain Bob Minor"]})

    def test_what_one_ringer_covers(self, seeded):
        seeded.post("/collections", json=a_set())
        self.band(seeded)
        body = seeded.get("/collections/Tuesday/coverage", params={"who": "Ann"}).json()
        assert body["rings"] == 1
        assert body["share"] == 0.5

    def test_it_says_what_is_left(self, seeded):
        seeded.post("/collections", json=a_set())
        self.band(seeded)
        body = seeded.get("/collections/Tuesday/coverage", params={"who": "Ann"}).json()
        assert body["missing"] == ["Cambridge Surprise Minor"]

    def test_the_whole_band(self, seeded):
        seeded.post("/collections", json=a_set())
        self.band(seeded)
        assert seeded.get("/collections/Tuesday/coverage").json()["rings"] == 1

    def test_a_ringer_nobody_has_heard_of(self, seeded):
        seeded.post("/collections", json=a_set())
        response = seeded.get("/collections/Tuesday/coverage", params={"who": "Nobody"})
        assert response.status_code == 404

    def test_the_coverage_route_is_not_read_as_a_name(self, seeded):
        seeded.post("/collections", json=a_set())
        assert seeded.get("/collections/Tuesday/coverage").status_code == 200
