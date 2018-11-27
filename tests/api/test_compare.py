"""Comparing methods over http."""

from __future__ import annotations

CAMBRIDGE = "Cambridge Surprise Major"
YORKSHIRE = "Yorkshire Surprise Major"
BRISTOL = "Bristol Surprise Major"


class TestOverHttp:
    def test_two_methods_can_be_compared(self, seeded):
        response = seeded.get(f"/methods/{CAMBRIDGE}/against/{YORKSHIRE}")
        assert response.status_code == 200
        assert response.json()["same"] > 0

    def test_it_says_whether_the_lead_heads_agree(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/against/{YORKSHIRE}").json()
        assert body["same_lead_head"] is True

    def test_bristol_does_not_agree(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/against/{BRISTOL}").json()
        assert body["same_lead_head"] is False

    def test_a_method_against_itself(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/against/{CAMBRIDGE}").json()
        assert body["identical"] is True
        assert body["share"] == 1.0

    def test_it_lists_where_they_part(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/against/{YORKSHIRE}").json()
        assert body["divergences"]

    def test_it_says_what_each_bell_shares(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/against/{YORKSHIRE}").json()
        assert len(body["work"]) == 8

    def test_two_stages_cannot_be_compared(self, seeded):
        response = seeded.get(f"/methods/{CAMBRIDGE}/against/Plain Bob Minor")
        assert response.status_code == 422

    def test_a_method_nobody_has_stored(self, seeded):
        assert seeded.get(f"/methods/{CAMBRIDGE}/against/Weasel Major").status_code == 404

    def test_the_nearest_can_be_asked_for(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/like").json()
        assert body["left"] == CAMBRIDGE
        assert body["right"] != CAMBRIDGE

    def test_the_nearest_is_at_the_same_stage(self, seeded):
        body = seeded.get(f"/methods/{CAMBRIDGE}/like").json()
        assert "Major" in body["right"]

    def test_a_stage_with_nothing_else_at_it(self, client):
        client.post("/methods", json={"name": "Only", "stage": 6, "notation": "x16x16x16,12"})
        assert client.get("/methods/Only Bob Minor/like").status_code == 404

    def test_the_like_route_is_not_read_as_a_bell(self, seeded):
        assert seeded.get(f"/methods/{CAMBRIDGE}/like").status_code == 200
