"""Commands about running the thing rather than about ringing.

Starting the server, and saying where it thinks it is pointed. The second
sounds trivial and is the first thing anybody asks when a tower's copy is
talking to the wrong database.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


from blueline.cli.declare import RED, Exit, Group, Opt, echo, secho
from blueline.cli import render
from blueline.cli.commands.common import show, stores, unwrap
from blueline.config import ConfigError, Settings, load
from blueline.service import checking

app = Group()

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def settings_from(path: Optional[Path]) -> Settings:
    """The settings, or a message somebody can act on."""
    try:
        return load(path)
    except ConfigError as error:
        secho(str(error), fg=RED, err=True)
        raise Exit(code=2) from None


@app.command(name="serve")
def serve(
    host: str = Opt(DEFAULT_HOST, "--host", help="What to listen on."),
    port: int = Opt(DEFAULT_PORT, "--port", "-p", help="Which port."),
    config: Optional[Path] = Opt(None, "--config", "-c", help="A settings file."),
) -> None:
    """Run the http service.

    On the server that ships with Python. It serves one request at a time,
    which is the right size for a tower: anything that needs more than that
    wants a real server in front of it, and this application is a plain wsgi
    callable so any of them will take it.
    """
    from wsgiref.simple_server import make_server

    from blueline.api.app import create_app

    application = create_app(settings_from(config))
    echo("listening on http://{0}:{1}".format(host, port))
    server = make_server(host, port, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        echo("stopped")


@app.command(name="where")
def where(
    config: Optional[Path] = Opt(None, "--config", "-c", help="A settings file."),
) -> None:
    """Say what this copy is pointed at."""
    show(render.settings_table(settings_from(config)))


@app.command(name="check")
def check_library(
    thorough: bool = Opt(
        False, "--thorough", help="Prove every stored composition again."
    ),
) -> None:
    """Look over everything stored and say what is wrong.

    Exits non zero when there are problems, so this can go in a cron line and
    be noticed. Notes on their own are not a failure: they are things worth a
    look and half of them are intentional.
    """
    store = stores()
    report = unwrap(
        checking.check(
            store.methods,
            store.compositions,
            store.collections,
            store.ringers,
            thorough=thorough,
        )
    )
    show(render.check_table(report))
    if not report.clean:
        raise Exit(code=1)
