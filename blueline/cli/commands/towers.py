"""Commands about the rings of bells themselves."""

from __future__ import annotations

from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.service import annual
from blueline.service import towers as service

app = Group()


@app.command(name="tower")
def add_tower(
    place: str = Arg(..., help="Where the ring is."),
    bells: int = Opt(..., "--bells", "-b", help="How many."),
    tenor: str = Opt(..., "--tenor", "-t", help="The tenor weight, as 23-1-14."),
) -> None:
    """Add a ring of bells."""
    with changing() as store:
        view = unwrap(service.add(store.towers, place, bells, tenor))
    echo(view.summary())


@app.command(name="towers")
def list_towers(
    place: Optional[str] = Opt(None, "--place", "-p"),
    min_bells: Optional[int] = Opt(None, "--min-bells"),
    max_bells: Optional[int] = Opt(None, "--max-bells"),
    min_tenor: Optional[str] = Opt(None, "--min-tenor", help="As 20-0-0."),
) -> None:
    """The rings of bells, heaviest first."""
    views = unwrap(
        service.search(
            stores().towers,
            place=place,
            min_bells=min_bells,
            max_bells=max_bells,
            min_tenor=min_tenor,
        )
    )
    show(render.tower_table(views))


@app.command(name="untower")
def remove_tower(place: str = Arg(...)) -> None:
    """Take a ring of bells out."""
    with changing() as store:
        removed = unwrap(service.remove(store.towers, place))
    echo(f"removed {removed}")


@app.command(name="year")
def annual_report(
    place: str = Arg(..., help="Which tower."),
    year: int = Arg(..., help="Which year."),
    against: str = Opt(
        "the standard eight", "--against", "-a", help="A set to measure the band against."
    ),
    top: int = Opt(5, "--top", "-t", help="How long the leaderboards are."),
) -> None:
    """Everything a tower puts in front of its AGM."""
    store = stores()
    view = unwrap(
        annual.report(
            store.performances,
            store.ringers,
            store.competitions,
            store.collections,
            store.methods,
            year=year,
            place=place,
            against=against,
            top=top,
        )
    )
    show(render.annual_table(view))
