import requests

from context import PluginContext, GameState
from settings import poi_categories, canonn_cloud_url_us_central
from modules.debug import debug, warning
from modules.lib.journal import JournalEntry
from modules.lib.module import Module

# Подключение функции перевода от EDMC
import l10n, functools                  # noqa: E401
_translate = functools.partial(l10n.translations.tl, context=__file__)


class CanonnCodexPOI(Module):
    localized_name = _translate("Codex module")
    URL = f"{canonn_cloud_url_us_central}/query/getSystemPoi"

    def __init__(self):
        PluginContext.exp_visualizer.register(self)
        self.destination_system: str = None


    def on_journal_entry(self, entry: JournalEntry):
        if not PluginContext.exp_visualizer.display_enabled_for(self):
            return

        event = entry.data.get("event")
        if event == "StartJump" and entry.data.get("JumpType") == "Hyperspace":
            self.destination_system = entry.data.get("StarSystem")
        elif event == "FSDJump":
            if (system := entry.data["StarSystem"]) == self.destination_system:
                self.fetch_data(system)
            self.destination_system = None
        elif event == "Location":
            self.fetch_data(entry.data["StarSystem"])


    def fetch_data(self, system: str):
        params = {
            "cmdr": GameState.cmdr,
            "system": system,
            "odyssey": GameState.odyssey
        }
        try:
            res = requests.get(self.URL, params=params)
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
                PluginContext.exp_visualizer.show(
                    caller=self,
                    body=poi.get("body"),
                    text=poi.get("english_name"),
                    category=category
                )
