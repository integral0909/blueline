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
