"""Turning results into something worth looking at in a terminal.

Kept apart from the commands so the commands stay about what to do and this
stays about how it looks. It also means the tables can be tested without going
anywhere near argument parsing.

Split the way the commands are, and by the same argument: twenty two tables in
one module meant a change to how a touch is reported sat in the middle of
everything about performances. The commands still say render.something, so
nothing outside this package had to move.

Re-exported with "as" rather than listed in an __all__ nobody remembered to
update. Forgetting one meant the linter deleted the import and the failure
turned up three files away.
"""

from blueline.cli.render.callchanges import callchange_rows as callchange_rows
from blueline.cli.render.callchanges import callchange_table as callchange_table
from blueline.cli.render.collections import (
    collection_listing as collection_listing,
)
from blueline.cli.render.collections import (
    collection_table as collection_table,
)
from blueline.cli.render.collections import (
    coverage_table as coverage_table,
)
from blueline.cli.render.common import bells as bells
from blueline.cli.render.common import console as console
from blueline.cli.render.common import fields as fields
from blueline.cli.render.common import listing as listing
from blueline.cli.render.common import yes_no as yes_no
from blueline.cli.render.competitions import (
    competition_listing as competition_listing,
)
from blueline.cli.render.competitions import (
    competition_table as competition_table,
)
from blueline.cli.render.competitions import (
    progress_table as progress_table,
)
from blueline.cli.render.compositions import (
    composition_listing as composition_listing,
)
from blueline.cli.render.compositions import (
    composition_table as composition_table,
)
from blueline.cli.render.learning import (
    advice_table as advice_table,
)
from blueline.cli.render.learning import (
    difficulty_panel as difficulty_panel,
)
from blueline.cli.render.learning import (
    difficulty_table as difficulty_table,
)
from blueline.cli.render.methods import (
    comparison_table as comparison_table,
)
from blueline.cli.render.methods import (
    dossier_table as dossier_table,
)
from blueline.cli.render.methods import (
    falseness_table as falseness_table,
)
from blueline.cli.render.methods import (
    group_table as group_table,
)
from blueline.cli.render.methods import (
    handbell_table as handbell_table,
)
from blueline.cli.render.methods import (
    line_panel as line_panel,
)
from blueline.cli.render.methods import (
    listing_table as listing_table,
)
from blueline.cli.render.methods import (
    method_table as method_table,
)
from blueline.cli.render.methods import (
    work_line as work_line,
)
from blueline.cli.render.records import (
    annual_table as annual_table,
)
from blueline.cli.render.records import (
    board_lines as board_lines,
)
from blueline.cli.render.records import (
    leaderboard_table as leaderboard_table,
)
from blueline.cli.render.records import (
    performance_table as performance_table,
)
from blueline.cli.render.records import (
    plan_table as plan_table,
)
from blueline.cli.render.records import (
    ringer_table as ringer_table,
)
from blueline.cli.render.records import (
    term_table as term_table,
)
from blueline.cli.render.records import (
    totals_table as totals_table,
)
from blueline.cli.render.records import (
    tower_table as tower_table,
)
from blueline.cli.render.service import check_table as check_table
from blueline.cli.render.service import settings_table as settings_table
from blueline.cli.render.striking import striking_table as striking_table
from blueline.cli.render.touches import (
    musical_table as musical_table,
)
from blueline.cli.render.touches import (
    position_table as position_table,
)
from blueline.cli.render.touches import (
    printed_table as printed_table,
)
from blueline.cli.render.touches import (
    search_table as search_table,
)
from blueline.cli.render.touches import (
    splice_table as splice_table,
)
from blueline.cli.render.touches import (
    target_table as target_table,
)
from blueline.cli.render.touches import (
    touch_table as touch_table,
)
