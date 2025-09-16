from context import PluginContext, GameState
from modules.legacy import GoogleReporter
from modules.debug import debug
from modules.lib.journal import JournalEntry
from modules.lib.module import Module

# функция перевода
import functools
_translate = functools.partial(PluginContext._tr_template, filepath=__file__)


class DeliveryTracker(Module):
    localized_name = _translate("Colonisation delivery tracker")

    def __init__(self):
        self.docked_on_cs: bool = False
        self.construction_site: str | None = None
        self.cargo: dict[str, int] = dict()

    def on_journal_entry(self, entry: JournalEntry):
        def _get_construction_type() -> str | None:
            # колонизационный корабль
            station_name: str = entry.data.get("StationName", "")
            if station_name == "System Colonisation Ship" or "$EXT_PANEL_ColonisationShip" in station_name:
                debug(f"Detected '{event}' on a colonisation ship (primary port construction site).")
                return "Primary port"
            # орбитальные постройки
            station_type: str = entry.data.get("StationType", "")
            if station_type == "SpaceConstructionDepot":
                future_name = station_name.split(': ')[1]
                debug(f"Detected '{event}' on an orbital construction site; construction name - {future_name}.")
                return f"Space construction: {future_name}"
            # наземные постройки
            if station_type == "PlanetaryConstructionDepot":
                future_name = station_name.split(': ')[1]
                debug(f"Detected '{event}' on a planetary construction site; construction name - {future_name}.")
                return f"Planetary construction: {future_name}"
            return None

        event: str = entry.data["event"]
        if event in ("Location", "Docked"):
            self.construction_type = _get_construction_type()
            self.docked_on_cs = self.construction_type is not None
        # брабфанка: игра может затупить с обновлением груза и прописать его после отстыковки,
        # поэтому вместо неё (event == "Undocked") будем отслеживать выход из инстанса
        elif (
            event in ("Shutdown", "Died", "SelfDestruct", "StartJump")
            or event == "Music" and entry.data.get("MusicTrack") == "MainMenu"
        ):
            self.docked_on_cs = False
            self.construction_site = None
        self.update_cargo(entry.state)

    def update_cargo(self, state: dict):
        new_cargo = state.get("Cargo", {})
        if self.docked_on_cs:
            diff: dict[str, int] = {
                item: self.cargo[item] - new_cargo.get(item, 0)
                for item in self.cargo
                if self.cargo[item] != new_cargo.get(item, 0)
            }
            if diff:
                self._report(diff)
        self.cargo = new_cargo

    def _report(self, delivered: dict[str, int]):
        debug(
            "Detected colonisation delivery: "
            f"system: {GameState.system}, "
            f"construction: {self.construction_type}, "
            f"cargo diff: {delivered}"
        )
        url = "https://docs.google.com/forms/d/e/1FAIpQLSdbG8pQUHDryAkd1ReEIEo25zOs6LUPErUElytgwI8wmfWAUA/formResponse?usp=pp_url"
        for item, amount in delivered.items():
            params = {
                "entry.1492553995": GameState.cmdr,
                "entry.639938351": GameState.system.replace("'", "’"),
                "entry.1059020094": self.construction_type.replace("'", "’"),
                "entry.173800538": item,
                "entry.883168154": amount
            }
            GoogleReporter(url, params.copy()).start()
