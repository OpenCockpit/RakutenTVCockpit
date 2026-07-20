import os
from Tools.Directories import resolveFilename, SCOPE_CONFIG
from .Version import PLUGIN


TIMER_FILE = os.path.join(os.path.realpath(resolveFilename(SCOPE_CONFIG)), PLUGIN, PLUGIN + ".timer")
RESUMEPOINTS_FILE = os.path.join(os.path.realpath(resolveFilename(SCOPE_CONFIG)), PLUGIN, "resumepoints.pkl")
PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))
PLUGIN_ICON = "plugin.jpg"
BOUQUET_FILE = "userbouquet.rakutentvcockpit_%s.tv"
BOUQUET_NAME = "Rakuten TV Cockpit (%s)"
CHANNELLIST_FILE = "channellist.rakutentvcockpit_%s.m3u8"
XMLTV_FILE = "xmltv.rakutentvcockpit_%s.xml"
NUMBER_OF_LIVETV_BOUQUETS = 5
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
