class TestPlan:
    def test_it_plans_a_practice(self, seeded):
        response = seeded.get("/plan", params={"ringers": 8, "minutes": 60})
        assert response.status_code == 200
        body = response.json()
        assert body["used_minutes"] <= 60

    def test_it_names_what_to_ring(self, seeded):
        body = seeded.get("/plan", params={"ringers": 8, "minutes": 60}).json()
        assert body["items"]

    def test_it_says_what_is_spare(self, seeded):
        body = seeded.get("/plan", params={"ringers": 8, "minutes": 60}).json()
        assert body["spare_minutes"] == 60 - body["used_minutes"]

    def test_it_only_picks_what_the_band_can_ring(self, seeded):
        body = seeded.get("/plan", params={"ringers": 6, "minutes": 60}).json()
        assert all(title.endswith((" 5", " 6")) for title in body["titles"])

    def test_a_tower_caps_the_band(self, seeded):
        seeded.post("/towers", json={"place": "St Mary, Ashcombe", "bells": 6, "tenor": "8-0-0"})
        body = seeded.get(
            "/plan", params={"ringers": 8, "minutes": 60, "place": "St Mary, Ashcombe"}
        ).json()
        assert body["ringers"] == 6

    def test_a_tower_that_is_not_there_is_a_404(self, seeded):
        response = seeded.get("/plan", params={"ringers": 8, "minutes": 60, "place": "Nowhere"})
        assert response.status_code == 404

    def test_a_band_too_small_is_rejected_by_the_schema(self, seeded):
        assert seeded.get("/plan", params={"ringers": 2, "minutes": 60}).status_code == 422

    def test_a_practice_of_no_time_is_rejected(self, seeded):
        assert seeded.get("/plan", params={"ringers": 8, "minutes": 0}).status_code == 422

    def test_an_impossible_speed_is_rejected(self, seeded):
        response = seeded.get("/plan", params={"ringers": 8, "minutes": 60, "speed": 0})
        assert response.status_code == 422

    def test_an_empty_library_plans_nothing(self, client):
        body = client.get("/plan", params={"ringers": 8, "minutes": 60}).json()
        assert body["items"] == []


class TestRingable:
    def test_it_lists_what_a_band_could_ring(self, seeded):
        body = seeded.get("/plan/ringable", params={"ringers": 8}).json()
        assert all(title.endswith((" 7", " 8")) for title in body)

    def test_it_comes_back_sorted(self, seeded):
        body = seeded.get("/plan/ringable", params={"ringers": 8}).json()
        assert body == sorted(body)

    def test_a_band_bigger_than_anything_stored_gets_nothing(self, seeded):
        assert seeded.get("/plan/ringable", params={"ringers": 16}).json() == []

    def test_a_band_too_small_is_rejected(self, seeded):
        assert seeded.get("/plan/ringable", params={"ringers": 2}).status_code == 422


class TestByAbility:
    def _band(self, client):
        for name in ("Ann", "Bob", "Cara", "Dan", "Eve", "Finn"):
            client.post(
                "/ringers",
                json={"name": name, "can_ring": ["Plain Bob Major", "Cambridge Surprise Major"]},
            )
        client.post(
            "/ringers",
            json={
                "name": "Gus",
                "can_ring": ["Plain Bob Major"],
                "learning": ["Cambridge Surprise Major"],
            },
        )
        client.post("/ringers", json={"name": "Hana", "can_ring": ["Plain Bob Major"]})

    def test_it_only_picks_what_the_band_can_get_through(self, seeded):
        self._band(seeded)
        body = seeded.get("/plan", params={"ringers": 8, "minutes": 60}).json()
        assert body["titles"] == ["Plain 8"]

    def test_it_says_what_was_left_out(self, seeded):
        self._band(seeded)
        body = seeded.get("/plan", params={"ringers": 8, "minutes": 60}).json()
        assert "Cambridge Surprise Major" in body["beyond_the_band"]

    def test_it_can_be_told_to_ignore_the_band(self, seeded):
        self._band(seeded)
        body = seeded.get("/plan", params={"ringers": 8, "minutes": 60, "by_ability": False}).json()
        assert len(body["titles"]) > 1
        assert body["beyond_the_band"] == []

    def test_with_nobody_stored_nothing_is_filtered(self, seeded):
        body = seeded.get("/plan", params={"ringers": 8, "minutes": 60}).json()
        assert body["titles"]


class TestTerm:
    def a_term(self, **over) -> dict:
        params = {"first": "2023-09-05", "last": "2023-12-19"}
        params.update(over)
        return params

    def test_it_lays_out_the_nights(self, seeded):
        response = seeded.get("/term", params=self.a_term())
        assert response.status_code == 200
        assert response.json()["count"] > 10

    def test_every_night_is_a_tuesday(self, seeded):
        body = seeded.get("/term", params=self.a_term()).json()
        assert body["night"] == "Tuesday"

    def test_another_night_can_be_asked_for(self, seeded):
        body = seeded.get("/term", params=self.a_term(weekday=3)).json()
        assert body["night"] == "Thursday"

    def test_it_puts_something_against_each(self, seeded):
        body = seeded.get("/term", params=self.a_term()).json()
        assert all(night["method"] or night["note"] for night in body["nights"])

    def test_it_can_work_from_a_named_set(self, seeded):
        body = seeded.get("/term", params=self.a_term(working_from="the standard four")).json()
        assert body["methods"]

    def test_a_set_nobody_names(self, seeded):
        response = seeded.get("/term", params=self.a_term(working_from="the weasel four"))
        assert response.status_code == 404

    def test_more_than_a_term_is_refused(self, seeded):
        response = seeded.get("/term", params=self.a_term(last="2025-12-19"))
        assert response.status_code == 422

    def test_a_range_the_wrong_way_round(self, seeded):
        response = seeded.get("/term", params=self.a_term(last="2023-01-01"))
        assert response.status_code == 422

    def test_a_day_that_does_not_exist(self, seeded):
        assert seeded.get("/term", params=self.a_term(weekday=9)).status_code == 422
