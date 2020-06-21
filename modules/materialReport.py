# -*- coding: utf-8 -*-
import threading
import requests
from urllib.parse import quote_plus
import sys
import json
from .lib.module import Module
from .emitter import Emitter
from .debug import debug
from .lib.thread import Thread
from .lib.canonn_api import CanonnApi


class MaterialsCollectedSender(Thread):
    def __init__(self, entry):
        super().__init__()
        self.entry = entry

    def run(self):
        c_api = CanonnApi(self.entry.is_beta)
        c_api.submit_materialscollected(self.entry)

class MaterialsRewardSender(Thread):
    def __init__(self, entry):
        super().__init__()
        self.entry = entry

    def run(self):
        c_api = CanonnApi(self.entry.is_beta)
        c_api.submit_materialreward(self.entry)
        


class MaterialsModule(Module):
    def on_journal_entry(self, entry):
        if entry.data["event"] == "MaterialCollected":
            MaterialsCollectedSender(entry).start()
        if "MaterialsReward" in entry.data:
            MaterialsRewardSender(entry).start()
