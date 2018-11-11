"""Handing back part of a listing rather than all of it.

Six endpoints each had a listing shape of their own, all the same two fields
under different names: a count, and the items under whatever the subject was
called. A client had to know that methods come back under "methods" and towers
under "towers", which is a thing to remember for no reason.

They are one page now, and the page carries what a client needs to walk a long
listing: how many there are altogether, where this slice starts, and where the
next one begins. A library with the council's thirty thousand methods in it
cannot be handed over in one response, and finding that out by trying is not a
good way to find it out.

Paged in the handler rather than in the query. The services answer with lists
and the counting is cheap next to the proving that produced them, so pushing
limit and offset down into every repository would be work in the wrong place.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: How much comes back when nobody says. Enough for a tower's library.
DEFAULT_LIMIT = 50
#: The most anybody can ask for in one go.
MOST = 500


class Paging:
    """Where in a listing a caller wants to be."""

    def __init__(self, offset: int = 0, limit: int = DEFAULT_LIMIT) -> None:
        self.offset = offset
        self.limit = limit

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Paging):
            return NotImplemented
        return (self.offset, self.limit) == (other.offset, other.limit)

    def __repr__(self) -> str:
        return f"Paging(offset={self.offset}, limit={self.limit})"


def page_of(everything: List[Any], where: Optional[Paging] = None) -> Dict[str, Any]:
    """A page out of a list somebody already has in hand."""
    at = where or Paging()
    start = max(0, at.offset)
    taken = everything[start: start + max(0, at.limit)]
    after = start + len(taken)
    return {
        "total": len(everything),
        "offset": start,
        "limit": at.limit,
        "count": len(taken),
        "items": taken,
        # Where to ask for the next page, or nothing if this is the last one.
        "next_offset": after if after < len(everything) else None,
    }


def paging(request: Any) -> Paging:
    """Where in a listing the caller wants to be, on every listing alike."""
    from blueline.api.validate import query_whole

    offset = query_whole(request, "offset", default=0, least=0)
    limit = query_whole(request, "limit", default=DEFAULT_LIMIT, least=1, most=MOST)
    return Paging(offset=offset or 0, limit=limit or DEFAULT_LIMIT)
