# Copyright (C) 2026 by xcentaurix

from Plugins.Plugin import PluginDescriptor
from skin import findSkinScreen

from . import _
from .RakutenTVDownload import RakutenTVDownload, Silent
from .RakutenTVCockpit import RakutenTVCockpit
from .Variables import PLUGIN_ICON
from .SkinUtils import loadPluginSkin


if findSkinScreen("RakutenTVCockpit") is None:
    loadPluginSkin()


def sessionstart(reason, session, **_kwargs):  # pylint: disable=unused-argument
    Silent.init(session)


def Download_RakutenTV(session, **_kwargs):
    session.open(RakutenTVDownload)


def system(session, **_kwargs):
    session.open(RakutenTVCockpit)


def Plugins(**_kwargs):
    return [
        PluginDescriptor(
            name=_("RakutenTVCockpit"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=PLUGIN_ICON,
            description=_("Browse FAST channels from Rakuten TV"),
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
