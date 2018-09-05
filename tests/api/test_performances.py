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


class TestRecording:
    def test_one_can_be_written_up(self, seeded):
        response = seeded.post("/performances", json=a_performance())
        assert response.status_code == 201
        assert response.json()["length"] == 5024

    def test_it_names_the_conductor(self, seeded):
        body = seeded.post("/performances", json=a_performance()).json()
        assert body["conductor"] == "Hana"

    def test_it_says_what_the_length_counts_as(self, seeded):
        body = seeded.post("/performances", json=a_performance()).json()
        assert body["counts_as"] == "peal"
        assert body["is_peal"]

    def test_a_quarter_says_so(self, seeded):
        body = seeded.post("/performances", json=a_performance(length=1250)).json()
        assert body["counts_as"] == "quarter peal"

    def test_it_carries_the_peal_board(self, seeded):
        body = seeded.post("/performances", json=a_performance()).json()
        assert "8 Hana (c)" in body["board"]

    def test_a_covering_tenor_is_noticed(self, seeded):
        body = seeded.post("/performances", json=a_performance(stage=7, length=5040)).json()
        assert body["has_covering_tenor"]

    def test_a_bad_date_is_unprocessable(self, seeded):
        response = seeded.post("/performances", json=a_performance(rang_on="last tuesday"))
        assert response.status_code == 422
        assert response.json()["detail"]["reason"] == "invalid"

    def test_a_repeated_ringer_is_unprocessable(self, seeded):
        response = seeded.post(
            "/performances", json=a_performance(ringers=["Ann", "Ann", "Cara", "Dan"])
        )
        assert response.status_code == 422

    def test_a_band_too_small_for_the_stage_is_unprocessable(self, seeded):
        response = seeded.post("/performances", json=a_performance(stage=12))
        assert response.status_code == 422

    def test_an_empty_title_is_rejected_by_the_schema(self, seeded):
        assert seeded.post("/performances", json=a_performance(title="  ")).status_code == 422

    def test_a_length_of_nothing_is_rejected_by_the_schema(self, seeded):
        assert seeded.post("/performances", json=a_performance(length=0)).status_code == 422

    def test_too_few_ringers_is_rejected_by_the_schema(self, seeded):
        response = seeded.post("/performances", json=a_performance(ringers=["Ann", "Bob"]))
        assert response.status_code == 422


class TestFetching:
    def test_one_can_be_fetched_back(self, seeded):
        made = seeded.post("/performances", json=a_performance()).json()
        response = seeded.get(f"/performances/{made['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "Cambridge Surprise Major"

    def test_one_that_is_not_there_is_a_404(self, seeded):
        assert seeded.get("/performances/999").status_code == 404


class TestListing:
    def test_an_empty_store_lists_nothing(self, seeded):
        assert seeded.get("/performances").json() == {"count": 0, "performances": []}

    def test_it_lists_what_is_there(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance(place="St Mary, Ashcombe"))
        assert seeded.get("/performances").json()["count"] == 2

    def test_the_most_recent_comes_first(self, seeded):
        seeded.post("/performances", json=a_performance(rang_on="2023-01-01"))
        seeded.post("/performances", json=a_performance(rang_on="2023-06-01"))
        body = seeded.get("/performances").json()
        assert body["performances"][0]["rang_on"] == "2023-06-01"

    def test_it_filters_by_place(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance(place="St Mary, Ashcombe"))
        body = seeded.get("/performances", params={"place": "Ashcombe"}).json()
        assert body["count"] == 1

    def test_it_filters_by_ringer(self, seeded):
        seeded.post("/performances", json=a_performance())
        body = seeded.get("/performances", params={"ringer": "Hana"}).json()
        assert body["count"] == 1

    def test_a_ringer_who_rang_nothing_finds_nothing(self, seeded):
        seeded.post("/performances", json=a_performance())
        assert seeded.get("/performances", params={"ringer": "Nobody"}).json()["count"] == 0

    def test_it_filters_by_length(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance(length=1250))
        body = seeded.get("/performances", params={"min_length": 5000}).json()
        assert body["count"] == 1

    def test_a_stage_out_of_range_is_rejected(self, seeded):
        assert seeded.get("/performances", params={"stage": 99}).status_code == 422
