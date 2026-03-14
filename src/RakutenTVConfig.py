# Copyright (C) 2026 by xcentaurix

from Components.config import ConfigSelection, ConfigSubsection, config

from . import _
from .Variables import NUMBER_OF_LIVETV_BOUQUETS


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


# --- Helper functions -----------------------------------------------------

def getselectedregions(skip=0):
    return [getattr(config.plugins.rakutentv, "live_tv_region" + str(n)).value for n in range(1, NUMBER_OF_LIVETV_BOUQUETS + 1) if n != skip]


def autoregion(_configElement):
    for idx in range(1, NUMBER_OF_LIVETV_BOUQUETS + 1):
        selected_regions = getselectedregions(idx)
        getattr(config.plugins.rakutentv, "live_tv_region" + str(idx)).setChoices([x for x in [("", _("None"))] + list(REGION_NAMES.items()) if x[0] and x[0] not in selected_regions or not x[0] and (idx == NUMBER_OF_LIVETV_BOUQUETS or not getattr(config.plugins.rakutentv, "live_tv_region" + str(idx + 1)).value)])


# --- LiveTV region config items -----------------------------------------

for n in range(1, NUMBER_OF_LIVETV_BOUQUETS + 1):
    setattr(config.plugins.rakutentv, "live_tv_region" + str(n), ConfigSelection(default="" if n > 1 else "de", choices=[("", _("None"))] + list(REGION_NAMES.items())))

for n in range(1, NUMBER_OF_LIVETV_BOUQUETS + 1):
    getattr(config.plugins.rakutentv, "live_tv_region" + str(n)).addNotifier(autoregion, initial_call=n == NUMBER_OF_LIVETV_BOUQUETS)
