import json
import requests
from datetime import datetime, timedelta

from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.settings import canonn_cloud_url_europe_west, canonn_cloud_url_us_central
from Triumvirate.core.shortcuts import _translate, debug, error, info, warning
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module
from Triumvirate.lib.thread import BasicThread, Thread
from Triumvirate.lib.timer import Timer


class CanonnReporter(BasicThread):
    """Смесь Reporter и Canonn-овского Emitter"""
    # https://github.com/canonn-science/EDMC-Canonn/blob/05a5d9c4f842ad4fdb52b1a04ffc01ac623eba2b/canonn/emitter.py

    def __init__(self, url: str, payload: dict):
        super().__init__()
        self.url = url
        self.payload = payload

    def run(self):
        if None in self.payload.values():
            error(f"None detected in params! {self.payload}")
            return
        try:
            res = requests.post(
                self.url,
                data=json.dumps(self.payload, ensure_ascii=False).encode('utf-8'),
                headers={"content-type": "application/json"},
                timeout=5,
            )
            res.raise_for_status()
        except requests.RequestException as e:
            error(f"Couldn't send data to Canonn Cloud. Url: {self.url}, payload: {self.payload} Exception info:", exc_info=e)
        else:
            debug(f"Data sent successfully: url {self.url!r}, payload {self.payload!r}.")


class HDDetector:
    """Отслеживает гиперперехваты таргоидами."""

    # возможные состояния
    SAFE = 1
    MISJUMP = 2
    THARGOID = 3
    HOSTILE = 4

    def __init__(self):
        self.departure_system: str | None = None
        self.destination_system_id: int | None = None
        self.departure_timestamp: datetime | None = None
        self.status = self.SAFE
        self._timer: Timer | None = None


    def journal_entry(self, journal_entry: JournalEntry):
        if GameState.gamemode != 'MainGame':
            return

        entry = journal_entry.data
        event = entry["event"]

        if event == "StartJump" and entry["JumpType"] == "Hyperspace":
            self.departure_system = journal_entry.system
            self.destination_system_id = entry["SystemAddress"]
            self.departure_timestamp = datetime.fromisoformat(entry["timestamp"])

        elif event == "FSDJump":
            arrived_to = entry["StarSystem"]
            if self.departure_system == arrived_to:
                # 99%, что проделки таргов, но на всякий случай перепроверим
                debug(f"Detected a misjump: departure and arrival systems are the same ({arrived_to}).")
                self.status = self.MISJUMP
            else:
                self.status = self.SAFE

        elif (
            event == "Music"
            and self.status in (self.MISJUMP, self.THARGOID)
            and entry.get("MusicTrack") in ("Unknown_Encounter", "Combat_Unknown", "Combat_Dogfight", "Combat_Hunters")
        ):
            if self.status < self.THARGOID:
                debug(f"Hyperdiction confirmed: music track {entry['MusicTrack']!r}")
            self.status = self.THARGOID

            if entry["MusicTrack"] in ("Unknown_Encounter"):
                # подождём, ожидая агрессии со стороны таргоида
                debug("Waiting for the signs of aggression...")
                if not self._timer:
                    self._timer = Timer(20, lambda: self._reportHD(journal_entry))
                    self._timer.start()

            elif entry["MusicTrack"] in ("Combat_Unknown", "Combat_Dogfight", "Combat_Hunters"):
                debug(f"Detected an attack on the player: music track {entry['MusicTrack']!r}")
                self.status = self.HOSTILE
                if self._timer:
                    self._timer.kill()
                    self._timer = None
                self._reportHD(journal_entry)


    def _reportHD(self, journal_entry: JournalEntry):
        if self.status != self.HOSTILE:
            debug("Aggression against the player not detected.")
        debug("Reporting the hyperdiction to Canonn.")

        if self.destination_system_id is None:
            error("Detected hyperdiction, but destination_system_id was None!")
            self.status = self.SAFE
            return

        current_coords = GameState.system_coords
        dest_coords = PluginContext.systems_cache.get_system_coords(self.destination_system_id)
        dest_name = PluginContext.systems_cache.get_system_name(self.destination_system_id)

        if current_coords is None:
            warning("Unable to send hyperdiction report: no current coords.")
        elif dest_coords is None or dest_name is None:
            warning("Unable to send hyperdiction report: no target coords or name.")
        else:
            x, y, z = current_coords
            dx, dy, dz = dest_coords
            url = f"{canonn_cloud_url_europe_west}/postHDDetected"
            params = {
                "cmdr": GameState.cmdr,
                "system": GameState.system,
                "timestamp": journal_entry.data["timestamp"],
                "x": x, "y": y, "z": z,
                "destination": dest_name,
                "dx": dx, "dy": dy, "dz": dz,
                "client": PluginContext.user_agent,
                "odyssey": GameState.odyssey,
                "hostile": (self.status == self.HOSTILE)
            }
            CanonnReporter(url, params).start()

        # сбрасываем состояние до следующего перехвата
        self.status = self.SAFE


    @classmethod
    def check_last_encounter(cls, journalEntry: JournalEntry):
        entry = journalEntry.data
        if entry.get("TG_ENCOUNTERS", {}).get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):
            debug(f"Detected {entry['event']!r} event, sending the last thargoid encounter to Canonn.")
            system = entry.get("TG_ENCOUNTERS", {}).get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
            if system == "Pleiades Sector IR-W d1-55":
                system = "Delphi"

            coords = PluginContext.systems_cache.get_system_coords(system)
            if coords is None:
                warning(f"Can't report last encounter to Canonn: system coordinates unknown ({system!r})")
                return

            x, y, z = coords
            gametime = entry.get("TG_ENCOUNTERS", {}).get("TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP")
            year, remainder = gametime.split("-", 1)
            timestamp = "{}-{}".format(str(int(year) - 1286), remainder)

            debug(f"Last encounter: timestamp {timestamp!r}, system {system!r}.")

            url = f"{canonn_cloud_url_europe_west}/postHD"
            params = {
                "cmdr": journalEntry.cmdr,
                "system": system,
                "timestamp": timestamp,
                "x": x, "y": y, "z": z
            }
            CanonnReporter(url, params).start()



