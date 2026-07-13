# Copyright (C) 2026 by xcentaurix

import ipaddress
import random

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

# Geo-spoofing IP ranges per region, used for X-Forwarded-For headers so the
# stream-resolution request appears to originate from the selected region
# instead of the box's real location. Each value is a /24 known (via public
# RIR delegation data) to be allocated within that country.
# pickForwardIP() draws a random host from it (cached for the process
# lifetime) instead of always sending one exact address.
X_FORWARD_NETS = {
    "at": "2.18.68.0/24",
    "ch": "5.144.31.0/24",
    "de": "85.214.132.0/24",
    "dk": "80.63.84.0/24",
    "es": "88.26.241.0/24",
    "fi": "85.194.236.0/24",
    "fr": "176.31.84.0/24",
    "ie": "2.57.24.0/24",
    "it": "5.133.48.0/24",
    "nl": "2.56.56.0/24",
    "no": "84.214.150.0/24",
    "pl": "2.56.68.0/24",
    "ro": "2.59.15.0/24",
    "se": "185.39.146.0/24",
    "uk": "185.199.220.0/24",
}

_forwardIPCache = {}


def pickForwardIP(region):
    """Return an X-Forwarded-For address for *region*, or None if unmapped.

    Picked once per region and cached for the life of the process (not
    re-rolled per call), so a single streaming session doesn't see its
    apparent origin IP change mid-flight. Restarting the plugin re-rolls
    it, spreading requests across the subnet over time.
    """
    net = X_FORWARD_NETS.get(region)
    if net is None:
        return None
    if region not in _forwardIPCache:
        _forwardIPCache[region] = str(random.choice(list(ipaddress.ip_network(net).hosts())))
    return _forwardIPCache[region]


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
