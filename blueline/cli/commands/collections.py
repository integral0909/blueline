"""Commands for named sets of methods."""

from __future__ import annotations

from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.service import collections as service

app = Group()


@app.command(name="set")
def keep_collection(
    name: str = Arg(..., help="What the set is called."),
    titles: list[str] = Opt(..., "--method", "-m", help="Repeat per method."),
    note: str = Opt("", "--note", help="What it is for."),
) -> None:
    """Write a set of methods down."""
    with changing() as store:
        view = unwrap(service.keep(store.collections, store.methods, name, list(titles), note=note))
    show(render.collection_table(view))


@app.command(name="sets")
def list_collections(
    stored_only: bool = Opt(False, "--mine", help="Leave out the named sets."),
) -> None:
    """Every set, stored or named."""
    store = stores()
    found = unwrap(service.listing(store.collections, store.methods, include_known=not stored_only))
    show(render.collection_listing(found))


@app.command(name="show-set")
def show_collection(
    name: str = Arg(..., help="Which set."),
) -> None:
    """What is in a set, and how hard it is."""
    store = stores()
    view = unwrap(service.fetch(store.collections, store.methods, name))
    show(render.collection_table(view))


@app.command(name="covers")
def collection_coverage(
    name: str = Arg(..., help="Which set."),
    who: Optional[str] = Opt(None, "--who", "-w", help="One ringer, or the band."),
) -> None:
    """How much of a set a ringer, or the whole band, rings."""
    store = stores()
    view = unwrap(service.coverage(store.collections, store.ringers, name, who=who))
    show(render.coverage_table(view))


@app.command(name="set-add")
def add_to_collection(
    name: str = Arg(..., help="Which set."),
    title: str = Arg(..., help="Which method."),
) -> None:
    """Put a method into a stored set."""
    with changing() as store:
        view = unwrap(service.add_to(store.collections, store.methods, name, title))
    show(render.collection_table(view))


@app.command(name="set-drop")
def take_out_of_collection(
    name: str = Arg(..., help="Which set."),
    title: str = Arg(..., help="Which method."),
) -> None:
    """Take a method out of a stored set."""
    with changing() as store:
        view = unwrap(service.take_out(store.collections, store.methods, name, title))
    show(render.collection_table(view))


@app.command(name="forget-set")
def forget_collection(
    name: str = Arg(..., help="Which set."),
) -> None:
    """Drop a stored set."""
    with changing() as store:
        unwrap(service.forget(store.collections, name))
    echo(f"forgot {name}")
