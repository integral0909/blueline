"""Reading and writing collections of methods as files.

A library that can only be filled in one method at a time through a form is no
use to anybody with a book of them. The format is deliberately plain: a header
saying what it is, and then one method per record with its name, stage and
notation. Everything else is worked out on the way in, because a file claiming
a method is Surprise when the notation says otherwise would have to be either
believed or argued with, and neither is good.

Two shapes are read. Json for anything talking to a program, and a line based
format for anything a person is going to type, because asking somebody to
write json by hand to add three methods is unkind.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from blueline.core.method import Method
from blueline.errors import BluelineError

FORMAT = "blueline.methods"
VERSION = 1

#: What separates the fields on a line in the plain format. The notation goes
#: last because it has commas in it and has to be able to keep them.
DELIMITER = ","
COMMENT = "#"


class DocumentError(BluelineError):
    """A file that cannot be read as a collection of methods."""


@dataclass()
class LoadResult:
    """What came out of a file, and what would not."""

    methods: List[Method] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def __len__(self) -> int:
        return len(self.methods)

    def summary(self) -> str:
        if self.ok:
            return f"{len(self.methods)} methods"
        return f"{len(self.methods)} methods, {len(self.problems)} could not be read"


def to_record(method: Method) -> Dict[str, Any]:
    return {"name": method.name, "stage": method.stage, "notation": method.notation}


def write_json(methods: List[Method], indent: int = 2) -> str:
    """The collection as json, with a header saying what it is."""
    document = {
        "format": FORMAT,
        "version": VERSION,
        "methods": [to_record(method) for method in methods],
    }
    return json.dumps(document, indent=indent, sort_keys=False)


def _method_from(record: Any, where: str) -> Method:
    if not isinstance(record, dict):
        raise DocumentError(f"{where} is not a method")
    missing = [field for field in ("name", "stage", "notation") if field not in record]
    if missing:
        raise DocumentError(f"{where} has no {missing[0]}")
    try:
        return Method.from_notation(
            str(record["name"]), int(record["stage"]), str(record["notation"])
        )
    except (BluelineError, TypeError, ValueError) as error:
        raise DocumentError(f"{where}: {error}") from error


def read_json(text: str) -> LoadResult:
    """Read a json collection, keeping what works and reporting what does not.

    One bad record does not throw the file away. Somebody importing forty
    methods wants the thirty nine that are fine and a list of what to fix.
    """
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise DocumentError(f"not json: {error}") from error
    if not isinstance(document, dict):
        raise DocumentError("a collection has to be an object")
    if document.get("format") != FORMAT:
        raise DocumentError(f"not a {FORMAT} document")
    records = document.get("methods")
    if not isinstance(records, list):
        raise DocumentError("a collection has to have a list of methods")

    result = LoadResult()
    for index, record in enumerate(records, start=1):
        try:
            result.methods.append(_method_from(record, f"method {index}"))
        except DocumentError as error:
            result.problems.append(str(error))
    return result


def write_lines(methods: List[Method]) -> str:
    """The collection as one method per line, for somebody to edit by hand."""
    out = [f"{COMMENT} {FORMAT} v{VERSION}", f"{COMMENT} name, stage, notation"]
    out.extend(
        DELIMITER.join([method.name, str(method.stage), method.notation]) for method in methods
    )
    return "\n".join(out) + "\n"


def read_lines(text: str) -> LoadResult:
    """Read the line based format, ignoring blanks and comments."""
    result = LoadResult()
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT):
            continue
        # Only the first two separators count. Place notation has commas of
        # its own, so splitting on every one turns x16x16x16,12 into two
        # fields and the line looks malformed when it is not.
        parts = [part.strip() for part in line.split(DELIMITER, 2)]
        if len(parts) != 3:
            result.problems.append(f"line {number}: wanted name, stage, notation")
            continue
        name, stage, notation = parts
        try:
            result.methods.append(Method.from_notation(name, int(stage), notation))
        except (BluelineError, ValueError) as error:
            result.problems.append(f"line {number}: {error}")
    return result


def read(text: str) -> LoadResult:
    """Read either shape, working out which it is from the first character."""
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return read_json(text)
    return read_lines(text)
