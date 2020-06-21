"""
Модуль, отвечающий за отправку данных
о Non-Human Signal Source'ах в Canonn API.
"""

import json
import sys
from urllib.parse import quote_plus

import requests

import settings

from .debug import debug, error
from .emitter import get_endpoint
from .lib.module import Module
from .lib.thread import Thread
from .lib.http import WebClient
from .lib.canonn_api import CanonnApi, CanonnRealtimeApi

class NHSSSubmitter(Thread):
    def __init__(self, entry, threat_level):
        super().__init__()
        self.entry = entry
        self.threat_level = threat_level

    def run(self):
        CanonnRealtimeApi().submit_nhss(self.entry, self.threat_level)
        CanonnApi(self.entry.is_beta).submit_nhss(self.entry, self.threat_level)


"""
    { 
        "timestamp":"2018-10-07T13:03:02Z", 
        "event":"USSDrop", 
        "USSType":"$USS_Type_NonHuman;", 
        "USSType_Localised":"Non-Human signal source", 
        "USSThreat":4 
    }
"""


class NHSSModule(Module):

    def __init__(self):
        self.fss = {}

    def on_journal_entry(self, entry):
        if not (
            entry.data["event"] in ("USSDrop", "FSSSignalDiscovered")
            and entry.data.get("USSType") == "$USS_Type_NonHuman;"
        ):
            return
        threat_level = (
            entry.data.get("ThreatLevel")
            if entry.data["event"] == "FSSSignalDiscovered"
            else entry.data.get("USSThreat")
        )
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
