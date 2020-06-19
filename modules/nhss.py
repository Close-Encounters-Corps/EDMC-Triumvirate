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

class NHSSSubmitter(Thread):
    def __init__(self, entry, threat_level):
        super().__init__()
        self.entry = entry
        self.cmdr = entry.cmdr
        self.system = entry.system
        self.x = entry.coords.x
        self.y = entry.coords.y
        self.z = entry.coords.z
        self.threat_level = threat_level

    def run(self):
        client = WebClient()
        client.get(
            settings.nhss_canonn_url,
            params=dict(
                cmdrName=self.cmdr,
                systemName=self.system,
                x=self.x,
                y=self.y,
                z=self.z,
                thread_level=self.threat_level,
            ),
        )
        endpoint = get_endpoint()
        if self.entry.data["event"] == "FSSSignalDiscovered":
            event_type = "FSS"
        else:
            event_type = "Drop"
        payload = dict(
            systemName=self.system,
            cmdrName=self.cmdr,
            nhssRawJson=self.entry.data,
            threatLevel=self.threat_level,
            isBeta=self.entry.is_beta,
            clientVersion=self.entry.client,
            reportStatus="accepted",
            reportComment=event_type
        )
        client.post(endpoint, json=payload)


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
