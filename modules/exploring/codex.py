import requests

from context import PluginContext, GameState
from settings import canonn_realtime_url, poi_categories
from modules.debug import debug, warning
from modules.lib.journal import JournalEntry
from modules.lib.module import Module


class CanonnPOIFetcher(Module):
    URL = f"{canonn_realtime_url}/query/getSystemPoi"

    def __init__(self):
        PluginContext.visualizer.register(self)
        self.destination_system: str = None


    def on_journal_entry(self, entry: JournalEntry):
        event = entry.data.get("event")
        if event == "StartJump" and entry.data.get("JumpType") == "Hyperspace":
            self.destination_system = entry.data.get("SystemName")
        elif event == "FSDJump" and (system := entry.data["StarSystem"] == self.destination_system):
            self.fetch_data(system)
        elif event == "Location":
            self.fetch_data(entry.data["StarSystem"])


    def fetch_data(self, system: str):
        url = f"{canonn_realtime_url}/query/getSystemPoi"
        params = {
            "cmdr": GameState.cmdr,
            "system": system,
            "odyssey": GameState.odyssey
        }
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()
        except requests.RequestException as e:
            PluginContext.logger.error("[Codex] Couldn't fetch system POIs from Canonn.", exc_info=e)
            return

        data: list[dict] = res.json().get("codex")
        if not data:
            debug("[Codex] No POIs from Canonn in this system.")
            return

        debug("[Codex] Got POI data from Canonn.")
        for poi in data:
            if poi.get("body") is None:
                warning("[Codex] Canonn POI entry contains null body: {}".format(poi))
                continue
            if poi.get("english_name") is None:
                warning("[Codex] Canonn POI entry contains null name: {}".format(poi))
                continue
            if (category := poi.get("hud_category")) is not None and category not in poi_categories:
                warning("[Codex] Unexpected POI category in Canonn data: {}".format(poi))
                continue
            if poi.get("scanned", False) in ('false', False):       # без понятия, почему оно (иногда?) даётся строкой
                PluginContext.visualizer.show(
                    caller=self,
                    body=poi.get("body"),
                    text=poi.get("english_name"),
                    category=category
                )
