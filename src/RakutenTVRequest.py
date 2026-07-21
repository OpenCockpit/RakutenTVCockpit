# Copyright (C) 2026 by xcentaurix

import time
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from Components.config import config
import requests

from .RakutenTVConfig import CLASSIFICATION_IDS, pickForwardIP
from .Variables import USER_AGENT
from .Debug import logger


class RakutenTVRequest:
    """API handler for Rakuten TV FAST channels."""

    API_BASE = "https://gizmo.rakuten.tv/v3"
    ORIGIN = "https://rakuten.tv"
    REFERER = "https://rakuten.tv/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Origin": self.ORIGIN,
            "Referer": self.REFERER,
        })
        self.requestCache = {}
        self._channels_cache = {}
        self._channels_cache_time = {}
        self._categories_cache = {}
        self._categories_cache_time = {}

    def _get_classification_id(self, region):
        return CLASSIFICATION_IDS.get(region, CLASSIFICATION_IDS.get("de", 307))

    def _get_base_params(self, region):
        return {
            "classification_id": self._get_classification_id(region),
            "device_identifier": "web",
            "locale": region,
            "market_code": region,
        }

    @staticmethod
    def _geoHeaders(region):
        """X-Forwarded-For header set, so playback authorization sees *region*'s IP."""
        ip = pickForwardIP(region)
        return {"X-Forwarded-For": ip} if ip else {}

    def getLiveChannels(self, region=None):
        """Fetch live channels from Rakuten TV API. Returns list of channel dicts."""
        region = region or config.plugins.rakutentv.region.value
        now = time.time()
        if region in self._channels_cache and now - self._channels_cache_time.get(region, 0) < 4 * 3600:
            return self._channels_cache[region]

        params = self._get_base_params(region)
        params["page"] = 1
        params["per_page"] = 200

        try:
            response = self.session.get(f"{self.API_BASE}/live_channels", params=params, headers=self._geoHeaders(region), timeout=10)
            response.raise_for_status()
            data = response.json()
            channels = data.get("data", [])
            self._channels_cache[region] = channels
            self._channels_cache_time[region] = now
            logger.debug("getLiveChannels: %s channels for %s", len(channels), region)
            return channels
        except Exception as e:
            logger.debug("getLiveChannels error: %s", e)
            return self._channels_cache.get(region, [])

    def getLiveChannelCategories(self, region=None):
        """Fetch channel categories from Rakuten TV API."""
        region = region or config.plugins.rakutentv.region.value
        now = time.time()
        if region in self._categories_cache and now - self._categories_cache_time.get(region, 0) < 4 * 3600:
            return self._categories_cache[region]

        params = self._get_base_params(region)

        try:
            response = self.session.get(f"{self.API_BASE}/live_channel_categories", params=params, headers=self._geoHeaders(region), timeout=10)
            response.raise_for_status()
            data = response.json()
            categories = data.get("data", [])
            self._categories_cache[region] = categories
            self._categories_cache_time[region] = now
            logger.debug("getLiveChannelCategories: %s categories for %s", len(categories), region)
            return categories
        except Exception as e:
            logger.debug("getLiveChannelCategories error: %s", e)
            return self._categories_cache.get(region, [])

    def getLiveStreamURL(self, channel_id, language_id, region=None):
        """Get HLS stream URL for a live channel via the AVOD streaming endpoint."""
        region = region or config.plugins.rakutentv.region.value
        params = self._get_base_params(region)
        params.update({
            "device_stream_audio_quality": "2.0",
            "device_stream_hdr_type": "NONE",
            "device_stream_video_quality": "FHD",
            "disable_dash_legacy_packages": False,
        })
        data = {
            "audio_language": language_id,
            "audio_quality": "2.0",
            "classification_id": self._get_classification_id(region),
            "content_id": channel_id,
            "content_type": "live_channels",
            "device_serial": "enigma2",
            "player": "web:HLS-NONE:NONE",
            "strict_video_quality": False,
            "subtitle_language": "MIS",
            "video_type": "stream",
        }

        try:
            response = self.session.post(f"{self.API_BASE}/avod/streamings", params=params, json=data, headers=self._geoHeaders(region), timeout=10)
            response.raise_for_status()
            result = response.json()
            stream_infos = result.get("data", {}).get("stream_infos", [])
            if stream_infos:
                url = stream_infos[0].get("url", "")
                return url
        except Exception as e:
            logger.debug("getLiveStreamURL error for %s: %s", channel_id, e)
        return ""

    def getChannels(self, region=None):
        """Get channels in a unified format (compatible with bouquet building).
        Returns list of channel dicts with _id, name, number, category, description, logo, stream_url, language_id."""
        region = region or config.plugins.rakutentv.region.value
        raw_channels = self.getLiveChannels(region)
        categories_raw = self.getLiveChannelCategories(region)

        cat_map = {}
        for category in categories_raw:
            cat_name = category.get("name", "Uncategorized")
            for ch_id in category.get("live_channels", []):
                cat_map[ch_id] = cat_name

        result = []
        for ch in raw_channels:
            ch_id = ch.get("id", "")
            if not ch_id:
                continue

            langs = []
            for lang in ch.get("labels", {}).get("languages", []):
                lang_id = lang.get("id")
                if lang_id:
                    langs.append(lang_id)

            logo = ""
            images = ch.get("images", {})
            if images:
                for key in ("artwork", "snapshot", "poster"):
                    if key in images:
                        logo = images[key]
                        break
                if not logo:
                    logo = next(iter(images.values()), "")

            classification = ch.get("classification", {})
            description = classification.get("description", "") if isinstance(classification, dict) else ""

            result.append({
                "_id": ch_id,
                "name": ch.get("title", ""),
                "number": int(ch.get("channel_number", 0) or 0),
                "category": cat_map.get(ch_id, "Uncategorized"),
                "description": description,
                "logo": logo,
                "stream_url": "",
                "language_id": langs[0] if langs else "ENG",
            })

        result.sort(key=lambda x: x["number"])
        return result

    def getLiveCategories(self, region=None):
        """Get live channels grouped by category for the plugin browser UI."""
        region = region or config.plugins.rakutentv.region.value
        channels = self.getChannels(region)
        if not channels:
            return []

        categories = {}
        for ch in channels:
            group = ch.get("category", "Uncategorized")
            if group not in categories:
                categories[group] = {
                    "name": group,
                    "items": [],
                }
            categories[group]["items"].append({
                "_id": ch["_id"],
                "name": ch.get("name", ""),
                "summary": ch.get("description", ""),
                "genre": group,
                "rating": "",
                "duration": 0,
                "type": "channel",
                "stream_url": "",
                "logo": ch.get("logo", ""),
                "language_id": ch.get("language_id", "ENG"),
            })

        return sorted(categories.values(), key=lambda x: x["name"].casefold())

    def buildStreamURL(self, channel_id, region=None):
        """Resolve the actual HLS stream URL for a channel."""
        region = region or config.plugins.rakutentv.region.value
        channels = self.getChannels(region)
        for ch in channels:
            if ch["_id"] == channel_id:
                return self.getLiveStreamURL(channel_id, ch.get("language_id", "ENG"), region)
        return ""

    def _fetchEPGWindow(self, region, start_dt, end_dt):
        """Fetch one EPG window from the API. Returns list of channel dicts."""
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        params = self._get_base_params(region)
        params.update({
            "per_page": 250,
            "device_stream_audio_quality": "2.0",
            "device_stream_hdr_type": "NONE",
            "device_stream_video_quality": "FHD",
            "epg_duration_minutes": duration_minutes,
            "epg_starts_at": start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "epg_starts_at_timestamp": int(start_dt.timestamp()),
            "epg_ends_at": end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "epg_ends_at_timestamp": int(end_dt.timestamp()),
        })
        try:
            response = self.session.get(f"{self.API_BASE}/live_channels", params=params, headers=self._geoHeaders(region), timeout=60)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.debug("getEPG window error: %s", e)
            return []

    def getEPG(self, region=None, hours=48):
        """Fetch EPG data from the Rakuten TV API and return XMLTV XML bytes.
        Fetches in 24-hour windows to avoid 503 errors on large regions."""
        region = region or config.plugins.rakutentv.region.value
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        end = now + timedelta(hours=hours)

        channel_names = {}
        programmes = []
        cursor = now
        while cursor < end:
            window_end = min(cursor + timedelta(hours=24), end)
            channels = self._fetchEPGWindow(region, cursor, window_end)
            for ch in channels:
                ch_id = ch.get("id", "")
                if not ch_id:
                    continue
                if ch_id not in channel_names:
                    channel_names[ch_id] = ch.get("title", "")
                for prog in ch.get("live_programs", []):
                    start = prog.get("starts_at", "")
                    stop = prog.get("ends_at", "")
                    if start and stop:
                        programmes.append((ch_id, start, stop,
                                           prog.get("title", ""),
                                           prog.get("subtitle", "") or "",
                                           prog.get("description", "") or ""))
            cursor = window_end

        if not programmes:
            logger.debug("getEPG: no events for %s", region)
            return None

        seen = set()
        unique = []
        for p in programmes:
            key = (p[0], p[1], p[2])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']
        for ch_id, title in channel_names.items():
            lines.append(f'  <channel id="{escape(ch_id)}">')
            lines.append(f'    <display-name>{escape(title)}</display-name>')
            lines.append('  </channel>')
        for ch_id, start, stop, title, subtitle, desc in unique:
            start_fmt = self._to_xmltv_time(start)
            stop_fmt = self._to_xmltv_time(stop)
            if not start_fmt or not stop_fmt:
                continue
            lines.append(f'  <programme start="{start_fmt}" stop="{stop_fmt}" channel="{escape(ch_id)}">')
            lines.append(f'    <title>{escape(title)}</title>')
            if subtitle:
                lines.append(f'    <sub-title>{escape(subtitle)}</sub-title>')
            if desc:
                lines.append(f'    <desc>{escape(desc)}</desc>')
            lines.append('  </programme>')
        lines.append('</tv>')
        logger.debug("getEPG: %s events for %s", len(unique), region)
        return "\n".join(lines).encode("utf-8")

    @staticmethod
    def _to_xmltv_time(iso_str):
        """Convert ISO 8601 timestamp to XMLTV format (YYYYMMDDHHmmSS +0000)."""
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.strftime("%Y%m%d%H%M%S %z")
        except (ValueError, AttributeError):
            return ""


rakutenRequest = RakutenTVRequest()
