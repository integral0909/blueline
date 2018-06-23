"""How many bells are being rung, and what they are called.

A stage is not just a count. Ringers name every stage, and the names carry
meaning: an odd stage such as doubles is rung on five working bells with the
tenor covering behind, so a method on eleven bells is called cinques and not
"elevens". Getting these names right matters because a method's full title is
built from them, and a title is how a method is identified everywhere else.

Bells are written as single characters so a row fits on one line. One to nine
are the obvious digits, then 0 for the tenth, E for the eleventh and T for the
twelfth. Above that the convention runs on through A, B, C and D, which is why
0 comes before E rather than after 9 in the usual place.
"""

from __future__ import annotations

from typing import Dict, Final

BELL_SYMBOLS: Final[str] = "1234567890ETABCD"

MAX_STAGE: Final[int] = len(BELL_SYMBOLS)
MIN_STAGE: Final[int] = 3

STAGE_NAMES: Final[Dict[int, str]] = {
    3: "Singles",
    4: "Minimus",
    5: "Doubles",
    6: "Minor",
    7: "Triples",
    8: "Major",
    9: "Caters",
    10: "Royal",
    11: "Cinques",
    12: "Maximus",
    13: "Sextuples",
    14: "Fourteen",
    15: "Septuples",
    16: "Sixteen",
}


class StageError(ValueError):
    """A stage outside the range this library can work with."""


def check_stage(stage: int) -> int:
    """Return the stage, having satisfied ourselves it is one we can ring."""
    if stage < MIN_STAGE or stage > MAX_STAGE:
        raise StageError(f"stage {stage} is outside {MIN_STAGE} to {MAX_STAGE}")
    return stage


def stage_name(stage: int) -> str:
    """The name ringers use for a stage, such as Major for eight."""
    check_stage(stage)
    return STAGE_NAMES[stage]


def is_odd_stage(stage: int) -> bool:
    """Whether the tenor covers rather than taking part in the changes.

    Doubles, triples, caters and cinques are rung on an odd number of working
    bells with the tenor struck last in every row. The method itself is even
    smaller than the number of bells in the tower would suggest.
    """
    check_stage(stage)
    return stage % 2 == 1


def bell_symbol(bell: int) -> str:
    """The character standing for a bell, counting the treble as one."""
    if bell < 1 or bell > MAX_STAGE:
        raise StageError(f"no symbol for bell {bell}")
    return BELL_SYMBOLS[bell - 1]


def bell_number(symbol: str) -> int:
    """The bell a character stands for, counting the treble as one."""
    upper = symbol.upper()
    index = BELL_SYMBOLS.find(upper)
    if len(symbol) != 1 or index < 0:
        raise StageError(f"{symbol!r} is not a bell")
    return index + 1


def rounds_string(stage: int) -> str:
    """Rounds at a stage, which is the bells in order from the treble down."""
    check_stage(stage)
    return BELL_SYMBOLS[:stage]


def stage_from_name(name: str) -> int:
    """The stage a name refers to, so a title can be read back apart."""
    wanted = name.strip().lower()
    for stage, known in STAGE_NAMES.items():
        if known.lower() == wanted:
            return stage
    raise StageError(f"{name!r} is not a stage name")
