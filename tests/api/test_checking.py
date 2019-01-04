"""Looking over the library, over http."""

from __future__ import annotations


class TestOverHttp:
    def test_a_clean_library(self, seeded):
        body = seeded.get("/check").json()
        assert body["clean"] is True
        assert body["problems"] == []

    def test_it_says_how_much_it_looked_at(self, seeded):
        assert seeded.get("/check").json()["checked"] > 0

    def test_it_summarises(self, seeded):
        assert "checked" in seeded.get("/check").json()["summary"]

    def test_an_empty_collection_is_a_note(self, seeded):
        seeded.post("/collections", json={"name": "Empty", "titles": []})
        body = seeded.get("/check").json()
        assert any(note["subject"] == "Empty" for note in body["notes"])

    def test_a_note_is_not_a_problem(self, seeded):
        seeded.post("/collections", json={"name": "Empty", "titles": []})
        assert seeded.get("/check").json()["clean"] is True

    def test_the_thorough_pass_looks_at_more(self, seeded):
        seeded.post(
            "/compositions",
            json={"title": "A 60", "method": "Plain Bob Minor", "calling": "---"},
        )
        quick = seeded.get("/check").json()["checked"]
        slow = seeded.get("/check", params={"thorough": True}).json()["checked"]
        assert slow > quick

    def test_it_changes_nothing(self, seeded):
        before = seeded.get("/methods").json()["total"]
        seeded.get("/check", params={"thorough": True})
        assert seeded.get("/methods").json()["total"] == before

    def test_the_check_route_is_not_read_as_something_else(self, seeded):
        assert seeded.get("/check").status_code == 200
