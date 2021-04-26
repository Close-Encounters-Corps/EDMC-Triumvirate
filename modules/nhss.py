"""
Модуль, отвечающий за отправку данных
о Non-Human Signal Source'ах в API.
"""

import settings

from .debug import debug
from .lib.module import Module
from .lib.thread import Thread
from .lib.context import global_context

class NHSSSubmitter(Thread):
    def __init__(self, entry, threat_level):
        super().__init__()
        self.entry = entry
        self.threat_level = threat_level

    def run(self):
        global_context.cec_api.submit("/v1/journal/nhss", self.entry)

class NHSSModule(Module):

    def __init__(self):
        self.fss = {}

    def on_journal_entry(self, entry):
        if not (
            entry.data["event"] in ("USSDrop", "FSSSignalDiscovered")
            and entry.data.get("USSType") == "$USS_Type_NonHuman;"
        ):
            return
        global_fss = None
        try:
            global_fss = self.fss.get(entry.system)
            old_threat = global_fss.get(threat_level)
        except:
            old_threat = False

        if old_threat:
            debug("Threat level already recorded here ({})", threat_level)
        else:
            self.fss.setdefault(entry.system, {})[threat_level] = True
            NHSSSubmitter(entry, threat_level).start()
