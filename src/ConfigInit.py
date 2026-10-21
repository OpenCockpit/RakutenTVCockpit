# Copyright (C) 2026 by xcentaurix
# License: GNU General Public License v3.0

from Components.config import ConfigDirectory, ConfigSelection, ConfigYesNo, config

from . import _
from . import Debug  # noqa: F401, pylint: disable=unused-import
from .Variables import NUMBER_OF_LIVETV_BOUQUETS
from .CockpitTVConfig import setupLocationSlots


# Regions available on Rakuten TV (FAST channels)
REGION_NAMES = {
    "at": "Austria",
    "ch": "Switzerland",
    "de": "Germany",
    "dk": "Denmark",
    "es": "Spain",
    "fi": "Finland",
    "fr": "France",
    "ie": "Ireland",
    "it": "Italy",
    "nl": "Netherlands",
    "no": "Norway",
    "pl": "Poland",
    "ro": "Romania",
    "se": "Sweden",
    "uk": "United Kingdom",
    # Appended (not alphabetized into the block above) so existing countries'
    # TSIDS values - derived from REGION_NAMES's insertion order - don't shift
    # and break already-imported EPG/timers for them.
    "al": "Albania",
    "ba": "Bosnia and Herzegovina",
    "be": "Belgium",
    "bg": "Bulgaria",
    "cz": "Czechia",
    "ee": "Estonia",
    "gr": "Greece",
    "hr": "Croatia",
    "is": "Iceland",
    "lt": "Lithuania",
    "lu": "Luxembourg",
    "me": "Montenegro",
    "mk": "North Macedonia",
    "pt": "Portugal",
    "rs": "Serbia",
    "sk": "Slovakia",
}

# Classification IDs for Rakuten TV API
CLASSIFICATION_IDS = {
    "al": 270,
    "at": 300,
    "ba": 245,
    "be": 308,
    "bg": 269,
    "ch": 319,
    "cz": 272,
    "de": 307,
    "dk": 283,
    "ee": 288,
    "es": 5,
    "fi": 284,
    "fr": 23,
    "gr": 279,
    "hr": 302,
    "ie": 41,
    "is": 287,
    "it": 36,
    "jp": 309,
    "lt": 290,
    "lu": 74,
    "me": 259,
    "mk": 275,
    "nl": 69,
    "no": 286,
    "pl": 277,
    "pt": 64,
    "ro": 268,
    "rs": 266,
    "se": 282,
    "sk": 273,
    "uk": 18,
}

TSIDS = {cc: f"{i:X}" for i, cc in enumerate(REGION_NAMES, 0x200)}


# --- Config subsection ---------------------------------------------------

# Debug creates config.plugins.rakutentvcockpit (with debug_log_level): the settings below join that subsection, it
# must not be created again here.
# The settings used to be config.plugins.rakutentv: take over what is stored there and drop it, so it isn't saved again.
if oldValues := config.plugins.content.stored_values.pop("rakutentv", None):
    for key, value in oldValues.items():
        config.plugins.rakutentvcockpit.content.stored_values.setdefault(key, value)
config.plugins.rakutentvcockpit.region = ConfigSelection(default="de", choices=list(REGION_NAMES.items()))
config.plugins.rakutentvcockpit.picons = ConfigSelection(default="snp", choices=[("snp", _("service name")), ("srp", _("service reference")), ("", _("None"))])
config.plugins.rakutentvcockpit.silentmode = ConfigSelection(default="yes", choices=[("yes", _("Yes")), ("no", _("No"))])
config.plugins.rakutentvcockpit.auto_update_check = ConfigSelection(default="yes", choices=[("yes", _("Yes")), ("no", _("No"))])
# Read by PRSCockpitPlayer (CockpitPlayer); not offered in the setup screen.
config.plugins.rakutentvcockpit.movie_resume_at_last_pos = ConfigYesNo(default=False)
config.plugins.rakutentvcockpit.movie_start_position = ConfigSelection(default="beginning", choices=[("beginning", _("beginning"))])
config.plugins.rakutentvcockpit.config_folder = ConfigDirectory(default="/etc/enigma2")
config.plugins.rakutentvcockpit.stream_proxy = ConfigYesNo(default=False)

# --- Live-TV region config items -----------------------------------------

getselectedregions = setupLocationSlots(config.plugins.rakutentvcockpit, "live_tv_region", REGION_NAMES, NUMBER_OF_LIVETV_BOUQUETS, _("None"), first_default="de")
