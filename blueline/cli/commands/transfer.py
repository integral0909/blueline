"""Commands for getting methods in and out of the library in bulk.

Kept apart from the commands that ask a method a question. Loading a council
library and drawing a blue line have nothing to do with each other beyond both
involving methods, and the file they were both in had grown to twenty commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


from blueline.cli.declare import Arg, Group, Opt, YELLOW, echo, secho
from blueline.cli.commands.common import changing, stores, unwrap
from blueline.db.seed import seed_standard
from blueline.service import library as service

app = Group()


@app.command(name="import")
def import_file(
    path: Path = Arg(..., exists=True, readable=True, help="A collection to read."),
) -> None:
    """Read a collection of methods into the library."""
    with changing() as store:
        report = unwrap(service.import_methods(store.methods, path.read_text()))
    echo(report.summary())
    for problem in report.problems:
        secho(f"  {problem}", fg=YELLOW, err=True)


@app.command(name="export")
def export_file(
    path: Optional[Path] = Arg(None, help="Where to write. Left off, it prints."),
    shape: str = Opt("json", "--format", "-f", help="json or lines."),
    stage: Optional[int] = Opt(None, "--stage", "-s"),
) -> None:
    """Write the library out as a file."""
    text = unwrap(service.export_methods(stores().methods, shape=shape, stage=stage))
    if path is None:
        echo(text)
        return
    path.write_text(text)
    echo(f"wrote {path}")


@app.command()
def seed() -> None:
    """Load the standard methods into an empty library."""
    with changing() as store:
        report = seed_standard(store.methods)
    echo(str(report))
