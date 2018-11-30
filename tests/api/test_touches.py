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
        assert response.json()["reason"] == "invalid"

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


class TestEarlyRounds:
    def test_a_touch_that_runs_to_the_end_reports_nothing(self, seeded):
        body = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "---"}).json()
        assert body["early_rounds"] is None

    def test_a_touch_that_comes_round_early_says_where(self, seeded):
        body = seeded.post(
            "/methods/Plain Bob Minor/prove", json={"calling": "---", "times": 2}
        ).json()
        assert body["early_rounds"]["row"] == 36
        assert body["early_rounds"]["lead"] == 3
        assert body["early_rounds"]["at_lead_end"]

    def test_the_summary_leads_with_it(self, seeded):
        body = seeded.post(
            "/methods/Plain Bob Minor/prove", json={"calling": "---", "times": 2}
        ).json()
        assert "comes round early" in body["summary"]

    def test_a_touch_stands_at_a_lead_end(self, seeded):
        body = seeded.post("/methods/Plain Bob Minor/prove", json={"calling": "---"}).json()
        assert body["stands_at_a_lead_end"]

    def test_a_plain_course_reports_it_too(self, seeded):
        body = seeded.get("/methods/Plain Bob Minor/course").json()
        assert body["early_rounds"] is None
        assert body["stands_at_a_lead_end"]


class TestForLength:
    def test_it_finds_a_touch_at_the_length(self, seeded):
        response = seeded.get(
            "/methods/Plain Bob Doubles/for-length",
            params={"length": 120, "max_found": 1},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["reachable"]
        assert body["found"][0]["length"] == 120

    def test_a_length_past_the_extent_is_reported_not_refused(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/for-length", params={"length": 1260})
        assert response.status_code == 200
        body = response.json()
        assert not body["reachable"]
        assert "only 720 rows" in body["why_not"]

    def test_a_length_that_does_not_divide_into_leads(self, seeded):
        body = seeded.get("/methods/Plain Bob Major/for-length", params={"length": 1250}).json()
        assert not body["reachable"]
        assert "16 changes to a lead" in body["why_not"]

    def test_a_tolerance_can_bring_it_into_range(self, seeded):
        body = seeded.get(
            "/methods/Plain Bob Major/for-length",
            params={"length": 1250, "tolerance": 2, "max_found": 1},
        ).json()
        assert body["reachable"]

    def test_it_says_what_it_was_looking_for(self, seeded):
        body = seeded.get(
            "/methods/Plain Bob Doubles/for-length",
            params={"length": 120, "max_found": 1},
        ).json()
        assert body["wanted"] == 120
        assert body["target"] == "120"

    def test_a_length_of_nothing_is_rejected_by_the_schema(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/for-length", params={"length": 0})
        assert response.status_code == 422

    def test_a_call_it_does_not_have_is_unprocessable(self, seeded):
        response = seeded.get(
            "/methods/Plain Bob Minor/for-length",
            params={"length": 60, "allowed": "pz"},
        )
        assert response.status_code == 422

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        response = seeded.get("/methods/Nowhere Surprise Major/for-length", params={"length": 120})
        assert response.status_code == 404


class TestPositions:
    def test_it_names_the_positions(self, seeded):
        body = seeded.get("/methods/Plain Bob Major/positions").json()
        assert body[-1]["name"] == "Home"

    def test_there_is_one_per_lead(self, seeded):
        assert len(seeded.get("/methods/Plain Bob Major/positions").json()) == 7

    def test_it_says_where_the_tenor_is(self, seeded):
        body = seeded.get("/methods/Plain Bob Major/positions").json()
        assert body[-1]["tenor_place"] == 8

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        assert seeded.get("/methods/Nowhere Surprise Major/positions").status_code == 404


class TestCall:
    def test_it_proves_a_touch_called_by_position(self, seeded):
        response = seeded.post("/methods/Plain Bob Major/call", json={"called": ["Home"]})
        assert response.status_code == 200
        assert response.json()["leads"] == 7

    def test_two_homes_run_on_into_another_course(self, seeded):
        body = seeded.post(
            "/methods/Plain Bob Major/call",
            json={"called": ["Wrong", "Home", "Home"]},
        ).json()
        assert body["leads"] == 14

    def test_the_calling_comes_back_in_symbols(self, seeded):
        body = seeded.post("/methods/Plain Bob Major/call", json={"called": ["Home"]}).json()
        assert body["calling"] == "pppppp-"

    def test_calling_nothing_is_the_plain_course(self, seeded):
        body = seeded.post("/methods/Plain Bob Major/call", json={"called": []}).json()
        assert body["length"] == 112

    def test_a_position_it_does_not_know_is_unprocessable(self, seeded):
        response = seeded.post("/methods/Plain Bob Major/call", json={"called": ["Sideways"]})
        assert response.status_code == 422

    def test_a_method_that_is_not_there_is_a_404(self, seeded):
        response = seeded.post("/methods/Nowhere Surprise Major/call", json={"called": ["Home"]})
        assert response.status_code == 404


class TestMusical:
    def test_it_ranks_what_it_finds(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/musical", params={"max_found": 30})
        assert response.status_code == 200
        assert response.json()["best"]

    def test_the_best_comes_first(self, seeded):
        body = seeded.get("/methods/Plain Bob Minor/musical", params={"max_found": 40}).json()
        scores = [entry["per_row"] for entry in body["best"]]
        assert scores == sorted(scores, reverse=True)

    def test_the_ranking_can_be_cut_short(self, seeded):
        body = seeded.get(
            "/methods/Plain Bob Minor/musical",
            params={"max_found": 40, "how_many": 3},
        ).json()
        assert len(body["best"]) <= 3

    def test_every_entry_says_where_its_music_came_from(self, seeded):
        body = seeded.get("/methods/Plain Bob Minor/musical", params={"max_found": 20}).json()
        assert all(entry["music"] for entry in body["best"])

    def test_a_method_nobody_has_stored(self, seeded):
        assert seeded.get("/methods/Weasel Major/musical").status_code == 404

    def test_a_ranking_that_holds_nothing_is_refused(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/musical", params={"how_many": 0})
        assert response.status_code == 422

    def test_the_musical_route_is_not_read_as_a_bell(self, seeded):
        response = seeded.get("/methods/Plain Bob Minor/musical", params={"max_found": 10})
        assert response.status_code == 200