class CanonnRealtimeAPI(Module):
    """Проверяет и отправляет интересные для Canonn-ов игровые события."""
    whitelist = dict()

    @property
    def localized_name(self) -> str:
        return _translate("Canonn API client")

    def __init__(self):
        self.hdtracker = HDDetector()
        self.signals_batch = list()
        self.batch_max_len = 40
        self.current_sysid = GameState.system_address
        WhitelistUpdater().start()


    def on_journal_entry(self, entry: JournalEntry):
        if GameState.gamemode != 'MainGame':
            return

        event = entry.data["event"]
        if event == "Statistics":
            self.hdtracker.check_last_encounter(entry)

        if GameState.system_address != self.current_sysid:
            self._dump_batch()
            self.current_sysid = GameState.system_address
        if self.current_sysid is None:
            return

        self.hdtracker.journal_entry(entry)

        # custom handling of stations to filter out CEC carriers and batch the events
        # this rule is absent from our whitelist, so the generic check later won't affect it
        if event == "FSSSignalDiscovered":
            is_station = entry.data.get("IsStation", False)
            is_cec_fc = entry.data.get("SignalType") == "FleetCarrier" and is_cec_fleetcarrier(entry.data.get("SignalName", ""))
            if is_station and not is_cec_fc:
                self.signals_batch.append(entry)
        # same with body signals
        elif event == "FSSBodySignals":
            self.signals_batch.append(entry)
        else:
            self.check_whitelisted_events(entry)

        self.check_batch_status(entry)


    def on_close(self):
        if len(self.signals_batch) > 0:
            self._dump_batch()


    def check_batch_status(self, journal_entry: JournalEntry):
        """
        Отправлять FSS сигналы в системе будем при одном из следующих условий:
        1) Очередь заполнена
        2) Мы покинули систему      <-- реализовано в on_journal_entry()
        3) Мы вышли из игровой сессии
        4) Мы закрываем плагин      <-- реализовано в on_close()
        5) Прошло достаточно времени
        """
        if len(self.signals_batch) == 0:
            return
        entry = journal_entry.data
        event = entry["event"]
        first_timestamp = datetime.fromisoformat(self.signals_batch[0].data["timestamp"])
        last_timestamp = datetime.fromisoformat(entry["timestamp"])
        timestamp_diff = last_timestamp - first_timestamp
        if (
            len(self.signals_batch) == self.batch_max_len                   # 1
            or event in ("Shutdown", "Died", "SelfDestruct", "Resurrect")   # 3
            or event == "Music" and entry["MusicTrack"] == "MainMenu"       # 3
            or timestamp_diff > timedelta(minutes=1)                        # 5
        ):
            self._dump_batch()


    def check_whitelisted_events(self, journal_entry: JournalEntry):
        entry = journal_entry.data
        valuable = False
        for accepted_event in self.whitelist:
            if all(entry.get(key) == value for key, value in accepted_event["definition"].items()):
                valuable = True
                break
        if not valuable:
            return
        # если все пары ключей-значений совпадают, каноны в этом заинтересованы
        debug(f"Sending {entry['event']!r} event to Canonn.")
        url = f"{canonn_cloud_url_us_central}/postEvent"
        gamestate = self._get_gamestate(journal_entry)
        params = {
            "gameState": gamestate,
            "rawEvents": [entry],
            "cmdrName": journal_entry.cmdr
        }
        CanonnReporter(url, params).start()


    def _dump_batch(self):
        if len(self.signals_batch) == 0:
            return
        debug(f"Dumping the batch, len={len(self.signals_batch)}.")
        url = f"{canonn_cloud_url_us_central}/postEvent"
        gamestate = self._get_gamestate(self.signals_batch[0])
        if gamestate is None:
            warning("Dropping the batch due to incomplete gamestate.")
            self.signals_batch.clear()
            return
        params = {
            "gameState": gamestate,
            "rawEvents": [entry.data for entry in self.signals_batch],
            "cmdrName": self.signals_batch[0].cmdr
        }
        CanonnReporter(url, params.copy()).start()
        self.signals_batch.clear()


    def _get_gamestate(self, journal_entry: JournalEntry) -> dict | None:
        # обязательные параметры
        # null system_address фильтруется в on_journal_entry, поэтому можем смело допустить, что у нас он здесь есть
        system_address: int = journal_entry.systemAddress  # pyright: ignore[reportAssignmentType]
        system_name = PluginContext.systems_cache.get_system_name(system_address)
        system_coords = PluginContext.systems_cache.get_system_coords(system_address)
        if system_name is None or system_coords is None:
            error("Cannot form gamestate: system name or coords unknown.")
            return None
        gamestate = {
            "systemName": system_name,
            "systemAddress": system_address,
            "systemCoordinates": [system_coords.x, system_coords.y, system_coords.z],
            "clientVersion": PluginContext.user_agent,
            "isBeta": journal_entry.is_beta
        }

        # дополнительные, которые мы 100% знаем
        gamestate["platform"] = "PC"

        # дополнительные, которые мы, возможно, знаем
        if GameState.odyssey is not None:
            gamestate["odyssey"] = GameState.odyssey
        if (body_id := journal_entry.data.get("BodyID")) is not None:
            gamestate["bodyId"] = body_id
        if GameState.body_name:
            gamestate["bodyName"] = GameState.body_name
        if GameState.temperature:
            gamestate["temperature"] = GameState.temperature
        if GameState.gravity:
            gamestate["gravity"] = GameState.gravity

        if GameState.latitude and GameState.longitude:
            gamestate["latitude"] = GameState.latitude
            gamestate["longitude"] = GameState.longitude

        return gamestate


