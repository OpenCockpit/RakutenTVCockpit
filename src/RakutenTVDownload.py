# Copyright (C) 2026 by xcentaurix

import os
import re
import time

from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists
from enigma import eDVBDB, eEPGCache, eTimer
from twisted.internet import threads, reactor

from . import _
from .RakutenTVConfig import REGION_NAMES, TSIDS, getselectedregions
from .RakutenTVRequest import rakutenRequest
from .PiconFetcher import PiconFetcher
from .Variables import TIMER_FILE, BOUQUET_FILE, BOUQUET_NAME


# Data paths for ignore list
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
RAKUTEN_IGNORE = "rakutentv.ignore"


class RakutenTVDownloadBase:
    downloadActive = False

    def __init__(self, silent=False):
        self.channelsList = {}
        self.categories = []
        self.state = 1
        self.silent = silent
        self.epgcache = eEPGCache.getInstance()
        RakutenTVDownloadBase.downloadActive = False
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

    def cc(self):
        """Yield selected regions and clean up deselected bouquets."""
        regions = [x for x in getselectedregions() if x] or [config.plugins.rakutentv.region.value]
        eDVBDB.getInstance().removeBouquet(re.escape(BOUQUET_FILE) % f"(?!{'|'.join(regions)}).+")
        yield from regions

    def download(self):
        if RakutenTVDownloadBase.downloadActive:
            if not self.silent:
                self.session.openWithCallback(self.close, MessageBox, _("A silent download is in progress."), MessageBox.TYPE_INFO, timeout=30)
            print("[RakutenTV Download] A silent download is in progress.")
            return
        self.ccGenerator = self.cc()
        self.piconFetcher = PiconFetcher(self)
        threads.deferToThread(self._downloadThread)

    def _downloadThread(self):
        """Run the entire download workflow in a background thread."""
        try:
            self._managerThread()
        except Exception as e:
            print(f"[RakutenTV Download] Error in download thread: {e}")
            RakutenTVDownloadBase.downloadActive = False

    def _managerThread(self):
        RakutenTVDownloadBase.downloadActive = True
        if cc := next(self.ccGenerator, None):
            self._downloadBouquetThread(cc)
        else:
            self.channelsList.clear()
            self.categories.clear()
            RakutenTVDownloadBase.downloadActive = False
            self.ccGenerator = None
            if self.piconFetcher.piconList:
                self.total = len(self.piconFetcher.piconList)
                reactor.callFromThread(self.updateProgressBar, 0)
                reactor.callFromThread(self.updateAction, _("picons"))
                reactor.callFromThread(self.updateStatus, _("Fetching picons..."))
                self.piconFetcher.fetchPicons()
                reactor.callFromThread(self.updateProgressBar, self.total)
            self.piconFetcher = None
            reactor.callFromThread(self.updateStatus, _("LiveTV update completed"))
            time.sleep(3)
            reactor.callFromThread(self.exitOk)
            reactor.callFromThread(self.start)

    def manager(self):
        """Legacy entry point - redirects to threaded version."""
        threads.deferToThread(self._managerThread)

    def _downloadBouquetThread(self, cc):
        self.bouquet = []
        self.bouquetCC = cc
        self.tsid = TSIDS.get(cc, "0")
        reactor.callFromThread(self.stop)
        self.channelsList.clear()
        self.categories.clear()
        reactor.callFromThread(self.updateAction, cc)
        reactor.callFromThread(self.updateProgressBar, 0)
        reactor.callFromThread(self.updateStatus, _("Processing data..."))

        channels = sorted(rakutenRequest.getChannels(cc), key=lambda x: x["number"])
        for channel in channels:
            self.buildM3U(channel)

        self.categories.sort(key=str.casefold)
        for _group, channels_in_group in self.channelsList.items():
            channels_in_group.sort(key=lambda ch: ch[2].casefold())

        self.total = len(channels)

        if len(self.categories) == 0:
            reactor.callFromThread(self.noCategories)
        else:
            if self.categories[0] in self.channelsList:
                self.subtotal = len(self.channelsList[self.categories[0]])
            else:
                self.subtotal = 0
            self.key = 0
            self.chitem = 0

            self._importEPG(cc)

            for i in range(self.total + 1):
                self.updateprogress(param=i)

    def _importEPG(self, cc):
        """Import EPG events from the Rakuten TV API."""
        fn = "/tmp/rakutentv-epg.xml"
        try:
            xmltv_data = rakutenRequest.getEPG(cc)
            if not xmltv_data:
                return

            with open(fn, "wb") as fp:
                fp.write(xmltv_data)

            # Build channel ref mapping: channel_id -> service ref
            channels_map = {}
            for cat in self.categories:
                if cat in self.channelsList:
                    for ch_sid, _ch_hash, _ch_name, _ch_logourl, _id, _lang in self.channelsList[cat]:
                        ref = f"4097:0:1:{ch_sid}:{self.tsid}:1:2:0:0:0"
                        channels_map[_id] = ref
                        channels_map[_id.lower()] = ref

            try:
                from Plugins.Extensions.EPGImport.xmltvconverter import XMLTVConverter
            except ImportError:
                print("[RakutenTV Download] EPGImport not available, skipping EPG import")
                return

            with open(fn, "rb") as fp:
                xmltv_parser = XMLTVConverter(channels_map, {})
                evt_cnt = 0
                for item in xmltv_parser.enumFile(fp):
                    if not item:
                        continue
                    sref, event = item
                    evt_cnt += 1
                    reactor.callFromThread(self.epgcache.importEvents, sref, [event])
                print(f"[RakutenTV Download] {evt_cnt} EPG events imported for {cc}")
        except Exception as e:
            print(f"[RakutenTV Download] EPG import error for {cc}: {e}")
        finally:
            if os.path.exists(fn):
                os.unlink(fn)

    def updateprogress(self, param):
        if hasattr(self, "state") and self.state == 1:
            reactor.callFromThread(self.updateProgressBar, param)
            if param < self.total:
                key = self.categories[self.key]
                if self.chitem == self.subtotal:
                    self.chitem = 0
                    found = False
                    while not found:
                        self.key += 1
                        key = self.categories[self.key]
                        found = key in self.channelsList
                    self.subtotal = len(self.channelsList[key])

                if self.chitem == 0:
                    self.bouquet.append(f"1:64:{self.key}:0:0:0:0:0:0:0::{self.categories[self.key]}")

                ch_sid, _ch_hash, ch_name, ch_logourl, _id, language_id = self.channelsList[key][self.chitem]

                stream_url = rakutenRequest.getLiveStreamURL(_id, language_id, self.bouquetCC).replace(":", "%3a")

                ref = f"4097:0:1:{ch_sid}:{self.tsid}:1:2:0:0:0"
                self.bouquet.append(f"{ref}:{stream_url}:{ch_name}")
                self.chitem += 1
                reactor.callFromThread(self.updateStatus, _("Waiting for Channel: ") + ch_name)

                self.piconFetcher.addPicon(ref, ch_name, ch_logourl, self.silent)
            else:
                bouquet_name = BOUQUET_NAME % REGION_NAMES.get(self.bouquetCC, self.bouquetCC).upper()
                bouquet_file = BOUQUET_FILE % self.bouquetCC
                reactor.callFromThread(eDVBDB.getInstance().addOrUpdateBouquet, bouquet_name, bouquet_file, self.bouquet, False)
                bouquet_path = "/etc/enigma2/" + bouquet_file
                if os.path.isfile(bouquet_path):
                    with open(bouquet_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    if lines and lines[0].startswith("#NAME"):
                        lines[0] = f"#NAME {bouquet_name}\r\n"
                        with open(bouquet_path, "w", encoding="utf-8") as f:
                            f.writelines(lines)
                os.makedirs(os.path.dirname(TIMER_FILE), exist_ok=True)
                with open(TIMER_FILE, "w", encoding="utf-8") as f:
                    f.write(str(time.time()))
                self._managerThread()

    def buildM3U(self, channel):
        logo = channel.get("logo", "")
        group = channel.get("category", "")
        _id = channel["_id"]

        if _id in self.ignore_list:
            return False

        if group not in self.channelsList:
            self.channelsList[group] = []
            self.categories.append(group)

        if int(channel["number"]) == 0:
            number = _id[-4:].upper()
        else:
            number = f"{channel['number']:X}"

        self.channelsList[group].append((str(number), _id, channel["name"], logo, _id, channel.get("language_id", "ENG")))
        return True

    def start(self):
        pass

    def stop(self):
        pass

    def exitOk(self, answer=None):
        pass

    def updateProgressBar(self, param):
        pass

    def updateStatus(self, name):
        pass

    def updateAction(self, cc=""):
        pass

    def noCategories(self):
        pass


class RakutenTVDownload(RakutenTVDownloadBase, Screen):

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

    def init(self):
        self["progress"].setValue(0)
        threads.deferToThread(self.download)

    def exit(self):
        self.session.openWithCallback(self.cleanup, MessageBox, _("The download is in progress. Exit now?"), MessageBox.TYPE_YESNO, timeout=30)

    def cleanup(self, answer=None):
        if answer:
            RakutenTVDownloadBase.downloadActive = False
            self.exitOk(answer)

    def exitOk(self, answer=True):
        if answer:
            Silent.stop()
            Silent.start()
            self.close(True)

    def updateProgressBar(self, param):
        try:
            progress = min(((param + 1) * 100) // self.total, 100)
        except Exception:
            progress = 0
        self["progress"].setValue(progress)
        self["wait"].text = str(progress) + " %"

    def updateStatus(self, name):
        self["status"].text = name

    def noCategories(self):
        self.session.openWithCallback(self.exitOk, MessageBox, _("There is no data, it is possible that Rakuten TV is not available in your region"), type=MessageBox.TYPE_ERROR, timeout=10)


class DownloadSilent(RakutenTVDownloadBase):
    def __init__(self):
        self.afterUpdate = []
        RakutenTVDownloadBase.__init__(self, silent=True)
        self.timer = eTimer()
        self.timer.timeout.get().append(self.download)

    def init(self, session):
        self.session = session
        with open("/etc/enigma2/bouquets.tv", "r", encoding="utf-8") as f:
            bouquets = f.read()
        if "rakutentv" in bouquets:
            self.start(True)

    def start(self, fromSessionStart=False):
        self.stop()
        minutes = 60 * 5
        if fileExists(TIMER_FILE):
            with open(TIMER_FILE, "r", encoding="utf-8") as f:
                last = float(f.read().strip())
            minutes -= int((time.time() - last) / 60)
            if minutes < 0:
                minutes = 1
        self.timer.startLongTimer(minutes * 60)
        if not fromSessionStart:
            self.afterUpdateCallbacks()

    def stop(self):
        self.timer.stop()

    def afterUpdateCallbacks(self):
        for f in self.afterUpdate:
            if callable(f):
                f()

    def noCategories(self):
        print("[Rakuten TV] There is no data, it is possible that Rakuten TV is not available in your region.")
        self.stop()
        os.makedirs(os.path.dirname(TIMER_FILE), exist_ok=True)
        with open(TIMER_FILE, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
        self.start()


Silent = DownloadSilent()
