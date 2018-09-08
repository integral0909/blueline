"""Commands about methods."""

from __future__ import annotations

from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, echo
from blueline.cli import render
from blueline.cli.commands.common import changing, show, stores, unwrap
from blueline.service import analysing as analysis_service
from blueline.service import dossier
from blueline.service import library as service

app = Group()


@app.command()
def analyse(
    notation: str = Arg(..., help="Place notation, such as x16x16x16,12."),
    stage: int = Opt(..., "--stage", "-s", help="How many bells."),
    name: str = Opt("Unnamed", "--name", "-n", help="What the method is called."),
) -> None:
    """Work out a method from its notation without storing it."""
    report = unwrap(service.describe(name, stage, notation))
    show(render.method_table(report))


@app.command(name="list")
def list_methods(
    name: Optional[str] = Opt(None, "--name", "-n"),
    stage: Optional[int] = Opt(None, "--stage", "-s"),
    classification: Optional[str] = Opt(None, "--class", "-c"),
) -> None:
    """List what is in the library."""
    reports = unwrap(
        service.search(stores().methods, name=name, stage=stage, classification=classification)
    )
    show(render.listing_table(reports))


@app.command(name="show")
def show_method(title: str = Arg(..., help="The method's full title.")) -> None:
    """Everything about one stored method."""
    report = unwrap(service.fetch(stores().methods, title))
    show(render.method_table(report))


@app.command()
def line(
    title: str = Arg(...),
    bell: int = Arg(1, help="Which bell's line to draw."),
) -> None:
    """Draw one bell's line through a lead."""
    view = unwrap(analysis_service.line(stores().methods, title, bell))
    show(render.line_panel(view, title))
    show(view.described)
    show(render.work_line(view))


@app.command()
def falseness(
    title: str = Arg(...),
    limit: int = Opt(20, "--limit", "-l", min=1, max=200),
) -> None:
    """The course heads that clash with the plain course."""
    entries = unwrap(analysis_service.falseness(stores().methods, title, limit=limit))
    show(render.falseness_table(entries))


@app.command(name="place-bells")
def place_bells(title: str = Arg(...)) -> None:
    """Which place bell you become at each lead head."""
    order = unwrap(analysis_service.place_bells(stores().methods, title))
    show(render.bells(order))


@app.command(name="add")
def add_method(
    notation: str = Arg(...),
    stage: int = Opt(..., "--stage", "-s"),
    name: str = Opt(..., "--name", "-n"),
) -> None:
    """Put a method into the library."""
    with changing() as store:
        stored = unwrap(service.store(store.methods, name, stage, notation))
    echo(f"stored {stored.title}")


@app.command()
def remove(title: str = Arg(...)) -> None:
    """Take a method out of the library."""
    with changing() as store:
        removed = unwrap(service.remove(store.methods, title))
    echo(f"removed {removed}")


@app.command(name="handbells")
def show_handbells(title: str = Arg(...)) -> None:
    """What each pair does, ringing the method in hand."""
    views = unwrap(analysis_service.handbells(stores().methods, title))
    show(render.handbell_table(views))


@app.command(name="vary")
def vary_method(
    title: str = Arg(..., help="The method's full title."),
    kind: str = Arg(..., help="reverse, mirror or double."),
    name: Optional[str] = Opt(None, "--name", "-n"),
) -> None:
    """Work out a variation of a method without storing it."""
    report = unwrap(analysis_service.vary(stores().methods, title, kind, name=name))
    show(render.method_table(report))


@app.command(name="lead-end")
def change_lead_end(
    title: str = Arg(...),
    notation: str = Arg(..., help="The new change, such as 16."),
    name: Optional[str] = Opt(None, "--name", "-n"),
) -> None:
    """The same method with a different change at the lead end."""
    report = unwrap(analysis_service.change_lead_end(stores().methods, title, notation, name=name))
    show(render.method_table(report))


@app.command(name="relation")
def method_relation(
    title: str = Arg(...),
    other: str = Arg(...),
) -> None:
    """How two methods are related, if they are."""
    echo(unwrap(analysis_service.relate(stores().methods, title, other)))


@app.command(name="groups")
def lead_head_groups(
    stage: Optional[int] = Opt(None, "--stage", "-s"),
) -> None:
    """Methods that take each other's compositions."""
    views = unwrap(analysis_service.lead_head_groups(stores().methods, stage=stage))
    show(render.group_table(views))


@app.command(name="same-compositions")
def same_compositions(title: str = Arg(...)) -> None:
    """Every other method a composition for this one would ring to."""
    for other in unwrap(analysis_service.takes_the_same_compositions(stores().methods, title)):
        echo(other)


@app.command(name="against")
def compare_methods(
    title: str = Arg(..., help="The method you know."),
    other: str = Arg(..., help="The one you are learning."),
) -> None:
    """How alike two methods are."""
    show(
        render.comparison_table(
            unwrap(analysis_service.compare_methods(stores().methods, title, other))
        )
    )


@app.command(name="like")
def nearest_method(
    title: str = Arg(..., help="Which method."),
) -> None:
    """Whichever stored method this one is most like."""
    show(render.comparison_table(unwrap(analysis_service.nearest_to(stores().methods, title))))


@app.command(name="everything")
def method_dossier(
    title: str = Arg(..., help="The method's full title."),
    bell: int = Opt(2, "--bell", "-b", help="Whose line to draw."),
) -> None:
    """Everything about one method, in one go."""
    store = stores()
    found = unwrap(
        dossier.compile_dossier(
            store.methods, store.compositions, store.collections, title, bell=bell
        )
    )
    show(render.dossier_table(found))
