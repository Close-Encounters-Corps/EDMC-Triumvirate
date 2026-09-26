import requests
import sqlite3
from dataclasses import dataclass

from Triumvirate.core.context import PluginContext
from Triumvirate.lib.journal import Coords


@dataclass
class _SystemData:
    sid: int
    name: str
    coords: Coords


class SystemsCache:
    def __init__(self):
        self._cache = sqlite3.connect(PluginContext.paths.userdata_dir / "cache.db", check_same_thread=False)
        self._cache.execute("CREATE TABLE IF NOT EXISTS systems (id INTEGER PRIMARY KEY, name TEXT, x REAL, y REAL, z REAL)")
        self._cache.execute("CREATE INDEX IF NOT EXISTS idx_systems_name ON systems(name)")
        self._cache.commit()

    def on_close(self):
        self._cache.close()


    def cache_system(self, entry: dict):
        sid = entry["SystemAddress"]
        name = entry["StarSystem"]
        coords = Coords(*entry["StarPos"])
        self._db_add_system(_SystemData(sid, name, coords))

    def get_system_coords(self, system: str | int) -> Coords | None:
        data = self._get_system_by_id(system) if isinstance(system, int) else self._get_system_by_name(system)
        return data.coords if data else None

    def get_system_name(self, system_id: int) -> str | None:
        data = self._get_system_by_id(system_id)
        return data.name if data else None

    def get_system_id(self, system_name: str) -> int | None:
        data = self._get_system_by_name(system_name)
        return data.sid if data else None


    def _db_add_system(self, data: _SystemData):
        cur = self._cache.execute(
            "INSERT OR IGNORE INTO systems VALUES (?,?,?,?,?)",
            (data.sid, data.name, data.coords.x, data.coords.y, data.coords.z)
        )
        self._cache.commit()
        if cur.rowcount == 1:
            PluginContext.logger.debug(f"New cached system: {data.name} (id {data.sid}), coords: {data.coords}.")


    def _get_system_by_id(self, sid: int) -> _SystemData | None:
        cur = self._cache.execute("SELECT * FROM systems WHERE id = ?", (sid,))
        res = cur.fetchone()
        if res is not None:
            name = res[1]
            coords = Coords(res[2], res[3], res[4])
            return _SystemData(sid, name, coords)

        PluginContext.logger.debug(f"No cached data for sid {sid}, attempting remote fetching.")
        system_data = self._fetch_system_by_id(sid)
        if system_data:
            self._db_add_system(system_data)
        else:
            PluginContext.logger.debug(f"Couldn't fetch system data for sid {sid}.")
        return system_data


    def _get_system_by_name(self, name: str) -> _SystemData | None:
        cur = self._cache.execute("SELECT * FROM systems WHERE name = ?", (name,))
        res = cur.fetchall()
        if len(res) == 1:
            sid = res[0][0]
            coords = Coords(res[0][2], res[0][3], res[0][4])
            return _SystemData(sid, name, coords)
        if len(res) > 1:
            PluginContext.logger.debug(
                f"System name {name} is ambigious: ({len(res)} matches). Unable to determine the desired one, system ID is required."
            )
            return None

        PluginContext.logger.debug(f"No cached data for system {name}, attempting remote fetching.")
        data = self._fetch_system_by_name(name)
        if data is None:
            PluginContext.logger.debug(f"Couldn't fetch system data for {name}.")
            return None
        if isinstance(data, _SystemData):
            self._db_add_system(data)
            return data

        # data: list[_SystemData]
        for system_data in data:
            self._db_add_system(system_data)
        PluginContext.logger.debug(
            f"System name {name} is ambigious: ({len(res)} matches). Unable to determine the desired one, system ID is required."
        )
        return None


    def _fetch_system_by_id(self, system_id: int) -> _SystemData | None:
        url = f"https://spansh.co.uk/api/system/{system_id}"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except requests.RequestException as e:
            PluginContext.logger.error(f"Couldn't fetch system data for sid {system_id} from Spansh:", exc_info=e)
            return None

        data: dict | None = resp.json().get("record")
        if data is None:
            PluginContext.logger.warning(f"Spansh data for sid {system_id} doesn't contain the `record` field.")
            return None

        name = data.get("name")
        x, y, z = data.get("x"), data.get("y"), data.get("z")
        if None in (name, x, y, z):
            PluginContext.logger.warning(
                f"Spansh data for sid {system_id} is inconsistent. "
                f"Reported name: {name}, reported coords: [{x}, {y}, {z}]."
            )
            return None
        return _SystemData(system_id, name, Coords(x, y, z))  # pyright: ignore[reportArgumentType]


    def _fetch_system_by_name(self, system_name: str) -> _SystemData | list[_SystemData] | None:
        url = "https://spansh.co.uk/api/search"
        params = {"q": system_name}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
        except requests.RequestException as e:
            PluginContext.logger.error(f"Couldn't fetch system data for {system_name} from Spansh:", exc_info=e)
            return None

        results: list[dict] = resp.json().get("results", [])
        systems = []
        for result in results:
            record: dict | None = result.get("record")
            if record is None:
                continue
            if result.get("type") == "system" and record.get("name") == system_name:
                sid = record.get("id64")
                x, y, z = record.get("x"), record.get("y"), record.get("z")
                if None in (sid, x, y, z):
                    PluginContext.logger.warning(
                        f"Spansh data for system {system_name} is inconsistent. "
                        f"Reported sid: {sid}, reported coords: [{x}, {y}, {z}]."
                    )
                    continue
                systems.append(_SystemData(sid, system_name, Coords(x, y, z)))

        match len(systems):
            case 0:
                PluginContext.logger.debug(f"No results found for system name {system_name} on Spansh.")
                return None
            case 1:
                return systems[0]
            case _:
                PluginContext.logger.debug(f"Multiple results ({len(systems)}) found for system name {system_name} on Spansh.")
                return systems
