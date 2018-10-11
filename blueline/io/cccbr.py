"""Reading the central council's method library.

The CCCBR publish every method that has ever been named, as xml. It is the
canonical source and anybody serious about methods will want to load it rather
than typing notation in by hand. The shape is a collection of methods, each
with a title, a stage, and place notation, plus a great deal else this does not
need.

Only the four fields that matter are read. Everything the analyser can work out
is worked out rather than trusted: a file saying a method is Surprise when the
notation says otherwise would have to be either believed or argued with.

Parsed with the standard library rather than a dependency. The format is simple
and adding an xml library to read four fields would be a poor trade.
"""

from __future__ import annotations

from typing import Optional

from xml.etree import ElementTree

from blueline.core.method import Method
from blueline.errors import BluelineError
from blueline.io.loading import LoadError, LoadResult

#: The namespace the council's files are published under. Elements come back
#: with it glued on the front, which is why nothing here matches a bare tag.
NAMESPACE = "http://mathslib.co.uk/xml/method-library"


class CccbrError(LoadError):
    """A file that cannot be read as a council method library."""


def _tag(element: ElementTree.Element) -> str:
    """An element's name without whatever namespace it came wrapped in."""
    return element.tag.rsplit("}", 1)[-1]


def _child_text(element: ElementTree.Element, name: str) -> Optional[str]:
    for child in element:
        if _tag(child) == name and child.text:
            return child.text.strip()
    return None


def _name_from(title: str, stage_name: str) -> str:
    """The bare name, which is the title with the class and stage taken off."""
    from blueline.core.title import parse_title

    try:
        return parse_title(title).name
    except BluelineError:
        return title.replace(stage_name, "").strip() or title


def method_from(element: ElementTree.Element) -> Method:
    """One method out of a <method> element."""
    title = _child_text(element, "title")
    stage_text = _child_text(element, "stage")
    notation = _child_text(element, "notation")

    missing = [
        name
        for name, value in (("title", title), ("stage", stage_text), ("notation", notation))
        if not value
    ]
    if missing:
        raise CccbrError(f"a method has no {missing[0]}")

    assert title is not None and stage_text is not None and notation is not None
    try:
        stage = int(stage_text)
    except ValueError as error:
        raise CccbrError(f"{title}: stage {stage_text!r} is not a number") from error

    from blueline.core.stage import STAGE_NAMES

    name = _name_from(title, STAGE_NAMES.get(stage, ""))
    try:
        return Method.from_notation(name, stage, notation)
    except BluelineError as error:
        raise CccbrError(f"{title}: {error}") from error


def read(text: str) -> LoadResult:
    """Read a library, keeping what works and reporting what does not."""
    try:
        # Stripped first. A declaration has to be the very first thing in the
        # file, and a downloaded library with a blank line on the front is
        # otherwise rejected for a reason nobody could act on.
        root = ElementTree.fromstring(text.strip())
    except ElementTree.ParseError as error:
        raise CccbrError(f"not xml: {error}") from error

    found = LoadResult()
    elements = [element for element in root.iter() if _tag(element) == "method"]
    if not elements:
        raise CccbrError("no methods in this file")

    for index, element in enumerate(elements, start=1):
        try:
            found.methods.append(method_from(element))
        except CccbrError as error:
            found.problems.append(f"method {index}: {error}")
    return found
