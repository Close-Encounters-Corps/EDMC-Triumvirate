import requests

import settings
from modules.debug import debug
from modules.lib.cache import Cache


class SystemsModule:
    def __init__(self):
        self.name_to_coords_cache = Cache(max_size=1024, name="COORDS_CACHE")
        self.name_to_coords_cache.start()
        self.id_to_name_cache = Cache(max_size=1024, name="ID CACHE")
        self.id_to_name_cache.start()

    def add_system(self, entry: dict):
        sysid = entry["SystemAddress"]
        system = entry["StarSystem"]
        coords = entry["StarPos"]
        self.id_to_name_cache[sysid] = system
        self.name_to_coords_cache[system] = coords

    def get_system_coords(self, system: str):
        try:
            return self.name_to_coords_cache[system]
        except KeyError:
            coords = self.fetch_system_coords(system)
            if coords is not None:
                self.name_to_coords_cache[system] = coords
            return coords

    def get_system_name(self, sysid: int):
        try:
            return self.id_to_name_cache[sysid]
        except KeyError:
            res: tuple[str, tuple[float, float, float]] | None = self.fetch_system_data_from_id(sysid)
            if res is not None:
                name, coords = res
                self.id_to_name_cache[sysid] = name
                self.name_to_coords_cache[name] = coords
                return name
            return None


    def fetch_system_coords(self, system: str) -> tuple[float, float, float] | None:
        try:
            resp = requests.get(
                url=f"{settings.galaxy_url}/api/v1/lookup",
                params={"name": system},
                timeout=5,
            )
            resp.raise_for_status()
            json = resp.json() or dict()
            x, y, z = json.get("x"), json.get("y"), json.get("z")
            if None not in (x, y, z):
                debug(f"Got coordinates for {system} from CEC API: {x}, {y}, {z}")
                return x, y, z  # type: ignore
            else:
                debug(f"CEC API doesn't contain valid coordinates for {system}, attempting Spansh")
        except Exception as e:
            debug(f"Failed to retrieve coordinates from CEC API, attempting Spansh: {e}.")

        try:
            resp = requests.get(
                url="https://www.spansh.co.uk/api/search",
                params={"q": system},
                timeout=5,
            )
            resp.raise_for_status()
            record = next(
                (
                    s["record"] for s in resp.json()["results"]
                    if s["type"] == "system"
                    and s["record"]["name"] == system
                ),
                None
            )
            if record is None:
                debug(f"Spansh doesn't contain a record for {system}")
                return None
            else:
                x, y, z = record["x"], record["y"], record["z"]
                debug(f"Got coordinates for {system} from Spansh: {x}, {y}, {z}")
                return x, y, z
        except Exception as e:
            debug(f"Failed to retrieve coordinates from Spansh: {e}")
            return None


    def fetch_system_data_from_id(self, sysid: int):
        try:
            resp = requests.get(
                url="https://www.spansh.co.uk/api/system/{sysid}",
                timeout=5,
            )
            resp.raise_for_status()
            record = resp.json()["record"]
            name = record["name"]
            x, y, z = record["x"], record["y"], record["z"]
            debug(f"Got data for system ID {sysid} from Spansh: name - {name}, coords - {x}, {y}, {z}")
            return name, (x, y, z)
        except Exception as e:
            debug(f"Failed to retrieve coordinates from Spansh: {e}")
            return None
