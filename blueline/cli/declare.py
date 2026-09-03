"""Building a click command out of a function's signature.

click wants the parameters spelled out in decorators above the function, which
for seventy five commands means the name of every argument written three times:
in the decorator, in the signature, and in the body. This reads the signature
instead and builds the decorators from it, so a command says what it takes once.

Nothing clever is going on. A parameter whose default is Arg() becomes a
positional, one whose default is Opt() becomes an option, and the annotation
decides the type. Anything this cannot work out is a mistake worth hearing
about at import rather than at the point somebody runs the command, so it
raises rather than guessing.
"""

from __future__ import annotations

import functools
import inspect
import typing
from pathlib import Path
from typing import Any, Callable, List, Tuple, get_args, get_origin

import click

#: What the colours are called, so a command can say RED without importing
#: click for the one word.
RED = "red"
YELLOW = "yellow"
GREEN = "green"


class Exit(Exception):
    """Stop this command with a particular exit code."""

    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.code = code


BadParameter = click.BadParameter
echo = click.echo
secho = click.secho


class _Arg:
    """A positional argument."""

    def __init__(self, default: Any = inspect.Parameter.empty, help: str = "", **rest: Any) -> None:
        self.default = default
        self.help = help
        self.rest = rest

    @property
    def required(self) -> bool:
        return self.default is Ellipsis or self.default is inspect.Parameter.empty


class _Opt:
    """A named option, with whatever flags it answers to."""

    def __init__(self, default: Any = None, *flags: str, help: str = "", **rest: Any) -> None:
        self.default = default
        self.flags = flags
        self.help = help
        self.rest = rest

    @property
    def required(self) -> bool:
        return self.default is Ellipsis


def Arg(default: Any = inspect.Parameter.empty, help: str = "", **rest: Any) -> Any:
    """Declare a positional argument.

    Says it gives back Any so that a parameter annotated int can carry one as
    its default without the type checker objecting. What actually arrives in
    the command is an int, because click converts it on the way in.
    """
    return _Arg(default, help, **rest)


def Opt(default: Any = None, *flags: str, help: str = "", **rest: Any) -> Any:
    """Declare a named option. Any for the same reason as Arg."""
    return _Opt(default, *flags, help=help, **rest)


def _bare(annotation: Any) -> Any:
    """The type inside Optional[...] or List[...]."""
    origin = get_origin(annotation)
    if origin is None:
        return annotation
    args = [each for each in get_args(annotation) if each is not type(None)]
    return args[0] if args else str


def _is_list(annotation: Any) -> bool:
    origin = get_origin(annotation)
    return origin in (list, List)


class _PathType(click.Path):
    """A path that arrives as a Path rather than as a string.

    click's own Path checks the file and then hands back the text it was
    given. Every command here goes straight on to read_text, so the coercion
    has to happen somewhere, and once here beats once per command.
    """

    def convert(self, value: Any, param: Any, ctx: Any) -> Any:
        # click can hand back bytes, which Path will not take; everything
        # this is pointed at is a text path.
        found = super().convert(value, param, ctx)
        if isinstance(found, bytes):
            found = found.decode()
        return Path(found)


def _click_type(annotation: Any, marker: Any) -> Any:
    """What click should parse this parameter as."""
    kind = _bare(annotation)
    if kind is Path:
        return _PathType(
            exists=marker.rest.get("exists", False),
            readable=marker.rest.get("readable", True),
            dir_okay=False,
        )
    if kind in (str, int, float, bool):
        return kind
    return str


def _decorate(function: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a function in the click decorators its signature asks for.

    The annotations are resolved rather than read off the signature. Every
    module here has "from __future__ import annotations" at the top, which
    makes them strings, and a parameter annotated with the string "int" would
    otherwise be handed to click as text and arrive in the command as text.
    """
    signature = inspect.signature(function)
    hints = typing.get_type_hints(function)
    decorators: List[Callable[..., Any]] = []

    for name, parameter in signature.parameters.items():
        marker = parameter.default
        annotation = hints.get(name, parameter.annotation)
        listed = _is_list(annotation)

        if isinstance(marker, _Arg):
            decorators.append(
                click.argument(
                    name,
                    required=marker.required,
                    default=None if marker.required else marker.default,
                    type=_click_type(annotation, marker),
                    nargs=-1 if listed else 1,
                )
            )
        elif isinstance(marker, _Opt):
            flags = list(marker.flags) or ["--" + name.replace("_", "-")]
            kind = _bare(annotation)
            if kind is bool:
                decorators.append(
                    click.option(
                        *flags,
                        name,
                        is_flag=True,
                        default=bool(marker.default),
                        help=marker.help,
                    )
                )
            else:
                decorators.append(
                    click.option(
                        *flags,
                        name,
                        default=None if marker.required else marker.default,
                        required=marker.required,
                        multiple=listed,
                        type=_click_type(annotation, marker),
                        help=marker.help,
                    )
                )
        else:
            raise TypeError(
                "{0}: {1} has no Arg() or Opt() to say what it is".format(
                    function.__name__, name
                )
            )

    wrapped = function
    # Applied bottom up, the way they would read if they were written out.
    for decorator in reversed(decorators):
        wrapped = decorator(wrapped)
    return wrapped


class Group:
    """A set of commands, gathered before anything is mounted."""

    def __init__(self, help: str = "") -> None:
        self.help = help
        self.commands: List[Tuple[str, Any]] = []

    def command(self, name: str = "", **options: Any) -> Callable[..., Any]:
        def keep(function: Callable[..., Any]) -> Callable[..., Any]:
            label = name or function.__name__.replace("_", "-")
            built = click.command(
                name=label,
                help=inspect.getdoc(function) or "",
                context_settings=options.get("context_settings"),
            )(_decorate(_guarded(function)))
            self.commands.append((label, built))
            return function

        return keep

    @property
    def registered_commands(self) -> List[Any]:
        """The click commands in this group, for anything counting them."""
        return [command for _, command in self.commands]


def _guarded(function: Callable[..., Any]) -> Callable[..., Any]:
    """Turn an Exit into the exit code click expects.

    functools.wraps rather than copying the name across by hand: it also sets
    __wrapped__, which is what makes inspect.signature look through to the
    real function instead of seeing this one's *args.
    """

    @functools.wraps(function)
    def run(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except Exit as stopping:
            raise SystemExit(stopping.code)

    return run


def assemble(groups: List[Group], help: str = "") -> Any:
    """One click group holding every command, at the top level.

    Flat rather than nested: nobody wants to type "blueline methods show" when
    "blueline show" will do.
    """
    root = click.Group(help=help)
    for group in groups:
        for label, command in group.commands:
            root.add_command(command, name=label)
    return root
