import settings
from .lib.module import Module
from .lib.cache import Cache
from .lib.http import WebClient
from .debug import Debug

class SystemsModule(WebClient, Module):
    def __init__(self):
        super().__init__(settings.galaxy_url)
        self.cache = Cache(max_size=1024)
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
        resp = self.get("/api/v1/lookup", params={"name": system})
        if resp.status_code == 200:
            data = resp.json()
            return data["x"], data["y"], data["z"]
        if resp.status_code != 400:
            Debug.p(f"fetch_system failed with code {resp.status_code}")
        return None
