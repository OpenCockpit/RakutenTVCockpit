# Copyright (C) 2026 by xcentaurix

from Components.config import config
from Plugins.Plugin import PluginDescriptor
from skin import findSkinScreen

from .PluginUpgrade import checkPluginUpdateAndOpen
from . import _
from . import ConfigInit  # noqa: F401, pylint: disable=unused-import
from .RakutenTVDownload import RakutenTVDownload, Silent
from .RakutenTVCockpit import RakutenTVCockpit
from .Variables import PLUGIN_ICON
from .SkinUtils import loadPluginSkin
from .Version import VERSION
from .Debug import logger


if findSkinScreen("RakutenTVCockpit") is None:
    loadPluginSkin()


def sessionstart(reason, session, **_kwargs):  # pylint: disable=unused-argument
    logger.info("+++ Version: %s starts...", VERSION)
    Silent.init(session)


def Download_RakutenTV(session, **_kwargs):
    session.open(RakutenTVDownload)


def system(session, **_kwargs):
    checkPluginUpdateAndOpen(
        session, "enigma2-plugin-extensions-rakutentvcockpit", "RakutenTVCockpit",
        RakutenTVCockpit, config.plugins.rakutentv.auto_update_check)


def Plugins(**_kwargs):
    return [
        PluginDescriptor(
            name=_("RakutenTVCockpit"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=PLUGIN_ICON,
            description=_("Live-TV Bouquet Management"),
            fnc=system,
            needsRestart=True
        ),
        PluginDescriptor(
            name=_("Download Rakuten TV bouquet and picons"),
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=Download_RakutenTV,
            needsRestart=True
        ),
        PluginDescriptor(
            name=_("Silently download Rakuten TV"),
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=sessionstart
        ),
    ]
