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
        self.cargo: dict[str, int] = dict()

    def on_journal_entry(self, entry: JournalEntry):
        def on_colonisation_ship():
            station_name: str = entry.data.get("StationName", "")
            return station_name == "System Colonisation Ship" or "$EXT_PANEL_ColonisationShip" in station_name

        event: str = entry.data["event"]
        if event == "Location":
            docked = entry.data.get("Docked", False)
            colonisation_ship = on_colonisation_ship()
            self.docked_on_cs = docked and colonisation_ship
        elif event == "Docked":
            self.docked_on_cs = on_colonisation_ship()
        # брабфанка: игра может затупить с обновлением груза и прописать его после отстыковки,
        # поэтому вместо неё (event == "Undocked") будем отслеживать выход из инстанса
        elif (
            event in ("Shutdown", "Died", "SelfDestruct", "StartJump")
            or event == "Music" and entry.data.get("MusicTrack") == "MainMenu"
        ):
            self.docked_on_cs = False
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
        debug(f"[ColonisationTracker] Detected colonisation delivery, cargo diff: {delivered}")
        url = "https://docs.google.com/forms/d/e/1FAIpQLSdbG8pQUHDryAkd1ReEIEo25zOs6LUPErUElytgwI8wmfWAUA/formResponse?usp=pp_url"
        for item, amount in delivered.items():
            params = {
                "entry.1492553995": GameState.cmdr,
                "entry.639938351": GameState.system,
                "entry.173800538": item,
                "entry.883168154": amount
            }
            GoogleReporter(url, params.copy()).start()
