# Copyright (C) 2026 by xcentaurix

from Components.Console import Console
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Standby import QUIT_RESTART, TryQuitMainloop
from skin import findSkinScreen

from .PluginUtils import checkPluginUpdate
from . import _
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
    if config.plugins.rakutentv.auto_update_check.value != "yes":
        session.open(RakutenTVCockpit)
        return

    update = checkPluginUpdate("enigma2-plugin-extensions-rakutentvcockpit")
    if update:
        def _installUpdate(answer):
            if answer:
                def _showRestartPrompt(_data, _retval, _extra_args):
                    session.openWithCallback(
                        lambda restart: session.open(RakutenTVCockpit) if not restart else session.open(TryQuitMainloop, QUIT_RESTART),
                        MessageBox,
                        _("The package has been installed. Restart Enigma2 now to load the update?"),
                        type=MessageBox.TYPE_YESNO,
                        default=True
                    )

                install_cmd = f"opkg install {update['path'] or update['package']}"
                Console().ePopen(install_cmd, _showRestartPrompt)
                return

            session.open(RakutenTVCockpit)

        session.openWithCallback(
            _installUpdate,
            MessageBox,
            _("A newer RakutenTVCockpit package (%s) is available. Do you want to install it now?") % update["version"],
            type=MessageBox.TYPE_YESNO,
            default=False
        )
        return

    session.open(RakutenTVCockpit)


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
