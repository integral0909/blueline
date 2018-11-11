CAMBRIDGE = "Cambridge Surprise Major"
PLAIN = "Plain Bob Major"
YORKSHIRE = "Yorkshire Surprise Major"


def a_band(client):
    for name in ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn"):
        client.post("/ringers", json={"name": name, "can_ring": [CAMBRIDGE, PLAIN]})
    client.post("/ringers", json={"name": "Gus", "can_ring": [PLAIN], "learning": [CAMBRIDGE]})
    client.post("/ringers", json={"name": "Hana", "can_ring": [PLAIN], "learning": [YORKSHIRE]})
    return client


class TestAdding:
    def test_somebody_can_be_added(self, client):
        response = client.post("/ringers", json={"name": "Ann", "can_ring": [CAMBRIDGE]})
        assert response.status_code == 201
        assert response.json()["method_count"] == 1

    def test_the_titles_come_back_sorted(self, client):
        body = client.post("/ringers", json={"name": "Ann", "can_ring": [PLAIN, CAMBRIDGE]}).json()
        assert body["can_ring"] == [CAMBRIDGE, PLAIN]

    def test_somebody_who_rings_nothing_yet_is_fine(self, client):
        body = client.post("/ringers", json={"name": "New"}).json()
        assert body["can_ring"] == []

    def test_the_same_name_twice_is_a_conflict(self, client):
        client.post("/ringers", json={"name": "Ann"})
        assert client.post("/ringers", json={"name": "Ann"}).status_code == 409

    def test_ringing_and_learning_the_same_method_is_unprocessable(self, client):
        response = client.post(
            "/ringers",
            json={"name": "Ann", "can_ring": [CAMBRIDGE], "learning": [CAMBRIDGE]},
        )
        assert response.status_code == 422

    def test_an_empty_name_is_rejected_by_the_schema(self, client):
        assert client.post("/ringers", json={"name": "  "}).status_code == 422


class TestListing:
    def test_an_empty_tower_lists_nobody(self, client):
        body = client.get("/ringers").json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_it_lists_everybody(self, client):
        a_band(client)
        assert client.get("/ringers").json()["count"] == 8

    def test_they_come_back_in_name_order(self, client):
        a_band(client)
        names = [entry["name"] for entry in client.get("/ringers").json()["items"]]
        assert names == sorted(names)


class TestFetching:
    def test_somebody_can_be_fetched(self, client):
        a_band(client)
        assert client.get("/ringers/Ann").json()["method_count"] == 2

    def test_lookup_ignores_case(self, client):
        a_band(client)
        assert client.get("/ringers/ann").status_code == 200

    def test_somebody_who_is_not_there_is_a_404(self, client):
        assert client.get("/ringers/Nobody").status_code == 404


class TestLearnt:
    def test_it_moves_a_method_across(self, client):
        a_band(client)
        body = client.post("/ringers/Gus/learnt", json={"title": CAMBRIDGE}).json()
        assert CAMBRIDGE in body["can_ring"]
        assert CAMBRIDGE not in body["learning"]

    def test_it_is_saved(self, client):
        a_band(client)
        client.post("/ringers/Gus/learnt", json={"title": CAMBRIDGE})
        assert CAMBRIDGE in client.get("/ringers/Gus").json()["can_ring"]

    def test_somebody_who_is_not_there_is_a_404(self, client):
        response = client.post("/ringers/Nobody/learnt", json={"title": CAMBRIDGE})
        assert response.status_code == 404

    def test_an_empty_title_is_rejected_by_the_schema(self, client):
        a_band(client)
        assert client.post("/ringers/Gus/learnt", json={"title": ""}).status_code == 422


class TestDeleting:
    def test_somebody_can_be_deleted(self, client):
        a_band(client)
        assert client.delete("/ringers/Hana").status_code == 204

    def test_they_are_gone_afterwards(self, client):
        a_band(client)
        client.delete("/ringers/Hana")
        assert client.get("/ringers/Hana").status_code == 404

    def test_deleting_somebody_who_is_not_there_is_a_404(self, client):
        assert client.delete("/ringers/Nobody").status_code == 404


class TestLearning:
    def test_it_groups_by_method(self, client):
        a_band(client)
        body = client.get("/ringers/learning").json()
        assert body[CAMBRIDGE] == ["Gus"]
        assert body[YORKSHIRE] == ["Hana"]

    def test_a_tower_learning_nothing_has_nothing(self, client):
        client.post("/ringers", json={"name": "Ann", "can_ring": [PLAIN]})
        assert client.get("/ringers/learning").json() == {}

    def test_learning_is_not_read_as_somebody_called_learning(self, client):
        assert client.get("/ringers/learning").status_code == 200


class TestBandAbility:
    def test_it_says_what_the_band_can_get_through(self, seeded):
        a_band(seeded)
        body = seeded.get("/ringers/can-ring", params={"stage": 8}).json()
        assert PLAIN in body["titles"]
        assert CAMBRIDGE not in body["titles"]

    def test_once_the_learner_has_it_they_can(self, seeded):
        a_band(seeded)
        seeded.post("/ringers/Gus/learnt", json={"title": CAMBRIDGE})
        body = seeded.get("/ringers/can-ring", params={"stage": 8}).json()
        assert CAMBRIDGE in body["titles"]

    def test_it_counts_the_band(self, seeded):
        a_band(seeded)
        assert seeded.get("/ringers/can-ring", params={"stage": 8}).json()["ringers"] == 8

    def test_a_band_too_small_is_unprocessable(self, seeded):
        seeded.post("/ringers", json={"name": "Ann"})
        assert seeded.get("/ringers/can-ring", params={"stage": 8}).status_code == 422

    def test_a_stage_out_of_range_is_rejected(self, seeded):
        assert seeded.get("/ringers/can-ring", params={"stage": 99}).status_code == 422
