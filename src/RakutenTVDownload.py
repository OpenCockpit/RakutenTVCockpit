# Copyright (C) 2026 by xcentaurix

import os
import zlib

from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eTimer

from . import _
from .RakutenTVConfig import REGION_NAMES, TSIDS, getselectedregions
from .RakutenTVRequest import rakutenRequest
from .Variables import TIMER_FILE, BOUQUET_FILE, BOUQUET_NAME
from .CockpitTVDownload import TVDownloadBase, TVDownloadScreenMixin, TVDownloadSilentMixin, importXMLTVGuide


# Data paths for ignore list
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
RAKUTEN_IGNORE = "rakutentv.ignore"


class RakutenTVDownloadBase(TVDownloadBase):
    downloadActive = False

    TIMER_FILE = TIMER_FILE
    BOUQUET_FILE = BOUQUET_FILE
    TSIDS = TSIDS

    LOG_PREFIX = "RakutenTV Download"
    SILENT_IN_PROGRESS_TEXT = _("A silent download is in progress.")
    PICONS_LABEL = _("picons")
    FETCHING_PICONS_TEXT = _("Fetching picons...")
    UPDATE_COMPLETED_TEXT = _("LiveTV update completed")
    PROCESSING_TEXT = _("Processing data...")
    WAITING_FOR_CHANNEL_TEXT = _("Waiting for Channel: ")
    EPGIMPORT_MISSING_TEXT = _("EPGImport plugin not found - please install it to get EPG data for Rakuten TV.")

    def __init__(self, silent=False):
        TVDownloadBase.__init__(self, silent)
        self.ignore_list = self._get_ignore_list()

    @staticmethod
    def _get_ignore_list():
        """Load channel IDs to ignore from the ignore file."""
        fpath = os.path.join(DATA_PATH, RAKUTEN_IGNORE)
        ignores = set()
        try:
            with open(fpath, "r", encoding="utf-8") as fd:
                for line in fd:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignores.add(line)
        except FileNotFoundError:
            pass
        return ignores

    def _selectedLocations(self):
        return getselectedregions()

    def _defaultLocation(self):
        return config.plugins.rakutentv.region.value

    def _picons_config(self):
        return config.plugins.rakutentv.picons

    def _fetchChannels(self, cc):
        return rakutenRequest.getChannels(cc)

    def _bouquetName(self, cc):
        return BOUQUET_NAME % REGION_NAMES.get(cc, cc).upper()

    def _importGuide(self, cc):
        """Import EPG events from the Rakuten TV API."""
        xmltv_data = rakutenRequest.getEPG(cc)
        if not xmltv_data:
            return

        # Build channel ref mapping: channel_id -> service ref
        channels_map = {}
        for cat in self.categories:
            if cat in self.channelsList:
                for ch_sid, _ch_hash, _ch_name, _ch_logourl, _id, _lang in self.channelsList[cat]:
                    ref = f"4097:0:1:{ch_sid}:{self.tsid}:1:2:0:0:0"
                    channels_map[_id] = ref
                    channels_map[_id.lower()] = ref

        if not importXMLTVGuide(self.epgcache, self.LOG_PREFIX, "/tmp/rakutentv-epg.xml", xmltv_data, channels_map):
            self.epgimport_missing = True

    def _buildBouquetEntry(self, key, chitem):
        ch_sid, _ch_hash, ch_name, ch_logourl, _id, language_id = self.channelsList[key][chitem]
        stream_url = rakutenRequest.getLiveStreamURL(_id, language_id, self.bouquetCC).replace(":", "%3a")
        ref = f"4097:0:1:{ch_sid}:{self.tsid}:1:2:0:0:0"
        return ref, stream_url, ch_name, ch_logourl

    def buildM3U(self, channel):
        logo = channel.get("logo", "")
        group = channel.get("category", "")
        _id = channel["_id"]

        if _id in self.ignore_list:
            return False

        if group not in self.channelsList:
            self.channelsList[group] = []
            self.categories.append(group)

        sid = int(channel["number"])
        if sid <= 0:
            sid = (zlib.crc32(_id.encode("utf-8")) & 0xFFFF) or 1
        while sid in self.usedServiceIds:
            sid = (sid + 1) & 0xFFFF or 1
        self.usedServiceIds.add(sid)
        number = f"{sid:X}"

        self.channelsList[group].append((str(number), _id, channel["name"], logo, _id, channel.get("language_id", "ENG")))
        return True


class RakutenTVDownload(TVDownloadScreenMixin, RakutenTVDownloadBase, Screen):

    EXIT_CONFIRM_TEXT = _("The download is in progress. Exit now?")

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.skinName = "DownloadProgress"
        self.title = _("Rakuten TV updating")
        RakutenTVDownloadBase.__init__(self)
        self.total = 0
        self["progress"] = ProgressBar()
        self["action"] = Label()
        self.updateAction()
        self["wait"] = Label()
        self["status"] = Label(_("Please wait..."))
        self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.exit}, -1)
        self.onFirstExecBegin.append(self.init)

    def updateAction(self, cc=""):
        self["action"].text = _("Updating: Rakuten TV %s") % cc.upper()

    def noCategories(self):
        self.session.openWithCallback(self.exitOk, MessageBox, _("There is no data, it is possible that Rakuten TV is not available in your region"), type=MessageBox.TYPE_ERROR, timeout=10)

    def _restartSilentTimer(self):
        Silent.stop()
        Silent.start()


class DownloadSilent(TVDownloadSilentMixin, RakutenTVDownloadBase):

    BOUQUET_MARKER = "rakutentv"
    FRIENDLY_NAME = "Rakuten TV"
    LOCATION_WORD = "region"

    def __init__(self):
        self.afterUpdate = []
        RakutenTVDownloadBase.__init__(self, silent=True)
        self.timer = eTimer()
        self.timer.timeout.get().append(self.download)


Silent = DownloadSilent()
