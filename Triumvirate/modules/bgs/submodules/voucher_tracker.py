from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module
from Triumvirate.modules.bgs.submodules.base import BGSSubmodule
from Triumvirate.modules.legacy import URL_GOOGLE


class VoucherTracker(Module, BGSSubmodule):
    @property
    def localized_name(self) -> str:
        return _translate("Voucher tracker")

    def __init__(self):
        self.station_owner: str | None = None
        self.system_factions: list[str] = list()  # we don't care about redeems for foreign factions, they won't affect local bgs
        self.redeemed_factions: list[str] = list()  # there's a game bug that would duplicate faction entries in certain conditions

    def on_journal_entry(self, entry: JournalEntry):
        if GameState.gamemode != 'MainGame':
            return

        raw = entry.data
        event = raw["event"]
        if event in ("Location", "FSDJump", "CarrierJump"):
            self.system_factions = [fct.get("Name", "") for fct in raw.get("Factions", [])]
            PluginContext.logger.debug(f"Factions in system: {self.system_factions}")
            return
        elif event == "Docked" or (event == "Location" and raw["Docked"] is True):
            self.station_owner = raw["StationFaction"]["Name"]
            self.redeemed_factions.clear()
            return
        elif event == "Undocked" or (event == "Location" and raw["Docked"] is False):
            self.station_owner = None
            self.redeemed_factions.clear()
            return
        elif event != "RedeemVoucher":
            return

        # игнорируем флитаки и юристов
        if self.station_owner == "FleetCarrier" or "BrokerPercentage" in raw:
            PluginContext.logger.debug("Ignoring RedeemVoucher event - FC or Interstellar Factors")
            return

        url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse'
        voucher_type = raw["Type"]
        cmdr = GameState.cmdr
        system = GameState.system

        if voucher_type == "CombatBond":
            faction_name = raw["Faction"]
            amount = raw["Amount"]
            if faction_name not in self.system_factions:
                PluginContext.logger.debug(f"Ignoring bonds for faction {faction_name} - not present in the system")
                return
            PluginContext.logger.debug(f"Redeeming combat bonds: faction {faction_name}, amount: {amount} cr.")
            params = {
                "entry.503143076": cmdr,
                "entry.1108939645": voucher_type,
                "entry.127349896": system,
                "entry.442800983": "",
                "entry.48514656": faction_name,
                "entry.351553038": amount,
                "usp": "pp_url",
            }
            self.send_bgs_report(url, params, system)  # pyright: ignore[reportArgumentType]

        elif voucher_type == "bounty":
            PluginContext.logger.debug("Redeeming bounties:")
            for faction in raw["Factions"]:
                faction_name: str = faction["Faction"]
                amount: int = faction["Amount"]
                if faction_name != "" and faction_name not in self.redeemed_factions:
                    if faction_name not in self.system_factions:
                        PluginContext.logger.debug(f"Ignoring faction {faction_name} - not present in the system")
                        continue
                    PluginContext.logger.debug(f"Faction {faction_name}, amount: {amount} cr.")
                    params = {
                        "entry.503143076": cmdr,
                        "entry.1108939645": voucher_type,
                        "entry.127349896": system,
                        "entry.442800983": "",
                        "entry.48514656": faction_name,
                        "entry.351553038": amount,
                        "usp": "pp_url",
                    }
                    self.redeemed_factions.append(faction_name)
                    self.send_bgs_report(url, params, system)  # pyright: ignore[reportArgumentType]
