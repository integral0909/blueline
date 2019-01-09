"""Method titles, which is how a method is named to anybody else.

A title is a name, a class and a stage stuck together: Cambridge Surprise
Major, Kent Treble Bob Royal. Get any part of it wrong and you are talking
about a different method, or about no method at all, so it is worth being able
to build one and take one apart rather than passing strings around.

Two things trip up a naive split. The class can be two words, and Treble Bob
has to be looked for before Bob or Kent Treble Bob Major comes out as a method
called Kent Treble. And a handful of old methods carry no class in their title
at all: nobody has ever said Grandsire Bob Triples, and a library that started
would be wrong about the most rung method there is.
"""

from __future__ import annotations

from typing import FrozenSet, List, Optional, Tuple

from dataclasses import dataclass

from blueline.core.stage import STAGE_NAMES, stage_from_name, stage_name
from blueline.errors import StageError, TitleError

#: Class words, longest first so Treble Bob beats Bob when both would match.
CLASS_WORDS: Tuple[str, ...] = (
    "Treble Place",
    "Treble Bob",
    "Slow Course",
    "Surprise",
    "Delight",
    "Alliance",
    "Hybrid",
    "Place",
    "Bob",
)

#: Modifiers that sit in front of the class rather than being part of the name.
MODIFIERS: Tuple[str, ...] = ("Little", "Differential")

#: Methods old enough that their title never picked up a class word.
CLASSLESS_NAMES: FrozenSet[str] = frozenset(
    {"Grandsire", "Stedman", "Erin", "Original", "Reverse Grandsire", "Double Grandsire"}
)


@dataclass(frozen=True)
class Title:
    """A method's full name, in its three parts."""

    name: str
    stage: int
    classification: Optional[str] = None
    modifiers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise TitleError("a method has to have a name")
        if self.stage not in STAGE_NAMES:
            raise StageError(f"stage {self.stage} has no name")

    def __str__(self) -> str:
        parts = [self.name, *self.modifiers]
        if self.classification:
            parts.append(self.classification)
        parts.append(stage_name(self.stage))
        return " ".join(parts)

    @property
    def is_classless(self) -> bool:
        return self.classification is None


def title_for(name: str, stage: int, classification: Optional[str]) -> Title:
    """Build a title, dropping the class where the name never carries one."""
    cleaned = name.strip()
    if cleaned in CLASSLESS_NAMES:
        return Title(name=cleaned, stage=stage, classification=None)
    return Title(name=cleaned, stage=stage, classification=classification)


def _take_class(words: List[str]) -> Tuple[Optional[str], List[str]]:
    """Pull a class phrase off the end of the words, if there is one.

    Matched without regard to case and handed back in the canonical spelling,
    so a title typed in lower case reads the same as one off a peal board.
    """
    lowered = [word.lower() for word in words]
    for phrase in CLASS_WORDS:
        parts = phrase.lower().split()
        if len(words) >= len(parts) and lowered[-len(parts):] == parts:
            return phrase, words[: -len(parts)]
    return None, words


def _take_modifiers(words: List[str]) -> Tuple[Tuple[str, ...], List[str]]:
    """Pull Little and Differential off the end of the name.

    Never down to nothing. Little Bob Major is a method whose name is Little,
    and stripping the modifier would leave a title with no method in it.
    """
    lowered = {word.lower(): word for word in MODIFIERS}
    found: List[str] = []
    while len(words) > 1 and words[-1].lower() in lowered:
        found.insert(0, lowered[words.pop().lower()])
    return tuple(found), words


def parse_title(text: str) -> Title:
    """Read a title such as Cambridge Surprise Major back into its parts."""
    words = text.strip().split()
    if len(words) < 2:
        raise TitleError(f"{text!r} is not a title")
    stage = stage_from_name(words[-1])
    rest = words[:-1]
    classification, rest = _take_class(rest)
    modifiers, rest = _take_modifiers(rest)
    if not rest:
        raise TitleError(f"{text!r} leaves no name once the class is taken off")
    return Title(
        name=" ".join(rest),
        stage=stage,
        classification=classification,
        modifiers=modifiers,
    )


def same_method(first: str, second: str) -> bool:
    """Whether two titles name the same method, ignoring spacing and case."""
    try:
        left, right = parse_title(first), parse_title(second)
    except (TitleError, StageError):
        return False
    return (
        left.name.lower() == right.name.lower()
        and left.stage == right.stage
        and (left.classification or "").lower() == (right.classification or "").lower()
    )
