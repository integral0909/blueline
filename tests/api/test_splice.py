GROUP = [
    "Cambridge Surprise Major",
    "Yorkshire Surprise Major",
    "Superlative Surprise Major",
    "Lincolnshire Surprise Major",
]


class TestSplice:
    def test_seven_leads_of_the_group_come_round_true(self, seeded):
        response = seeded.post("/splice", json={"titles": GROUP, "order": "CYSLCYS"})
        assert response.status_code == 200
        body = response.json()
        assert body["is_ringable"]
        assert body["length"] == 224

    def test_it_names_the_methods_used(self, seeded):
        body = seeded.post("/splice", json={"titles": GROUP, "order": "CYC"}).json()
        assert body["methods_used"] == ["Cambridge", "Yorkshire"]

    def test_a_calling_can_be_given(self, seeded):
        body = seeded.post(
            "/splice", json={"titles": GROUP, "order": "CYSL", "calling": "p-pp"}
        ).json()
        assert body["calling"] == "p-pp"

    def test_a_touch_that_does_not_come_round_says_so(self, seeded):
        body = seeded.post("/splice", json={"titles": GROUP, "order": "CY"}).json()
        assert not body["comes_round"]
        assert "does not come round" in body["summary"]

    def test_methods_that_do_not_splice_are_unprocessable(self, seeded):
        response = seeded.post(
            "/splice",
            json={"titles": [*GROUP, "Bristol Surprise Major"], "order": "CYSLB"},
        )
        assert response.status_code == 422
        assert "lead heads differ" in response.json()["detail"]["detail"]

    def test_splicing_across_stages_is_unprocessable(self, seeded):
        response = seeded.post(
            "/splice",
            json={"titles": ["Cambridge Surprise Major", "London Surprise Minor"], "order": "CL"},
        )
        assert response.status_code == 422

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        response = seeded.post("/splice", json={"titles": ["Nowhere Surprise Major"], "order": "N"})
        assert response.status_code == 404

    def test_an_initial_it_does_not_know_is_unprocessable(self, seeded):
        response = seeded.post("/splice", json={"titles": GROUP, "order": "CZ"})
        assert response.status_code == 422

    def test_an_empty_order_is_rejected_by_the_schema(self, seeded):
        response = seeded.post("/splice", json={"titles": GROUP, "order": "   "})
        assert response.status_code == 422

    def test_no_methods_at_all_is_rejected_by_the_schema(self, seeded):
        response = seeded.post("/splice", json={"titles": [], "order": "C"})
        assert response.status_code == 422

    def test_it_counts_the_music(self, seeded):
        body = seeded.post("/splice", json={"titles": GROUP, "order": "CYSLCYS"}).json()
        assert body["music"]["named"]["rounds"] == 1
