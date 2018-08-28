class TestCourse:
    def test_it_reports_the_plain_course(self, seeded):
        response = seeded.get("/methods/Cambridge Surprise Minor/course")
        assert response.status_code == 200
        assert response.json()["length"] == 120

    def test_a_plain_course_is_ringable(self, seeded):
        assert seeded.get("/methods/Plain Bob Minor/course").json()["is_ringable"]

    def test_it_is_all_plain_leads(self, seeded):
        assert seeded.get("/methods/Plain Bob Minor/course").json()["calling"] == "ppppp"

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        assert seeded.get("/methods/Nowhere Surprise Major/course").status_code == 404


class TestProve:
    def test_the_three_bob_touch(self, seeded):
        response = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "---"})
        assert response.status_code == 200
        body = response.json()
        assert body["length"] == 36
        assert body["comes_round"]
        assert body["is_true"]

    def test_the_classic_hundred_and_twenty(self, seeded):
        response = seeded.post(
            "/methods/Plain Bob Doubles/prove", json={"calling": "ppp-", "times": 3}
        )
        body = response.json()
        assert body["length"] == 120
        assert body["is_extent"]

    def test_a_touch_that_does_not_come_round(self, seeded):
        body = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "--"}).json()
        assert not body["comes_round"]
        assert not body["is_ringable"]
        assert "does not come round" in body["summary"]

    def test_a_false_touch_names_its_repeats(self, seeded):
        body = seeded.post(
            "/methods/Plain Bob Doubles/prove", json={"calling": "pppp", "times": 2}
        ).json()
        assert not body["is_true"]
        assert body["repeats"]
        assert "row" in body["repeats"][0]

    def test_it_counts_the_music(self, seeded):
        body = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "---"}).json()
        assert body["music"]["named"]["rounds"] == 1

    def test_a_calling_it_cannot_read_is_unprocessable(self, seeded):
        response = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "zzz"})
        assert response.status_code == 422
        assert response.json()["detail"]["reason"] == "invalid"

    def test_an_empty_calling_is_rejected_by_the_schema(self, seeded):
        assert (
            seeded.post("/methods/Plain Bob Minor/prove", json={"calling": ""}).status_code == 422
        )

    def test_a_silly_repeat_count_is_rejected(self, seeded):
        response = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "-", "times": 0})
        assert response.status_code == 422

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        response = seeded.post("/methods/Nowhere Surprise Major/prove", json={"calling": "-"})
        assert response.status_code == 404

    def test_grandsire_takes_its_own_calls(self, seeded):
        response = seeded.post("/methods/Grandsire Doubles/prove", json={"calling": "-p-"})
        assert response.status_code == 200


class TestSearch:
    def test_it_finds_callings(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/search", params={"max_found": 3})
        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 3
        assert body["found"][0]["calling"] == "ppppp"

    def test_it_says_which_calls_it_used(self, seeded):
        body = seeded.get(
            "/methods/Plain Bob Minor/search", params={"allowed": "p-", "max_found": 2}
        ).json()
        assert body["looked_at"] == "p-"

    def test_it_honours_a_minimum_length(self, seeded):
        body = seeded.get(
            "/methods/Plain Bob Doubles/search", params={"min_length": 100, "max_found": 3}
        ).json()
        assert all(entry["length"] >= 100 for entry in body["found"])

    def test_it_says_whether_it_finished(self, seeded):
        body = seeded.get("/methods/Plain Bob Minor/search", params={"max_found": 2}).json()
        assert "exhausted" in body
        assert "callings" in body["summary"]

    def test_a_call_the_method_does_not_have_is_unprocessable(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/search", params={"allowed": "pz"})
        assert response.status_code == 422

    def test_a_backwards_range_is_unprocessable(self, seeded):
        response = seeded.get(
            "/methods/Plain Bob Minor/search", params={"min_length": 500, "max_length": 100}
        )
        assert response.status_code == 422

    def test_a_silly_limit_is_rejected_by_the_schema(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/search", params={"max_found": 0})
        assert response.status_code == 422

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        assert seeded.get("/methods/Nowhere Surprise Major/search").status_code == 404


class TestStanding:
    def test_a_short_touch_counts_as_a_touch(self, seeded):
        body = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "---"}).json()
        assert body["standing"]["counts_as"] == "touch"

    def test_it_says_how_far_off_a_quarter_it_is(self, seeded):
        body = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "---"}).json()
        assert body["standing"]["short_by"] == 1260 - 36

    def test_a_quarter_length_counts_as_a_quarter(self, seeded):
        body = seeded.post(
            "/methods/Plain Bob Minor/prove", json={"calling": "---", "times": 35}
        ).json()
        assert body["length"] == 1260
        assert body["standing"]["counts_as"] == "quarter peal"

    def test_the_plain_course_carries_a_standing_too(self, seeded):
        body = seeded.get("/methods/Cambridge Surprise Major/course").json()
        assert body["standing"]["counts_as"] == "touch"

    def test_a_splice_carries_one_as_well(self, seeded):
        body = seeded.post(
            "/splice",
            json={
                "titles": ["Cambridge Surprise Major", "Yorkshire Surprise Major"],
                "order": "CYCYCYC",
            },
        ).json()
        assert "standing" in body
