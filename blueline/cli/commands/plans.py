"""Commands for planning a practice."""

from __future__ import annotations

from datetime import date
from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import show, stores, unwrap
from blueline.service import plans as service
from blueline.service import terms

app = Group()


@app.command(name="plan")
def plan_practice(
    ringers: int = Arg(..., help="How many people are coming."),
    minutes: int = Arg(60, help="How long the practice is."),
    speed: float = Opt(30.0, "--speed", help="Rows a minute."),
    place: Optional[str] = Opt(None, "--place", "-p", help="Cap it by a tower."),
    anything: bool = Opt(
        False, "--anything", help="Ignore what the band can actually ring."
    ),
) -> None:
    """What a band could ring in the time."""
    store = stores()
    view = unwrap(
        service.plan(
            store.methods,
            ringers=ringers,
            minutes=minutes,
            speed=speed,
            towers=store.towers,
            place=place,
            band=None if anything else store.ringers,
        )
    )
    show(render.plan_table(view))


@app.command(name="ringable")
def what_can_be_rung(
    ringers: int = Arg(..., help="How many people are coming."),
) -> None:
    """The methods a band of this size could ring."""
    titles = unwrap(service.what_can_be_rung(stores().methods, ringers))
    for title in titles:
        echo(title)


@app.command(name="term")
def plan_the_term(
    first: str = Arg(..., help="The first day of term, as 2023-09-05."),
    last: str = Arg(..., help="The last."),
    weekday: int = Opt(1, "--night", "-n", help="0 is Monday, 1 is Tuesday."),
    working_from: Optional[str] = Opt(None, "--from", "-f", help="A named set."),
) -> None:
    """A term's practice nights, with something against each."""
    store = stores()
    view = unwrap(
        terms.plan_term(
            store.methods,
            store.ringers,
            store.collections,
            date.fromisoformat(first),
            date.fromisoformat(last),
            weekday=weekday,
            working_from=working_from,
        )
    )
    show(render.term_table(view))
