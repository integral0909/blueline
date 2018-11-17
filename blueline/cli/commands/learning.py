"""Commands about what to learn next."""

from __future__ import annotations

from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import show, stores, unwrap
from blueline.service import learning as service

app = Group()


@app.command(name="order")
def ranked(
    stage: Optional[int] = Opt(None, "--stage", "-s", help="Only this many bells."),
) -> None:
    """The library in order of how hard it is, easiest first."""
    found = unwrap(service.rank(stores().methods, stage=stage))
    show(render.difficulty_table(found))


@app.command(name="hard")
def how_hard(
    title: str = Arg(..., help="Which method."),
) -> None:
    """What one method is going to ask of somebody."""
    difficulty = unwrap(service.how_hard(stores().methods, title))
    show(render.difficulty_panel(difficulty))


@app.command(name="next")
def advise(
    name: str = Arg(..., help="Whose advice to work out."),
    how_many: int = Opt(3, "--how-many", "-n", help="How many suggestions."),
) -> None:
    """What a particular ringer should learn next."""
    store = stores()
    view = unwrap(service.advise(store.methods, store.ringers, name, how_many=how_many))
    show(render.advice_table(view))
    echo(view.summary())


@app.command(name="band-next")
def advise_the_band(
    how_many: int = Opt(3, "--how-many", "-n", help="How many suggestions."),
) -> None:
    """What the whole band could learn together."""
    store = stores()
    found = unwrap(service.advise_a_band(store.methods, store.ringers, how_many=how_many))
    show(render.difficulty_table(found))
