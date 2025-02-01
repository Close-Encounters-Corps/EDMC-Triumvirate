import requests, traceback, json
from datetime import datetime, timedelta

from context import PluginContext, GameState
from settings import canonn_cloud_url_us_central, canonn_cloud_url_europe_west
from modules.debug import info, debug, error
from modules.lib.module import Module
from modules.lib.journal import JournalEntry
from modules.lib.thread import Thread, BasicThread
from modules.lib.timer import Timer


class CanonnReporter(BasicThread):
    """Смесь Reporter и Canonn-овского Emitter"""
    # https://github.com/canonn-science/EDMC-Canonn/blob/05a5d9c4f842ad4fdb52b1a04ffc01ac623eba2b/canonn/emitter.py

    def __init__(self, url: str, payload: dict):
        super().__init__()
        self.url = url
        self.payload = payload

    def run(self):
        try:
            res = requests.post(
                self.url,
                data=json.dumps(self.payload, ensure_ascii=False).encode('utf-8'),
                headers={"content-type": "application/json"}
            )
            res.raise_for_status()
        except requests.RequestException as e:
            PluginContext.logger.error(
                "[CanonnReporter] Couldn't send data to Canonn Cloud. Url: {}, payload: {}.".format(self.url, self.payload),
                exc_info=e
            )
        else:
            debug("[CanonnReporter] Data sent successfully: url {!r}, payload {!r}.", self.url, self.payload)


