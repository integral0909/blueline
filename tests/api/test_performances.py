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


class TestTotals:
    def test_an_empty_store_totals_nothing(self, seeded):
        body = seeded.get("/performances/totals").json()
        assert body["performances"] == 0
        assert body["summary"] == "nothing rung"

    def test_it_counts_what_is_there(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance(length=1250))
        body = seeded.get("/performances/totals").json()
        assert body["performances"] == 2
        assert body["peals"] == 1
        assert body["quarters"] == 1

    def test_the_three_kinds_add_up(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance(length=224))
        body = seeded.get("/performances/totals").json()
        assert body["peals"] + body["quarters"] + body["touches"] == body["performances"]

    def test_it_totals_the_changes(self, seeded):
        seeded.post("/performances", json=a_performance())
        assert seeded.get("/performances/totals").json()["changes"] == 5024

    def test_it_gives_the_dates_it_spans(self, seeded):
        seeded.post("/performances", json=a_performance(rang_on="2023-01-05"))
        seeded.post("/performances", json=a_performance(rang_on="2023-06-01"))
        body = seeded.get("/performances/totals").json()
        assert body["first"] == "2023-01-05"
        assert body["last"] == "2023-06-01"

    def test_it_gives_a_leaderboard_of_ringers(self, seeded):
        seeded.post("/performances", json=a_performance())
        body = seeded.get("/performances/totals").json()
        assert body["top_ringers"][0]["count"] == 1

    def test_it_gives_a_leaderboard_of_methods(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance())
        body = seeded.get("/performances/totals").json()
        assert body["top_methods"][0] == {"name": "Cambridge Surprise Major", "count": 2}

    def test_the_leaderboards_can_be_capped(self, seeded):
        seeded.post("/performances", json=a_performance())
        body = seeded.get("/performances/totals", params={"top": 3}).json()
        assert len(body["top_ringers"]) == 3

    def test_it_can_be_narrowed_to_a_place(self, seeded):
        seeded.post("/performances", json=a_performance())
        seeded.post("/performances", json=a_performance(place="St Mary, Ashcombe"))
        body = seeded.get("/performances/totals", params={"place": "Ashcombe"}).json()
        assert body["performances"] == 1

    def test_it_breaks_down_by_stage(self, seeded):
        seeded.post("/performances", json=a_performance())
        assert seeded.get("/performances/totals").json()["by_stage"] == {"8": 1}

    def test_totals_is_not_read_as_a_performance_id(self, seeded):
        # It sits above the parameterised route, or it comes back a 422.
        assert seeded.get("/performances/totals").status_code == 200


class TestTowerLink:
    def _towers(self, seeded):
        seeded.post(
            "/towers", json={"place": "St Andrew, Marchgate", "bells": 8, "tenor": "23-1-14"}
        )
        seeded.post("/towers", json={"place": "St Mary, Ashcombe", "bells": 6, "tenor": "8-0-0"})

    def test_it_links_the_tower_when_the_place_matches(self, seeded):
        self._towers(seeded)
        body = seeded.post("/performances", json=a_performance()).json()
        assert body["tower"] == "St Andrew, Marchgate"

    def test_a_place_with_no_tower_is_left_unlinked(self, seeded):
        self._towers(seeded)
        body = seeded.post("/performances", json=a_performance(place="Somewhere else")).json()
        assert body["tower"] is None

    def test_with_no_towers_stored_it_is_still_unlinked(self, seeded):
        assert seeded.post("/performances", json=a_performance()).json()["tower"] is None

    def test_a_tower_too_small_for_the_stage_is_unprocessable(self, seeded):
        self._towers(seeded)
        response = seeded.post(
            "/performances", json=a_performance(place="St Mary, Ashcombe", stage=8)
        )
        assert response.status_code == 422
        assert "cannot ring 8" in response.json()["detail"]["detail"]

    def test_nothing_is_stored_when_the_tower_refuses(self, seeded):
        self._towers(seeded)
        seeded.post("/performances", json=a_performance(place="St Mary, Ashcombe", stage=8))
        assert seeded.get("/performances").json()["count"] == 0


class TestDuration:
    def test_a_peal_carries_how_long_it_took(self, seeded):
        body = seeded.post("/performances", json=a_performance()).json()
        assert 150 < body["duration_minutes"] < 180

    def test_a_quarter_takes_less(self, seeded):
        peal = seeded.post("/performances", json=a_performance()).json()
        quarter = seeded.post("/performances", json=a_performance(length=1250)).json()
        assert quarter["duration_minutes"] < peal["duration_minutes"]

    def test_the_board_says_how_long(self, seeded):
        body = seeded.post("/performances", json=a_performance()).json()
        assert any("h " in line for line in body["board"])


class TestSpeed:
    def test_the_default_gives_about_three_hours(self, seeded):
        body = seeded.post("/performances", json=a_performance()).json()
        assert 150 < body["duration_minutes"] < 180

    def test_a_faster_band_takes_less_time(self, seeded):
        quick = seeded.post("/performances", json=a_performance(peal_speed=40)).json()
        slow = seeded.post("/performances", json=a_performance(peal_speed=20)).json()
        assert quick["duration_minutes"] < slow["duration_minutes"]

    def test_a_speed_of_nothing_is_rejected_by_the_schema(self, seeded):
        assert seeded.post("/performances", json=a_performance(peal_speed=0)).status_code == 422

    def test_an_impossible_speed_is_rejected(self, seeded):
        assert seeded.post("/performances", json=a_performance(peal_speed=200)).status_code == 422
