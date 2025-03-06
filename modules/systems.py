import settings
from .lib.cache import Cache
from .lib.http import WebClient
from .debug import debug


class SystemsModule(WebClient):
    def __init__(self):
        super().__init__(settings.galaxy_url)
        self.cache = Cache(max_size=1024, name="SYSTEMS_CACHE")
        self.cache.start()

    def add_system(self, entry: dict):
        system = entry["StarSystem"]
        coords = entry["StarPos"]
        self.cache[system] = coords

    def get_system_coords(self, system):
        try:
            return self.cache[system]
        except KeyError:
            coords = self.fetch_system(system)
            if coords:
                self.cache[system] = coords
                return self.cache[system]

    def fetch_system(self, system):
        try:
            resp = self.request("GET", "/api/v1/lookup", {"name": system})
        except Exception as e:
            debug(f"fetch_systems failed: {e}")
        else:
            if resp.status_code == 200:
                coords = resp.json()
                return coords["x"], coords["y"], coords["z"]
            else:
                debug(f"fetch_system failed with code {resp.status_code}")
                return None
