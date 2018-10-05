"""Commands for the people who ring."""

from __future__ import annotations


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.service import ringers as service

app = Group()


@app.command(name="ringer")
def add_ringer(
    name: str = Arg(..., help="Who they are."),
    can_ring: list[str] = Opt(None, "--rings", "-r", help="Repeat per method."),
    learning: list[str] = Opt(None, "--learning", "-l", help="Repeat per method."),
) -> None:
    """Add somebody to the tower's list."""
    with changing() as store:
        view = unwrap(service.add(store.ringers, name, list(can_ring or []), list(learning or [])))
    echo(view.summary())


@app.command(name="ringers")
def list_ringers() -> None:
    """Everybody, in name order."""
    views = unwrap(service.everybody(stores().ringers))
    show(render.ringer_table(views))


@app.command(name="learnt")
def mark_learnt(
    name: str = Arg(..., help="Who has learnt it."),
    title: str = Arg(..., help="What they have learnt."),
) -> None:
    """Move a method from what somebody is learning to what they can ring."""
    with changing() as store:
        view = unwrap(service.learnt(store.ringers, name, title))
    echo(view.summary())


@app.command(name="unringer")
def remove_ringer(name: str = Arg(...)) -> None:
    """Take somebody off the list."""
    with changing() as store:
        removed = unwrap(service.remove(store.ringers, name))
    echo(f"removed {removed}")


@app.command(name="learning")
def who_is_learning_what() -> None:
    """What people are learning, and who else is learning it."""
    for title, names in unwrap(service.learning(stores().ringers)).items():
        echo(f"{title}: {', '.join(names)}")


@app.command(name="band-can-ring")
def what_the_band_can_ring(
    stage: int = Arg(..., help="How many bells."),
) -> None:
    """Which stored methods this band could actually get through."""
    store = stores()
    for title in unwrap(service.what_can_be_rung(store.ringers, store.methods, stage)):
        echo(title)


@app.command(name="who-rings")
def who_can_ring(title: str = Arg(...)) -> None:
    """Everybody who can ring a method."""
    for name in unwrap(service.who_can_ring(stores().ringers, title)):
        echo(name)
