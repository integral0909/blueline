"""Commands for the compositions somebody has written down."""

from __future__ import annotations

from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.service import compositions as service

# A calling starts with a bob more often than not, and click reads a leading
# dash as an option. Same reason the prove command turns option parsing off.
app = Group()


@app.command(name="keep", context_settings={"ignore_unknown_options": True})
def keep_composition(
    title: str = Arg(..., help="What the touch is called."),
    method: str = Arg(..., help="The method it is rung to."),
    calling: str = Arg(..., help="The calls, as - s and p."),
    composer: str = Opt("", "--composer", "-c", help="Who wrote it."),
) -> None:
    """Prove a touch and keep it."""
    with changing() as store:
        view = unwrap(
            service.store(
                store.compositions,
                store.methods,
                title=title,
                method_title=method,
                calling=calling,
                composer=composer,
            )
        )
    show(render.composition_table(view))


@app.command(name="compositions")
def list_compositions(
    method: Optional[str] = Opt(None, "--method", "-m", help="Only this method."),
    limit: int = Opt(10, "--limit", "-l", help="How many, longest first."),
) -> None:
    """Everything written for one method, or the longest in the library."""
    store = stores()
    if method is not None:
        found = unwrap(service.for_method(store.compositions, store.methods, method))
    else:
        found = unwrap(service.longest(store.compositions, store.methods, limit=limit))
    show(render.composition_listing(found))


@app.command(name="forget")
def forget_composition(
    composition_id: int = Arg(..., help="Which one to drop."),
) -> None:
    """Take a composition out of the library."""
    with changing() as store:
        unwrap(service.remove(store.compositions, composition_id))
    echo(f"forgot composition {composition_id}")
