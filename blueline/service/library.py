"""Getting methods in and out of the library.

Storing, fetching, searching, removing, and moving whole collections. Anything
here reads or writes what is stored; working a method out without touching the
library is in analysis.
"""

from __future__ import annotations

from typing import List, Optional

from blueline.analysis import MethodReport, analyse
from blueline.core.method import Method
from blueline.db.models import StoredMethod
from blueline.db.repository import MethodRepository, to_method
from blueline.errors import BluelineError
from blueline.io.documents import read, write_json, write_lines
from blueline.io.loading import LoadError, LoadResult
from blueline.service.method_views import ImportReport
from blueline.service.results import Result, already_exists, invalid, not_found, succeeded


def parse_method(name: str, stage: int, notation: str) -> Result[Method]:
    """Build a method from what somebody typed, without letting a throw out."""
    try:
        return succeeded(Method.from_notation(name, stage, notation))
    except BluelineError as error:
        return invalid(str(error))


def describe(name: str, stage: int, notation: str) -> Result[MethodReport]:
    """Analyse a method given as notation, without storing it."""
    built = parse_method(name, stage, notation)
    if not built.ok:
        return Result(failure=built.failure)
    return succeeded(analyse(built.unwrap()))


def store(
    repository: MethodRepository, name: str, stage: int, notation: str
) -> Result[StoredMethod]:
    """Put a method in the library, refusing one that is already there."""
    built = parse_method(name, stage, notation)
    if not built.ok:
        return Result(failure=built.failure)
    method = built.unwrap()
    report = analyse(method)
    if repository.find(str(report.title)) is not None:
        return already_exists(f"{report.title} is already in the library")
    return succeeded(repository.add(method))


def fetch(repository: MethodRepository, title: str) -> Result[MethodReport]:
    """The analysis of a stored method, looked up by title."""
    stored = repository.find(title)
    if stored is None:
        return not_found(f"no method called {title!r}")
    return succeeded(analyse(to_method(stored)))


def remove(repository: MethodRepository, title: str) -> Result[str]:
    stored = repository.find(title)
    if stored is None:
        return not_found(f"no method called {title!r}")
    repository.remove(stored.title)
    return succeeded(stored.title)


def search(
    repository: MethodRepository,
    name: Optional[str] = None,
    stage: Optional[int] = None,
    classification: Optional[str] = None,
) -> Result[List[MethodReport]]:
    found = repository.search(name=name, stage=stage, classification=classification)
    return succeeded([analyse(to_method(stored)) for stored in found])


def import_methods(repository: MethodRepository, text: str) -> Result[ImportReport]:
    """Read a collection and put what is in it into the library.

    Anything already stored is skipped rather than failing the import. Loading
    a file that overlaps what you already have is the normal case, not a
    mistake.
    """
    try:
        loaded: LoadResult = read(text)
    except LoadError as error:
        return invalid(str(error))

    added: List[str] = []
    skipped: List[str] = []
    for method in loaded.methods:
        report = analyse(method)
        title = str(report.title)
        if repository.find(title) is not None:
            skipped.append(title)
            continue
        repository.add(method)
        added.append(title)

    return succeeded(
        ImportReport(
            added=tuple(added),
            skipped=tuple(skipped),
            problems=tuple(loaded.problems),
        )
    )


def export_methods(
    repository: MethodRepository,
    shape: str = "json",
    stage: Optional[int] = None,
) -> Result[str]:
    """The library, or part of it, as a file."""
    if shape not in {"json", "lines"}:
        return invalid(f"no such format as {shape!r}")
    stored = repository.search(stage=stage)
    methods = [to_method(each) for each in stored]
    text = write_json(methods) if shape == "json" else write_lines(methods)
    return succeeded(text)
