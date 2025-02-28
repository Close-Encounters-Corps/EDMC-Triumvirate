from modules.legacy import Reporter
from modules.debug import debug
from modules.lib.journal import JournalEntry
from modules.lib.module import Module


class DeliveryTracker(Module):
    def __init__(self):
        self.docked_on_cs: bool = False
        self.cargo: dict[str, int] = dict()

    def on_journal_entry(self, entry: JournalEntry):
        event: str = entry.data["event"]
        if event == "Location":
            self.docked_on_cs = entry.data.get("Docked") is True and entry.data.get("StationName") == "System Colonisation Ship"
        elif event == "Docked":
            self.docked_on_cs = entry.data.get("StationName") == "System Colonisation Ship"
        # брабфанка: игра может затупить с обновлением груза и прописать его после отстыковки,
        # поэтому вместо неё (event == "Undocked") будем отслеживать выход из инстанса
        elif (
            event in ("Shutdown", "Died", "SelfDestruct", "StartJump")
            or event == "Music" and entry.data.get("MusicTrack") == "MainMenu"
        ):
            self.docked_on_cs = False
        self.update_cargo(entry.state, entry.cmdr, entry.system)

    def update_cargo(self, state: dict, cmdr: str, system: str):
        new_cargo = state.get("Cargo", {})
        if self.docked_on_cs:
            diff: dict[str, int] = {
                item: self.cargo[item] - new_cargo.get(item, 0)
                for item in self.cargo
                if self.cargo[item] != new_cargo.get(item, 0)
            }
            if diff:
                self._report(diff, cmdr, system)
        self.cargo = new_cargo

    def _report(self, delivered: dict[str, int], cmdr: str, system: str):
        debug(f"[ColonisationTracker] Detected colonisation delivery, cargo diff: {delivered}")
        url = "https://docs.google.com/forms/d/e/1FAIpQLSdbG8pQUHDryAkd1ReEIEo25zOs6LUPErUElytgwI8wmfWAUA/formResponse?usp=pp_url"
        for item, amount in delivered.items():
            params = {
                "entry.1492553995": cmdr,
                "entry.639938351": system,
                "entry.173800538": item,
                "entry.883168154": amount
            }
            Reporter(url, params.copy()).start()
