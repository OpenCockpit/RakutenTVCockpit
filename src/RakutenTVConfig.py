# Copyright (C) 2026 by xcentaurix

from Components.config import ConfigSelection, ConfigSubsection, config

from . import _
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

config.plugins.rakutentv = ConfigSubsection()
config.plugins.rakutentv.region = ConfigSelection(default="de", choices=list(REGION_NAMES.items()))
config.plugins.rakutentv.picons = ConfigSelection(default="snp", choices=[("snp", _("service name")), ("srp", _("service reference")), ("", _("None"))])
config.plugins.rakutentv.silentmode = ConfigSelection(default="yes", choices=[("yes", _("Yes")), ("no", _("No"))])


# --- LiveTV region config items -----------------------------------------

getselectedregions = setupLocationSlots(config.plugins.rakutentv, "live_tv_region", REGION_NAMES, NUMBER_OF_LIVETV_BOUQUETS, _("None"), first_default="de")
