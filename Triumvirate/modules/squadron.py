from Triumvirate.core.context import GameState
from Triumvirate.core.plugin_config import plugin_config
from Triumvirate.core.shortcuts import _translate, debug
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module
from Triumvirate.modules import legacy


class SquadronTracker(Module):
    SQUADRON_KEY = "SquadronTracker.SavedSquadron"

    @property
    def localized_name(self) -> str:
        return _translate("Squadron tracker")

    def __init__(self):
        self.saved_squadron = plugin_config.get_str(self.SQUADRON_KEY) or None
        debug(f"Saved squadron: {self.saved_squadron}")
        # При запуске плагина сквадрон определяется данными из нашей таблички,
        # поэтому здесь контекст не редактируем.


    def on_journal_entry(self, entry: JournalEntry):
        match entry.data["event"]:
            case "SquadronStartup": self.startup_squadron(entry)
            case "JoinedSquadron" | "SquadronCreated": self.joined_squadron(entry)
            case "KickedFromSquadron" | "LeftSquadron" | "DisbandedSquadron": self.left_squadron(entry)


    def startup_squadron(self, journal_entry: JournalEntry):
        squadron = journal_entry.data["SquadronName"].upper()
        GameState.squadron = squadron
        if squadron != self.saved_squadron:
            debug("Saved squadron doesn't match the in-game data.")
            plugin_config.set(self.SQUADRON_KEY, squadron)
            self.saved_squadron = squadron
            debug(f"New saved squadron: {self.saved_squadron}. Reporting.")
            self.report_sq()


    def joined_squadron(self, journal_entry: JournalEntry):
        squadron = journal_entry.data["SquadronName"].upper()
        GameState.squadron = squadron
        plugin_config.set(self.SQUADRON_KEY, squadron)
        self.saved_squadron = squadron
        debug(f"Joined the squadron {self.saved_squadron}. Reporting.")
        self.report_sq()


    def left_squadron(self, journal_entry: JournalEntry):
        GameState.squadron = None
        GameState.legacy_sqid = None
        plugin_config.set(self.SQUADRON_KEY, "")
        self.saved_squadron = None
        debug("Left the squadron. Reporting.")
        self.report_sq()


    def report_sq(self):
        # TODO: вернуть после тестов на реальную форму
        # url = "https://docs.google.com/forms/d/e/1FAIpQLScZvs3MB2AK6pPwFoSCpdaarfAeu_P-ineIhtO1mOPgr09q8A/formResponse?usp=pp_url"
        # params = {
        #     "entry.558317192":  GameState.cmdr,
        #     "entry.1042067605": GameState.squadron
        # }
        url = "https://docs.google.com/forms/d/e/1FAIpQLSfFxDAvHttNmVFwk56PvrNNVouQYmgE4rd-vqO_3yR2CdkFIA/formResponse?usp=pp_url"
        params = {
            "entry.1289608233": GameState.cmdr,
            "entry.1616589915": GameState.squadron or "[independent]"
        }
        legacy.GoogleReporter(url, params).start()
