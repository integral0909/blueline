"""Working a method out, without touching the library.

Lines, falseness, place bells, handbells, variations, lead head groups and
comparisons. None of it writes anything; a method only has to be stored so it
can be named.

Split by subject like everything else that got past two hundred lines. Drawing
a blue line and working out which methods take each other's compositions are
different questions that happened to need the same repository.
"""

from blueline.service.analysing.comparing import ComparisonView as ComparisonView
from blueline.service.analysing.comparing import compare_methods as compare_methods
from blueline.service.analysing.comparing import nearest_to as nearest_to
from blueline.service.analysing.groups import lead_head_groups as lead_head_groups
from blueline.service.analysing.groups import (
    takes_the_same_compositions as takes_the_same_compositions,
)
from blueline.service.analysing.lines import falseness as falseness
from blueline.service.analysing.lines import handbells as handbells
from blueline.service.analysing.lines import line as line
from blueline.service.analysing.lines import place_bells as place_bells
from blueline.service.analysing.variations import VARIATIONS as VARIATIONS
from blueline.service.analysing.variations import change_lead_end as change_lead_end
from blueline.service.analysing.variations import relate as relate
from blueline.service.analysing.variations import vary as vary