class WhitelistUpdater(Thread):
    STANDARD_RETRY_DELAY = 20
    LONG_RETRY_DELAY = 10 * 60

    def __init__(self):
        super().__init__(name="Canonn whitelist updater")

    def do_run(self):
        attempts = 0
        while True:
            attempts += 1
            debug(f"Trying to retrieve the list of tracked events, attempt {attempts}")
            url = "https://api.github.com/gists/5b993467bf6be84b392418ddc9fcb6d3"
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except requests.RequestException as e:
                error("Couldnt't get the list of tracked events from GitHub, exception info:", exc_info=e)
            else:
                info("Got the list of tracked events from GitHub.")
                CanonnRealtimeAPI.whitelist = json.loads(response.json()["files"]["canonn_whitelist.json"]["content"])
                return
            # вторая попытка аналогично из другого источника
            url = "https://gitlab.com/api/v4/snippets/4888707/raw"
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except requests.RequestException as e:
                error("Couldn't get the list of tracked events from GitLab either, expection info:", exc_info=e)
                self.sleep(self.STANDARD_RETRY_DELAY)
                continue
            else:
                info("Got the list of tracked events from GitLab.")
                CanonnRealtimeAPI.whitelist = json.loads(response.text)
                return


def is_cec_fleetcarrier(signalName: str) -> bool:
    name = signalName.strip().upper().replace('С', 'C').replace('Е', 'E')
    return name[0:4] == "CEC "
