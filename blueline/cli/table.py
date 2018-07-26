"""Printing a table on a terminal.

Small on purpose. What the commands need is a title, some columns, some rows,
and the columns lined up; everything else a table library offers - colour,
boxes, wrapping, panels - is decoration this does not use.

The surface is the same handful of methods the render modules already call, so
they did not have to change when this replaced what was there before: add a
column, add a row, add a section, print it.

Overflow is handled by cutting rather than wrapping. A method title that runs
past its column is better cut short with an ellipsis than folded over two lines
and putting every other column out of line.
"""

from __future__ import annotations

import sys
from typing import Any, List, Optional, TextIO

ELLIPSIS = "…"
GAP = "  "


class Column:
    """One column, and how it wants to be laid out."""

    def __init__(
        self,
        header: str = "",
        justify: str = "left",
        style: str = "",
        overflow: str = "",
        max_width: Optional[int] = None,
        **rest: Any,
    ) -> None:
        self.header = header
        self.justify = justify
        self.style = style
        self.overflow = overflow
        self.max_width = max_width
        # Anything else a caller passed is accepted and ignored, so a render
        # module can keep saying what it means without this having to know.
        self.rest = rest


class Table:
    """A title, some columns and some rows."""

    def __init__(
        self,
        title: str = "",
        show_header: bool = True,
        title_justify: str = "left",
        **rest: Any,
    ) -> None:
        self.title = title
        self.show_header = show_header
        self.title_justify = title_justify
        self.columns: List[Column] = []
        self.rows: List[Optional[List[str]]] = []

    def add_column(self, header: str = "", **options: Any) -> None:
        self.columns.append(Column(header, **options))

    def add_row(self, *cells: Any, **_ignored: Any) -> None:
        self.rows.append(["" if cell is None else str(cell) for cell in cells])

    def add_section(self) -> None:
        """A rule between one group of rows and the next."""
        self.rows.append(None)

    @property
    def row_count(self) -> int:
        return sum(1 for row in self.rows if row is not None)

    def _cut(self, text: str, column: Column) -> str:
        limit = column.max_width
        if limit is None or len(text) <= limit:
            return text
        return text[: max(0, limit - 1)] + ELLIPSIS

    def _widths(self, body: List[List[str]]) -> List[int]:
        widths = [len(column.header) if self.show_header else 0 for column in self.columns]
        for row in body:
            for index, cell in enumerate(row):
                if index < len(widths):
                    widths[index] = max(widths[index], len(cell))
        return widths

    def lines(self) -> List[str]:
        """The table, one string per line."""
        body: List[Optional[List[str]]] = []
        for row in self.rows:
            if row is None:
                body.append(None)
                continue
            body.append(
                [
                    self._cut(cell, self.columns[index])
                    if index < len(self.columns)
                    else cell
                    for index, cell in enumerate(row)
                ]
            )

        filled = [row for row in body if row is not None]
        widths = self._widths(filled)
        out: List[str] = []
        if self.title:
            out.append(self.title)

        if self.show_header and any(column.header for column in self.columns):
            out.append(GAP.join(self._pad(column.header, widths[index], self.columns[index])
                                for index, column in enumerate(self.columns)).rstrip())
            out.append(GAP.join("-" * width for width in widths).rstrip())

        for row in body:
            if row is None:
                out.append(GAP.join("-" * width for width in widths).rstrip())
                continue
            out.append(
                GAP.join(
                    self._pad(cell, widths[index], self.columns[index])
                    if index < len(self.columns)
                    else cell
                    for index, cell in enumerate(row)
                ).rstrip()
            )
        return out

    def _pad(self, text: str, width: int, column: Column) -> str:
        if column.justify == "right":
            return text.rjust(width)
        return text.ljust(width)

    def __str__(self) -> str:
        return "\n".join(self.lines())


class Console:
    """Somewhere to print to, or nowhere when asked to be quiet."""

    def __init__(self, quiet: bool = False, stream: Optional[TextIO] = None) -> None:
        self.quiet = quiet
        self._stream = stream

    @property
    def stream(self) -> TextIO:
        # Looked up at the moment of writing rather than held. Anything that
        # swaps the stream afterwards, and the tests do it around every test,
        # would otherwise leave this holding a closed file.
        return self._stream if self._stream is not None else sys.stdout

    def print(self, renderable: Any = "") -> None:
        if self.quiet:
            return
        if isinstance(renderable, Table):
            for line in renderable.lines():
                self.stream.write(line + "\n")
        else:
            self.stream.write(str(renderable) + "\n")
