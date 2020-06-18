import glob
import json
import os
from urllib.parse import quote_plus

import requests

import settings
from modules.debug import Debug, debug, error
from .lib.module import Module
from .lib.cache import Cache
from .lib.http import WebClient


class SystemsModule(Module):
    def __init__(self):
        self.cache = Cache(max_size=1024, static=settings.systems_static_coords)
        self.cache.start()

    def on_journal_entry(self, entry):
        if entry.data.get("event") != "FSDJump":
            return
        self.cache[entry.system] = entry.data["StarPos"]

    def get_system_coords(self, system):
        try:
            return self.cache[system]
        except KeyError:
            coords = self.fetch_system(system)
            if coords:
                self.cache[system] = coords
                return self.cache[system]

    def fetch_system(self, system):
        client = WebClient()
        data = client.get(
            settings.edsm_system_url,
            params={"systemName": system, "showCoordinates": "1"}
        ).json()
        if data:
            coords = data["coords"]
            return coords["x"], coords["y"], coords["z"]
