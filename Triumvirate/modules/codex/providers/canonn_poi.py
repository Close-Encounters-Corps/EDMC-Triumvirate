import requests

from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.settings import canonn_cloud_url_us_central, poi_categories
from Triumvirate.core.shortcuts import debug, error, warning
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module


# isort: off
import functools
_translate = functools.partial(PluginContext._tr_template, filepath=__file__)
# isort: on


class CanonnPOI(Module):
    URL = f"{canonn_cloud_url_us_central}/query/getSystemPoi"

    @property
    def localized_name(self) -> str:
        return _translate("Codex module")

    def __init__(self):
        PluginContext.codex_ui.register(self)
        self.destination_system: str | None = None


    def on_journal_entry(self, entry: JournalEntry):
        if not PluginContext.codex_ui.display_enabled_for(self):
            return
        if GameState.gamemode != 'MainGame':
            return

        event = entry.data.get("event")
        if event == "StartJump" and entry.data.get("JumpType") == "Hyperspace":
            self.destination_system = entry.data["StarSystem"]
        elif event == "FSDJump":
            if (system := entry.data["StarSystem"]) == self.destination_system:
                # в противном случае это, скорее всего, таргоидский перехват, и мы всё ещё в старой системе
                self.fetch_data(system)
            self.destination_system = None
        elif event in ("Location", "CarrierJump"):
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
            error("Couldn't fetch system POIs from Canonn. Exception info:", exc_info=e)
            return

        data: list[dict] = res.json().get("codex")
        if not data:
            debug("No POIs from Canonn in this system.")
            return

        debug("Got POI data from Canonn.")
        for poi in data:
            if poi.get("body") is None:
                warning(f"Canonn POI entry contains null body: {poi}")
                continue
            if poi.get("english_name") is None:
                warning(f"Canonn POI entry contains null name: {poi}")
                continue
            if (category := poi.get("hud_category")) is not None and category not in poi_categories:
                warning(f"Unexpected POI category in Canonn data: {poi}")
                continue
            if poi.get("scanned", False) in ('false', False):  # без понятия, почему оно (иногда?) даётся строкой
                PluginContext.codex_ui.show(
                    caller=self,
                    location=poi.get("body"),
                    text=poi.get("english_name"),  # pyright: ignore[reportArgumentType]
                    category=category,  # pyright: ignore[reportArgumentType]
                )
