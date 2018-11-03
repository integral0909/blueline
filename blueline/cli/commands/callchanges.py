"""Commands for call change ringing."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import show, unwrap
from blueline.service import callchanges as service

app = Group()


@app.command(name="calls")
def prove_calling(
    calling: str = Arg(..., help="The calls, separated by semicolons."),
    stage: int = Arg(..., help="How many bells."),
    style: str = Opt("down", "--style", help="up in Devon, down elsewhere."),
    start: str = Opt("", "--from", help="Where the band is standing."),
    rows: bool = Opt(False, "--rows", help="Show every row, not the summary."),
) -> None:
    """Ring a calling through and say where it went."""
    report = unwrap(service.prove(calling, stage, style=style, start=start))
    if rows:
        show(render.callchange_rows(report))
        return
    show(render.callchange_table(report))


@app.command(name="calls-file")
def prove_file(
    path: Path = Arg(..., exists=True, readable=True, help="A calling, one a line."),
    stage: int = Arg(..., help="How many bells."),
    style: str = Opt("down", "--style", help="up in Devon, down elsewhere."),
    start: str = Opt("", "--from", help="Where the band is standing."),
) -> None:
    """Ring a calling that was written down."""
    report = unwrap(service.prove(path.read_text(), stage, style=style, start=start))
    show(render.callchange_rows(report))


@app.command(name="route")
def route_to(
    target: str = Arg(..., help="A named change, or a row."),
    stage: int = Arg(..., help="How many bells."),
    start: str = Opt("", "--from", help="Where the band is standing."),
    style: Optional[str] = Opt(None, "--style", help="How to say the calls."),
) -> None:
    """The calls that take a band from where they are to somewhere else."""
    report = unwrap(service.how_to_get_to(target, stage, start=start))
    spoken = unwrap(service.said(report, style or "down"))
    show(render.callchange_table(report))
    for call in spoken:
        echo(f"  {call}")
