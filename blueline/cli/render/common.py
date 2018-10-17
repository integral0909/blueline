"""Pieces every table is built out of.

Five of the tables here were the same shape: a title, a dim column of field
names and a column of values, filled in a row at a time. They are one function
now, because the third time somebody adds a field to one of them and it comes
out styled differently to the others is one time too many.
"""

from __future__ import annotations

from collections.abc import Iterable

from blueline.cli.table import Console
from blueline.cli.table import Table

from blueline.core.stage import bell_symbol

#: A pair a field table is filled from. None for the value means leave it out,
#: which saves every caller writing the same if around the same add_row.
Field = tuple[str, str | None]


def bells(order: tuple[int, ...] | list[int]) -> str:
    """A run of bells written the way a ringer writes them."""
    return "".join(bell_symbol(bell) for bell in order)


def yes_no(value: bool, otherwise: str = "no") -> str:
    """How a table says whether something is so."""
    return "yes" if value else otherwise


def fields(title: str, rows: Iterable[Field]) -> Table:
    """One thing described down the page rather than across it."""
    table = Table(title=title, show_header=False, title_justify="left")
    table.add_column("field", style="dim")
    table.add_column("value")
    for name, value in rows:
        if value is not None:
            table.add_row(name, value)
    return table


def listing(title: str, columns: Iterable[tuple[str, dict[str, object]]]) -> Table:
    """Many of something, one per line."""
    table = Table(title=title)
    for name, options in columns:
        table.add_column(name, **options)
    return table


def console(quiet: bool = False) -> Console:
    """A console, or one that swallows everything when asked to be quiet."""
    return Console(quiet=quiet)
