from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module
from Triumvirate.modules.bgs.submodules.base import BGSSubmodule
from Triumvirate.modules.legacy import URL_GOOGLE


class ExpDataTracker(Module, BGSSubmodule):
    @property
    def localized_name(self) -> str:
        return _translate("Exploration data tracker")

    def __init__(self):
        self.station_owner: str | None = None

    def on_journal_entry(self, entry: JournalEntry):
        if GameState.gamemode != 'MainGame':
            return

        raw = entry.data
        event = raw["event"]
        if event == "Docked" or (event == "Location" and raw["Docked"] is True):
            self.station_owner = raw["StationFaction"]["Name"]
            return
        elif event == "Undocked" or (event == "Location" and raw["Docked"] is False):
            self.station_owner = None
            return
        elif event != "SellExplorationData":
            return

        # игнорируем флитаки
        if self.station_owner == "FleetCarrier":
            return

        url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse'
        amount = raw["TotalEarnings"]
        params = {
            "entry.503143076": GameState.cmdr,
            "entry.1108939645": "SellExpData",
            "entry.127349896": GameState.system,
            "entry.442800983": GameState.station,
            "entry.48514656": self.station_owner,
            "entry.351553038": amount,
            "usp": "pp_url"
        }
        PluginContext.logger.debug(f"Sold exploration data: station owner - {self.station_owner}, total amount - {amount} cr.")
        self.send_bgs_report(url, params, GameState.system)  # pyright: ignore[reportArgumentType]
