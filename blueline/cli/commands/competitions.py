"""Commands for striking competitions.

A sheet comes in as a file rather than as arguments. A district final has ten
bands on it and typing that as options would be worse than writing it down.

The format is one band a line: a position, a band, and a fault count, with an
optional note after a hash. It is what a judge's sheet already looks like, so
transcribing one is typing rather than translating.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional


from blueline.cli.declare import Arg, BadParameter, Group, Opt
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.cli.commands.striking import read_attempts
from blueline.core.competitions import CompetitionError, Entry
from blueline.service import competitions as service

app = Group()

COMMENT = "#"


def read_sheet(text: str) -> tuple[Entry, ...]:
    """A judge's sheet: position, band, faults, one to a line."""
    entries: list[Entry] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line, _, note = raw.partition(COMMENT)
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            raise BadParameter(f"line {number}: wanted position, band, faults")
        position, faults = parts[0], parts[-1]
        band = " ".join(parts[1:-1])
        try:
            entry = Entry(
                band=band,
                position=int(position),
                faults=int(faults),
                percentage=0.0,
                note=note.strip(),
            )
        # CompetitionError before ValueError: it is one, and catching the
        # wide one first would turn "a position starts at one" into a
        # complaint about the number not being a number.
        except CompetitionError as error:
            raise BadParameter(f"line {number}: {error}") from None
        except ValueError:
            raise BadParameter(
                f"line {number}: position and faults have to be numbers"
            ) from None
        entries.append(entry)
    if not entries:
        raise BadParameter("nobody on that sheet")
    return tuple(entries)


@app.command(name="competition")
def record_competition(
    path: Path = Arg(..., exists=True, readable=True, help="A judge's sheet."),
    name: str = Arg(..., help="What the competition is called."),
    held_on: str = Arg(..., help="When it was held, as YYYY-MM-DD."),
    stage: int = Arg(..., help="How many bells."),
    place: str = Opt("", "--place", "-p", help="Where it was rung."),
    judge: str = Opt("", "--judge", "-j", help="Who marked it."),
) -> None:
    """Write up a sheet the judge announced."""
    with changing() as store:
        view = unwrap(
            service.record(
                store.competitions,
                name=name,
                held_on=date.fromisoformat(held_on),
                stage=stage,
                entries=read_sheet(path.read_text()),
                place=place,
                judge=judge,
            )
        )
    show(render.competition_table(view))


@app.command(name="judged")
def judge_competition(
    path: Path = Arg(..., exists=True, readable=True, help="A recording."),
    name: str = Arg(..., help="What the competition is called."),
    held_on: str = Arg(..., help="When it was held, as YYYY-MM-DD."),
    stage: int = Arg(..., help="How many bells."),
    place: str = Opt("", "--place", "-p", help="Where it was rung."),
    judge: str = Opt("", "--judge", "-j", help="Who marked it."),
) -> None:
    """Mark what was recorded, then write up the sheet it comes to."""
    with changing() as store:
        view = unwrap(
            service.judge_and_record(
                store.competitions,
                name=name,
                held_on=date.fromisoformat(held_on),
                stage=stage,
                attempts=read_attempts(path.read_text()),
                place=place,
                judge=judge,
            )
        )
    show(render.competition_table(view))


@app.command(name="competitions")
def list_competitions(
    name: Optional[str] = Opt(None, "--name", "-n"),
    place: Optional[str] = Opt(None, "--place", "-p"),
    band: Optional[str] = Opt(None, "--band", "-b"),
    stage: Optional[int] = Opt(None, "--stage", "-s"),
) -> None:
    """Sheets matching everything asked for, most recent first."""
    found = unwrap(
        service.listing(stores().competitions, name=name, place=place, band=band, stage=stage)
    )
    show(render.competition_listing(found))


@app.command(name="band")
def show_band(
    band: str = Arg(..., help="Whose record to look up."),
) -> None:
    """Where a band has come each year it entered."""
    view = unwrap(service.band_progress(stores().competitions, band))
    show(render.progress_table(view))