class HDDetector:
    """Отслеживает гиперперехваты таргоидами."""

    _instance = None
    def __new__(cls):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # возможные состояния
    SAFE     = 1
    MISJUMP  = 2
    THARGOID = 3
    HOSTILE  = 4
    
    def __init__(self):
        self.departure_system: str          = None
        self.destination_system: str        = None
        self.departure_timestamp: datetime  = None
        self.status = self.SAFE
        self._timer: Timer | None = None
        

    def journal_entry(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        event = entry["event"]

        if event == "StartJump" and entry["JumpType"] == "Hyperspace":
            self.departure_system = journalEntry.system
            self.destination_system = entry["StarSystem"]
            self.departure_timestamp = datetime.fromisoformat(entry["timestamp"])
        
        elif event == "FSDJump":
            arrived_to = entry["StarSystem"]
            if self.departure_system == arrived_to:
                # 99%, что проделки таргов, но на всякий случай перепроверим
                debug("[HDDetector] Detected a misjump.")
                self.status = self.MISJUMP
            else:
                self.status = self.SAFE

        elif (
            event == "Music"
            and self.status in (self.MISJUMP, self.THARGOID)
            and entry.get("MusicTrack") in ("Unknown_Encounter", "Combat_Unknown", "Combat_Dogfight", "Combat_Hunters")
        ):
            if self.status < self.THARGOID:
                debug("[HDDetector] Hyperdiction confirmed.")
            self.status = self.THARGOID

            if entry["MusicTrack"] in ("Unknown_Encounter"):
                # подождём, ожидая агрессии со стороны таргоида
                debug("[HDDetector] Waiting for the signs of aggression...")
                if not self._timer:
                    self._timer = Timer(20, lambda:self._reportHD(journalEntry))
                    self._timer.start()
            
            elif entry["MusicTrack"] in ("Combat_Unknown", "Combat_Dogfight", "Combat_Hunters"):
                debug("[HDDetector] Detected an attack on a player.")
                self.status = self.HOSTILE
                if self._timer:
                    self._timer.kill()
                    self._timer = None
                self._reportHD(journalEntry)
    

    def _reportHD(self, journalEntry: JournalEntry):
        if not self.status == self.HOSTILE:
            debug("[HDDetector] Aggression against the player not detected.")
        debug("[HDDetector] Reporting the hyperdiction to Canonn.")
        
        x, y, z    = journalEntry.coords
        dx, dy, dz = PluginContext.systems_module.get_system_coords(self.destination_system)
        
        url = f"{canonn_cloud_url_europe_west}/postHDDetected"
        params = {
            "cmdr": journalEntry.cmdr,
            "system": journalEntry.system,
            "timestamp": journalEntry.data["timestamp"],
            "x": x, "y": y, "z": z,
            "destination": self.destination_system,
            "dx": dx, "dy": dy, "dz": dz,
            "client": PluginContext.client_version,
            "odyssey": GameState.odyssey,
            "hostile": self.status == self.HOSTILE
        }
        CanonnReporter(url, params).start()

        # сбрасываем состояние до следующего перехвата
        self.status = self.SAFE
    

    @classmethod
    def check_last_encounter(cls, journalEntry: JournalEntry):
        entry = journalEntry.data
        if entry.get("TG_ENCOUNTERS", {}).get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):
            debug("[HDDetector] Detected {!r} event, sending the last thargoid encounter to Canonn.", entry["event"])
            system = entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
            if system == "Pleiades Sector IR-W d1-55":
                system = "Delphi"
            x, y, z = PluginContext.systems_module.get_system_coords(system)
            
            gametime = entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP")
            year, remainder = gametime.split("-", 1)
            timestamp = "{}-{}".format(str(int(year) - 1286), remainder)
            
            debug("[HDDetector] Last encounter: timestamp {!r}, system {!r}.", timestamp, system)

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
    _instance = None
    _hdtracker = HDDetector()
    whitelist = dict()

    def __init__(self):
        super().__init__()
        self.fss_signals_batch = list()
        self._batch_maxlen = 30         # каноны рекомендуют 40 во избежание таймаута, мы перестрахуемся
        self.fss_signals_timer: Timer | None = None
        WhitelistUpdater().start()


    def on_journal_entry(self, journalEntry: JournalEntry):
        if journalEntry.data["event"] == "Statistics":
            self._hdtracker.check_last_encounter(journalEntry)

        if not journalEntry.system:     # потому что некоторые ивенты, например, FSSSignalDiscovered, при старте игры идут до Location
            return                      # и EDMC в этот момент отдаёт system=None
        
        # проверяем:
        # сигналы в системе
        self._check_fss_signal(journalEntry)
        # таргоидские гиперперехваты
        self._hdtracker.journal_entry(journalEntry)
        # всё остальное
        if journalEntry.data["event"] != "FSSSignalDiscovered":
            self._check_whitelisted_events(journalEntry)
    

    def on_close(self):
        if len(self.fss_signals_batch) > 0:
            self._dump_batch()

    
    def _check_fss_signal(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        event = entry["event"]

        if event == "FSSSignalDiscovered":
            isStation = entry.get("IsStation", False)
            isCecFc = (
                entry.get("SignalType") == "FleetCarrier"
                and is_cec_fleetcarrier(entry.get("SignalName", ""))
            )
            if isStation and not isCecFc:
                self.fss_signals_batch.append(journalEntry)

        """
        Отправлять FSS сигналы в системе будем при одном из следующих условий:
        0) Очередь заполнена
        1) Мы покинули систему
        2) Мы вышли из игры
        3) Мы закрываем плагин      <-- реализовано в on_close()
        4) Прошло достаточно времени
        """
        first_timestamp = datetime.fromisoformat(self.fss_signals_batch[0].data["timestamp"]  if len(self.fss_signals_batch) > 0  else entry["timestamp"])
        last_timestamp  = datetime.fromisoformat(entry["timestamp"])
        timestamp_diff: timedelta = last_timestamp - first_timestamp
        if (
            len(self.fss_signals_batch) == self._batch_maxlen                               # 0
            or (event == "StartJump" and entry["JumpType"] == "Hyperspace")                 # 1
            or event in ["Died", "SelfDestruct", "Resurrect"]                               # 1
            or event == "Shutdown"                                                          # 2
            or event == "Music" and entry["MusicTrack"] == "MainMenu"                       # 2
            or (event != "FSSSignalDiscovered" and timestamp_diff > timedelta(minutes=1))   # 4
        ):
            self._dump_batch()


    def _check_whitelisted_events(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        valuable = False
        for accepted_event in self.whitelist:
            if all(entry.get(key) == value for key, value in accepted_event["definition"].items()):
                valuable = True
                break
        if not valuable:
            return
        # если все пары ключей-значений совпадают, каноны в этом заинтересованы
        debug("[CanonnAPI] Sending the {!r} event to Canonn.", entry["event"])
        url = f"{canonn_cloud_url_us_central}/postEvent"
        gamestate = self._get_gamestate(journalEntry)
        params = {
            "gameState": gamestate,
            "rawEvents": [entry],
            "cmdrName":  journalEntry.cmdr
        }
        CanonnReporter(url, params).start()

    
    def _dump_batch(self):
        if len(self.fss_signals_batch) == 0:
            return
        debug("[CanonnAPI] Dumping the batch, len={}.", len(self.fss_signals_batch))
        url = f"{canonn_cloud_url_us_central}/postEvent"
        gamestate = self._get_gamestate(self.fss_signals_batch[0])
        params = {
            "gameState": gamestate,
            "rawEvents": [entry.data for entry in self.fss_signals_batch],
            "cmdrName":  self.fss_signals_batch[0].cmdr
        }
        CanonnReporter(url, params.copy()).start()
        self.fss_signals_batch.clear()
    
    
    def _get_gamestate(self, journalEntry: JournalEntry):
        entry = journalEntry.data

        # обязательные параметры
        gamestate = {
            "systemName":       journalEntry.system,
            "systemAddress":    journalEntry.systemAddress,
            "systemCoordinates": [
                journalEntry.coords.x,
                journalEntry.coords.y,
                journalEntry.coords.z
            ],
            "clientVersion":    PluginContext.client_version,
            "isBeta":           journalEntry.is_beta
        }

        # дополнительные, которые мы 100% знаем
        gamestate["platform"] = "PC"

        # дополнительные, которые мы, возможно, знаем
        if GameState.odyssey is not None:   gamestate["odyssey"] = GameState.odyssey
        if entry.get("BodyID"):             gamestate["bodyId"] = entry["BodyID"]
        if GameState.body_name:             gamestate["bodyName"] = GameState.body_name
        if GameState.temperature:           gamestate["temperature"] = GameState.temperature
        if GameState.gravity:               gamestate["gravity"] = GameState.gravity

        if GameState.latitude and GameState.longitude:
            gamestate["latitude"] = GameState.latitude
            gamestate["longitude"] = GameState.longitude

        return gamestate



class WhitelistUpdater(Thread):
    def __init__(self):
        super().__init__(name="Canonn whitelist updater")
    def do_run(self):
        url = "https://api.github.com/gists/5b993467bf6be84b392418ddc9fcb6d3"
        attempts = 0
        while True:
            attempts += 1
            try: response = requests.get(url)
            except:
                error(traceback.format_exc())
                return
            
            if response.status_code == 200:
                info("[CanonnRealtimeAPI]: Got list of events to track.")
                CanonnRealtimeAPI.whitelist = json.loads(response.json()["files"]["canonn_whitelist.json"]["content"])
                return
            else:
                error("[CanonnRealtimeAPI] Couldn't get list of systems to track, response code {} ({} attempts)", response.status_code, attempts)
                self.sleep(10)



def is_cec_fleetcarrier(signalName: str) -> bool:
    name = signalName.strip().upper().replace('С', 'C').replace('Е', 'E')
    return name[0:4] == "CEC "