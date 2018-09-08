"""Commands about touches, and looking for them."""

from __future__ import annotations

from typing import Optional


from blueline.cli.declare import Arg, Group, Opt
from blueline.cli import render
from blueline.cli.commands.common import show, stores, unwrap
from blueline.service import calls as call_service
from blueline.service import proving as touch_service
from blueline.service import searching as search_service
from blueline.service import spliced as splice_service

app = Group()


@app.command(context_settings={"ignore_unknown_options": True})
def prove(
    title: str = Arg(..., help="The method's full title."),
    calling: str = Arg(..., help="One symbol per lead, such as -p-s."),
    times: int = Opt(1, "--times", "-t", min=1, max=500, help="Repeat the block."),
) -> None:
    """Ring a touch through and say whether it comes round and is true."""
    report = unwrap(touch_service.prove(stores().methods, title, calling, times=times))
    show(render.touch_table(report))


@app.command()
def course(title: str = Arg(...)) -> None:
    """The plain course, reported the way a touch is."""
    report = unwrap(touch_service.course_of(stores().methods, title))
    show(render.touch_table(report))


@app.command()
def search(
    title: str = Arg(..., help="The method's full title."),
    min_length: int = Opt(1, "--min", help="Shortest touch worth having."),
    max_length: int = Opt(5040, "--max", help="Longest touch worth having."),
    limit: int = Opt(20, "--limit", "-l", min=1, max=200),
    allowed: Optional[str] = Opt(None, "--calls", help="Only use these, such as p-."),
) -> None:
    """Look for callings that come round and are true."""
    report = unwrap(
        search_service.search(
            stores().methods,
            title,
            min_length=min_length,
            max_length=max_length,
            max_found=limit,
            allowed=allowed,
        )
    )
    show(render.search_table(report))


@app.command(context_settings={"ignore_unknown_options": True})
def splice(
    order: str = Arg(..., help="Initials in order, such as CYSLCYS."),
    titles: list[str] = Opt(..., "--method", "-m", help="Repeat for each method."),
    calling: str = Opt("", "--calling", "-c", help="One symbol per lead."),
) -> None:
    """Prove a touch that changes method as it goes."""
    report = unwrap(splice_service.splice(stores().methods, list(titles), order, calling=calling))
    show(render.splice_table(report))


@app.command(name="for-length")
def for_length(
    title: str = Arg(..., help="The method's full title."),
    length: int = Arg(..., help="How many changes are wanted."),
    tolerance: int = Opt(0, "--give-or-take", "-g", min=0),
    limit: int = Opt(10, "--limit", "-l", min=1, max=100),
    allowed: Optional[str] = Opt(None, "--calls"),
) -> None:
    """Callings that come round true at a particular length."""
    report = unwrap(
        search_service.for_length(
            stores().methods,
            title,
            length=length,
            tolerance=tolerance,
            max_found=limit,
            allowed=allowed,
        )
    )
    show(render.target_table(report))


@app.command(name="positions")
def calling_positions(title: str = Arg(...)) -> None:
    """The named places in the course where a call can be made."""
    views = unwrap(call_service.positions(stores().methods, title))
    show(render.position_table(views))


@app.command(name="call")
def prove_called(
    title: str = Arg(..., help="The method's full title."),
    called: list[str] = Arg(None, help="Wrong Home Home, and so on."),
) -> None:
    """Prove a touch written the way a conductor calls it."""
    report = unwrap(call_service.prove_positions(stores().methods, title, list(called or [])))
    show(render.touch_table(report))


@app.command(name="musical")
def musical_touches(
    title: str = Arg(..., help="Which method."),
    min_length: int = Opt(1, "--min", help="Shortest worth having."),
    max_length: int = Opt(5040, "--max", help="Longest worth having."),
    max_found: int = Opt(200, "--wide", help="How many callings to try."),
    how_many: int = Opt(10, "--how-many", "-n", help="How many to rank."),
    allowed: Optional[str] = Opt(None, "--calls", help="Which calls to use."),
    min_run: int = Opt(4, "--run", help="Shortest run worth counting."),
) -> None:
    """The most musical callings a search turns up."""
    report = unwrap(
        search_service.most_musical(
            stores().methods,
            title,
            min_length=min_length,
            max_length=max_length,
            max_found=max_found,
            how_many=how_many,
            allowed=allowed,
            min_run=min_run,
        )
    )
    show(render.musical_table(report))


@app.command(name="card")
def prove_printed(
    title: str = Arg(..., help="Which method."),
    printed: str = Arg(..., help='As printed, such as "W 2H x3".'),
) -> None:
    """Prove a composition written the way it is published."""
    view = unwrap(call_service.prove_printed(stores().methods, title, printed))
    show(render.printed_table(view))
