CAMBRIDGE = {
    "name": "Cambridge",
    "stage": 8,
    "notation": "x38x14x1258x36x14x58x16x78,12",
}


class TestAnalyse:
    def test_it_analyses_notation(self, client):
        response = client.post("/analyse", json=CAMBRIDGE)
        assert response.status_code == 200
        assert response.json()["title"] == "Cambridge Surprise Major"

    def test_it_gives_the_shape_of_the_method(self, client):
        body = client.post("/analyse", json=CAMBRIDGE).json()
        assert body["lead_length"] == 32
        assert body["course_length"] == 224
        assert body["classification"] == "Surprise"

    def test_it_gives_the_coursing_order(self, client):
        body = client.post("/analyse", json=CAMBRIDGE).json()
        assert body["coursing_order"] == [8, 7, 5, 3, 2, 4, 6]

    def test_it_does_not_store_anything(self, client):
        client.post("/analyse", json=CAMBRIDGE)
        assert client.get("/methods").json()["count"] == 0

    def test_bad_notation_is_unprocessable(self, client):
        response = client.post("/analyse", json={"name": "x", "stage": 5, "notation": "x1x1"})
        assert response.status_code == 422

    def test_it_says_why(self, client):
        body = client.post("/analyse", json={"name": "x", "stage": 5, "notation": "x1x1"}).json()
        assert body["detail"]["reason"] == "invalid"

    def test_a_stage_out_of_range_is_rejected_by_the_schema(self, client):
        response = client.post("/analyse", json={"name": "x", "stage": 99, "notation": "x18"})
        assert response.status_code == 422

    def test_an_empty_name_is_rejected(self, client):
        response = client.post("/analyse", json={"name": "   ", "stage": 8, "notation": "x18"})
        assert response.status_code == 422


class TestStoring:
    def test_a_method_can_be_stored(self, client):
        response = client.post("/methods", json=CAMBRIDGE)
        assert response.status_code == 201
        assert response.json()["title"] == "Cambridge Surprise Major"

    def test_it_is_there_afterwards(self, client):
        client.post("/methods", json=CAMBRIDGE)
        assert client.get("/methods").json()["count"] == 1

    def test_storing_it_twice_is_a_conflict(self, client):
        client.post("/methods", json=CAMBRIDGE)
        response = client.post("/methods", json=CAMBRIDGE)
        assert response.status_code == 409
        assert response.json()["detail"]["reason"] == "already-exists"


class TestFetching:
    def test_it_finds_a_stored_method(self, seeded):
        response = seeded.get("/methods/Cambridge Surprise Major")
        assert response.status_code == 200
        assert response.json()["stage"] == 8

    def test_lookup_ignores_case(self, seeded):
        assert seeded.get("/methods/cambridge surprise major").status_code == 200

    def test_something_missing_is_a_404(self, seeded):
        response = seeded.get("/methods/Nowhere Surprise Major")
        assert response.status_code == 404
        assert response.json()["detail"]["reason"] == "not-found"


class TestListing:
    def test_it_lists_everything(self, seeded):
        assert seeded.get("/methods").json()["count"] == 16

    def test_it_filters_by_name(self, seeded):
        body = seeded.get("/methods", params={"name": "cambridge"}).json()
        assert [m["title"] for m in body["methods"]] == [
            "Cambridge Surprise Minor",
            "Cambridge Surprise Major",
        ]

    def test_it_filters_by_stage(self, seeded):
        body = seeded.get("/methods", params={"stage": 6}).json()
        assert all(m["stage"] == 6 for m in body["methods"])

    def test_it_filters_by_class(self, seeded):
        body = seeded.get("/methods", params={"classification": "Surprise", "stage": 8}).json()
        assert body["count"] == 6

    def test_a_filter_matching_nothing_gives_an_empty_list(self, seeded):
        body = seeded.get("/methods", params={"name": "nowhere"}).json()
        assert body == {"count": 0, "methods": []}

    def test_a_stage_out_of_range_is_rejected(self, seeded):
        assert seeded.get("/methods", params={"stage": 99}).status_code == 422


class TestDeleting:
    def test_a_method_can_be_deleted(self, seeded):
        assert seeded.delete("/methods/Plain Bob Minor").status_code == 204

    def test_it_is_gone_afterwards(self, seeded):
        seeded.delete("/methods/Plain Bob Minor")
        assert seeded.get("/methods/Plain Bob Minor").status_code == 404

    def test_deleting_something_missing_is_a_404(self, seeded):
        assert seeded.delete("/methods/Nowhere Surprise Major").status_code == 404


class TestLines:
    def test_it_gives_a_bell_its_line(self, seeded):
        body = seeded.get("/methods/Plain Bob Minor/line/1").json()
        assert body["places"][:4] == [1, 2, 3, 4]
        assert "1 to 6 up" in body["described"]

    def test_the_grid_marks_the_bell(self, seeded):
        body = seeded.get("/methods/Plain Bob Minor/line/2").json()
        assert body["grid"][0] == "1*3456"

    def test_a_bell_that_is_not_there_is_unprocessable(self, seeded):
        assert seeded.get("/methods/Plain Bob Minor/line/9").status_code == 422

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        assert seeded.get("/methods/Nowhere Surprise Major/line/1").status_code == 404


class TestFalseness:
    def test_it_lists_false_course_heads(self, seeded):
        body = seeded.get("/methods/Cambridge Surprise Major/falseness").json()
        assert len(body) == 20
        assert body[0]["clashes"] >= body[-1]["clashes"]

    def test_the_limit_can_be_set(self, seeded):
        body = seeded.get("/methods/Cambridge Surprise Major/falseness", params={"limit": 3}).json()
        assert len(body) == 3

    def test_a_silly_limit_is_rejected(self, seeded):
        response = seeded.get("/methods/Cambridge Surprise Major/falseness", params={"limit": 0})
        assert response.status_code == 422


class TestPlaceBells:
    def test_plain_bob_major_runs_two_four_six_eight_seven_five_three(self, seeded):
        assert seeded.get("/methods/Plain Bob Major/place-bells").json() == [2, 4, 6, 8, 7, 5, 3]

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        assert seeded.get("/methods/Nowhere Surprise Major/place-bells").status_code == 404
