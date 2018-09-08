"""Commands about what has been rung."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.core.statistics import leaderboard
from blueline.service import performances as service

app = Group()


@app.command()
def rang(
    title: str = Arg(..., help="What was rung."),
    ringers: list[str] = Opt(..., "--ringer", "-r", help="Repeat, treble first."),
    stage: int = Opt(..., "--stage", "-s"),
    length: int = Opt(..., "--length", "-l"),
    on: str = Opt(..., "--on", help="The date, as 2023-03-18."),
    place: str = Opt(..., "--place", "-p"),
    conductor: Optional[str] = Opt(None, "--conductor", "-c"),
    composer: Optional[str] = Opt(None, "--composer"),
    speed: float = Opt(30.0, "--speed", help="Rows a minute."),
) -> None:
    """Write up something a band rang."""
    with changing() as store:
        view = unwrap(
            service.record(
                store.performances,
                store.methods,
                title=title,
                stage=stage,
                length=length,
                rang_on=on,
                place=place,
                ringers=list(ringers),
                conductor=conductor,
                composer=composer,
                peal_speed=speed,
                towers=store.towers,
            )
        )
    echo(render.board_lines(view))


@app.command()
def rung(
    place: Optional[str] = Opt(None, "--place", "-p"),
    title: Optional[str] = Opt(None, "--method", "-m"),
    stage: Optional[int] = Opt(None, "--stage", "-s"),
    min_length: Optional[int] = Opt(None, "--min"),
    ringer: Optional[str] = Opt(None, "--ringer", "-r"),
) -> None:
    """What has been rung, most recent first."""
    views = unwrap(
        service.search(
            stores().performances,
            place=place,
            title=title,
            stage=stage,
            min_length=min_length,
            ringer=ringer,
        )
    )
    show(render.performance_table(views))


@app.command()
def totals(
    place: Optional[str] = Opt(None, "--place", "-p"),
    ringer: Optional[str] = Opt(None, "--ringer", "-r"),
    top: int = Opt(10, "--top", min=1, max=100),
) -> None:
    """What has been rung, added up."""
    store = stores()
    counted = unwrap(service.statistics(store.performances, place=place, ringer=ringer))
    show(render.totals_table(counted))
    if counted.performances:
        show(render.leaderboard_table("methods", leaderboard(counted.by_method, top)))
        show(render.leaderboard_table("ringers", leaderboard(counted.by_ringer, top)))


@app.command(name="board")
def performance_board(
    performance_id: int = Arg(..., help="Which performance."),
    width: int = Opt(44, "--width", "-w", min=20, max=120),
) -> None:
    """Lay a performance out as it would be painted on a wall."""
    echo(unwrap(service.board(stores().performances, performance_id, width=width)))


@app.command(name="report")
def performance_report(
    performance_id: int = Arg(..., help="Which performance."),
) -> None:
    """Write a performance up ready to be pasted in."""
    echo(unwrap(service.report(stores().performances, performance_id)))


@app.command(name="paste")
def record_from_report(
    path: Path = Arg(..., exists=True, readable=True, help="A report."),
    stage: int = Arg(..., help="How many bells were rung."),
) -> None:
    """File a performance somebody wrote up as a report."""
    with changing() as store:
        view = unwrap(
            service.from_report(
                store.performances,
                store.methods,
                path.read_text(),
                stage,
                towers=store.towers,
            )
        )
    show(render.performance_table([view]))
