"""Call changes over http."""

from __future__ import annotations


def a_calling(**over) -> dict:
    body = {"calling": "2 to 3; 4 to 5", "stage": 8}
    body.update(over)
    return body


class TestProving:
    def test_a_calling_is_rung_through(self, client):
        response = client.post("/callchanges/prove", json=a_calling())
        assert response.status_code == 200
        assert response.json()["calls"] == 2

    def test_the_rows_come_back(self, client):
        body = client.post("/callchanges/prove", json=a_calling()).json()
        assert len(body["rows"]) == 3

    def test_the_first_row_is_where_they_started(self, client):
        body = client.post("/callchanges/prove", json=a_calling()).json()
        assert body["rows"][0]["call"] == "start"

    def test_it_says_the_calls_back(self, client):
        body = client.post("/callchanges/prove", json=a_calling()).json()
        assert body["said"] == ["2 to 3", "4 to 5"]

    def test_devon_gets_its_calls_back_the_way_it_gave_them(self, client):
        # Up-called, "3 to 2" puts the 2 after the 3, which is the same pair
        # a down-called "2 to 3" moves. It has to read back as it was given.
        body = client.post(
            "/callchanges/prove", json=a_calling(calling="3 to 2", style="up")
        ).json()
        assert body["said"] == ["3 to 2"]
        assert body["finish"] == "13245678"

    def test_a_style_nobody_uses_is_refused(self, client):
        response = client.post("/callchanges/prove", json=a_calling(style="sideways"))
        assert response.status_code == 422

    def test_an_impossible_call_is_refused(self, client):
        response = client.post("/callchanges/prove", json=a_calling(calling="2 to 5"))
        assert response.status_code == 422

    def test_a_calling_that_does_not_parse(self, client):
        response = client.post("/callchanges/prove", json=a_calling(calling="stand"))
        assert response.status_code == 422

    def test_a_touch_can_start_anywhere(self, client):
        body = client.post(
            "/callchanges/prove", json=a_calling(calling="2 to 3", start="13245678")
        ).json()
        assert body["start"] == "13245678"

    def test_a_call_that_stands_still_is_counted(self, client):
        body = client.post("/callchanges/prove", json=a_calling(calling="3 to 2")).json()
        assert body["stood_still"] == 1


class TestRouting:
    def test_it_reaches_queens(self, client):
        body = client.post("/callchanges/route", json={"target": "queens", "stage": 8}).json()
        assert body["finish"] == "13572468"

    def test_the_named_change_is_noticed(self, client):
        body = client.post("/callchanges/route", json={"target": "queens", "stage": 8}).json()
        assert "queens" in body["named_reached"]

    def test_a_row_can_be_given(self, client):
        body = client.post("/callchanges/route", json={"target": "13245678", "stage": 8}).json()
        assert body["calls"] == 1

    def test_somewhere_nobody_rings(self, client):
        response = client.post("/callchanges/route", json={"target": "weasels", "stage": 8})
        assert response.status_code == 422

    def test_the_wrong_number_of_bells(self, client):
        response = client.post("/callchanges/route", json={"target": "123456", "stage": 8})
        assert response.status_code == 422
