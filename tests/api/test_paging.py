"""Handing back part of a listing rather than all of it."""

from __future__ import annotations

from typing import List

from blueline.api.paging import DEFAULT_LIMIT, MOST, Page, Paging, page_of


class TestPageOf:
    def test_everything_fits_in_one_page(self) -> None:
        page = page_of([1, 2, 3])
        assert page.items == [1, 2, 3]
        assert page.total == 3

    def test_a_short_limit_cuts_it(self) -> None:
        page = page_of([1, 2, 3, 4], Paging(limit=2))
        assert page.items == [1, 2]
        assert page.count == 2

    def test_the_total_is_everything_not_the_page(self) -> None:
        assert page_of([1, 2, 3, 4], Paging(limit=2)).total == 4

    def test_an_offset_skips(self) -> None:
        assert page_of([1, 2, 3, 4], Paging(offset=2, limit=2)).items == [3, 4]

    def test_it_says_where_the_next_page_starts(self) -> None:
        assert page_of([1, 2, 3, 4], Paging(limit=2)).next_offset == 2

    def test_the_last_page_says_there_is_no_more(self) -> None:
        page = page_of([1, 2, 3, 4], Paging(offset=2, limit=2))
        assert page.next_offset is None
        assert not page.has_more

    def test_walking_a_listing_gets_everything_once(self) -> None:
        everything = list(range(17))
        seen: List[int] = []
        where = Paging(offset=0, limit=5)
        while True:
            page = page_of(everything, where)
            seen.extend(page.items)
            if page.next_offset is None:
                break
            where = Paging(offset=page.next_offset, limit=5)
        assert seen == everything

    def test_an_offset_past_the_end_gives_nothing(self) -> None:
        page = page_of([1, 2, 3], Paging(offset=99))
        assert page.items == []
        assert page.next_offset is None

    def test_an_empty_listing(self) -> None:
        page = page_of([])
        assert page.total == 0
        assert not page.has_more

    def test_a_negative_offset_starts_at_the_beginning(self) -> None:
        assert page_of([1, 2, 3], Paging(offset=-5)).offset == 0


class TestDefaults:
    def test_the_default_limit_is_a_towers_library(self) -> None:
        assert page_of(list(range(200))).count == DEFAULT_LIMIT

    def test_nobody_can_ask_for_everything(self) -> None:
        assert MOST < 10000

    def test_a_page_is_generic_over_what_is_in_it(self) -> None:
        page: Page[str] = page_of(["a", "b"])
        assert page.items == ["a", "b"]


class TestOverHttp:
    def test_a_listing_carries_the_page(self, seeded):
        body = seeded.get("/methods").json()
        assert set(body) == {"total", "offset", "limit", "items", "count", "next_offset"}

    def test_it_can_be_cut_short(self, seeded):
        body = seeded.get("/methods", params={"limit": 3}).json()
        assert body["count"] == 3
        assert body["total"] > 3

    def test_it_says_where_to_go_next(self, seeded):
        body = seeded.get("/methods", params={"limit": 3}).json()
        assert body["next_offset"] == 3

    def test_the_next_page_is_different(self, seeded):
        first = seeded.get("/methods", params={"limit": 3}).json()
        second = seeded.get("/methods", params={"limit": 3, "offset": 3}).json()
        assert first["items"] != second["items"]

    def test_the_last_page_says_so(self, seeded):
        total = seeded.get("/methods").json()["total"]
        body = seeded.get("/methods", params={"limit": 5, "offset": total - 1}).json()
        assert body["next_offset"] is None

    def test_a_limit_of_nothing_is_refused(self, seeded):
        assert seeded.get("/methods", params={"limit": 0}).status_code == 422

    def test_asking_for_more_than_the_most_is_refused(self, seeded):
        assert seeded.get("/methods", params={"limit": MOST + 1}).status_code == 422

    def test_a_negative_offset_is_refused(self, seeded):
        assert seeded.get("/methods", params={"offset": -1}).status_code == 422

    def test_every_listing_pages_the_same_way(self, seeded):
        for path in ("/methods", "/performances", "/towers", "/ringers", "/competitions"):
            body = seeded.get(path, params={"limit": 1}).json()
            assert "next_offset" in body, path
