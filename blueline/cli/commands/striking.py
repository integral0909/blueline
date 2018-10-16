"""Commands for judging striking.

The times come from a file rather than the command line. A quarter peal is
five thousand blows and nobody is typing those as arguments. One number per
line, or several to a line separated by whitespace, because a recorder writes
whichever it feels like and both read the same.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


from blueline.cli.declare import Arg, BadParameter, Group, Opt
from blueline.cli import render
from blueline.cli.commands.common import show, unwrap
from blueline.service import striking as service

app = Group()

COMMENT = "#"
#: What separates a band's name from its times in a competition file.
BAND_MARK = ":"


def read_times(text: str) -> list[float]:
    """Every number in a file, in the order it was written."""
    times: list[float] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        for word in line.split():
            try:
                times.append(float(word))
            except ValueError:
                raise BadParameter(f"line {number}: {word!r} is not a time") from None
    return times


def read_attempts(text: str) -> dict[str, list[float]]:
    """A competition file: a band name, a colon, and then its times.

    Times may run on over as many lines as they like until the next name, so a
    recorder can paste a column in without having to join it up first.
    """
    attempts: dict[str, list[float]] = {}
    band: str | None = None
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        if BAND_MARK in line:
            name, rest = line.split(BAND_MARK, 1)
            band = name.strip()
            if not band:
                raise BadParameter(f"line {number}: a band needs a name")
            attempts.setdefault(band, [])
            line = rest.strip()
            if not line:
                continue
        if band is None:
            raise BadParameter(f"line {number}: times before any band was named")
        attempts[band].extend(read_times(line))
    if not attempts:
        raise BadParameter("no bands in that file")
    return attempts


@app.command(name="strike")
def mark_attempt(
    path: Path = Arg(..., exists=True, readable=True, help="A file of blow times."),
    stage: int = Arg(..., help="How many bells were ringing."),
    band: Optional[str] = Opt(None, "--band", "-b", help="Who rang it."),
    threshold: float = Opt(0.10, "--threshold", "-t", help="What counts as a fault."),
) -> None:
    """Judge one band's striking."""
    report = unwrap(
        service.mark(
            band or path.stem,
            read_times(path.read_text()),
            stage,
            threshold=threshold,
        )
    )
    show(render.striking_table([report]))


@app.command(name="compete")
def judge_competition(
    path: Path = Arg(..., exists=True, readable=True, help="A competition file."),
    stage: int = Arg(..., help="How many bells were ringing."),
    threshold: float = Opt(0.10, "--threshold", "-t", help="What counts as a fault."),
) -> None:
    """Put a competition's bands in order of merit."""
    reports = unwrap(
        service.order_of_merit(read_attempts(path.read_text()), stage, threshold=threshold)
    )
    show(render.striking_table(reports))
