import requests, traceback, json
from datetime import datetime

from settings import canonn_realtime_url
from modules.release import Release
from modules.legacy import Reporter
from modules.debug import info, debug, error
from modules.lib.context import global_context
from modules.lib.module import Module
from modules.lib.journal import JournalEntry
from modules.lib.thread import Thread
from modules.lib.timer import Timer


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
        

    def journal_entry(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        event = entry["event"]

        if event == "Statistics":
            self._check_last_encounter(journalEntry)

        elif event == "StartJump" and entry["JumpType"] == "Hyperspace":
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
                if not self._timer:
                    self._reportHD(journalEntry)
                # в противном случае репорт будет послан после истечения таймера
    

    def _reportHD(self, journalEntry: JournalEntry):
        if not self.status == self.HOSTILE:
            debug("[HDDetector] Aggression against the player not detected.")
        debug("[HDDetector] Reporting the hyperdiction to Canonn.")
        
        x, y, z    = journalEntry.coords
        dx, dy, dz = global_context.systems_module.get_system_coords(journalEntry.system)
        
        url = f"{canonn_realtime_url}/postHDDetected"
        params = {
            "cmdr": journalEntry.cmdr,
            "system": journalEntry.system,
            "timestamp": journalEntry.data["timestamp"],
            "x": x, "y": y, "z": z,
            "destination": self.destination_system,
            "dx": dx, "dy": dy, "dz": dz,
            "client": journalEntry.client,
            "odyssey": global_context.odyssey,
            "hostile": self.status == self.HOSTILE
        }
        Reporter(url, params).start()

        # сбрасываем состояние до следующего перехвата
        self.status = self.SAFE
    

    def _check_last_encounter(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        if (entry.get("TG_ENCOUNTERS")
            and entry["TG_ENCOUNTERS"].get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
        ):
            debug("[HDDetector] Detected {!r} event, sending the last thargoid encounter to Canonn.", entry["event"])
            system = entry["TG_ENCOUNTERS"]["TG_ENCOUNTER_TOTAL_LAST_SYSTEM"]
            x, y, z = global_context.systems_module.get_system_coords(system)
            timestamp: str = entry["TG_ENCOUNTERS"]["TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP"]
            game_year = timestamp[:4]
            timestamp = timestamp.replace(game_year, str(int(game_year)-1286))
            debug("[HDDetector] Last encounter: timestamp {!r}, system {!r}.", timestamp, system)

            url = f"{canonn_realtime_url}/postHD"
            params = {
                "cmdr": journalEntry.cmdr,
                "system": system,
                "timestamp": timestamp,
                "x": x, "y": y, "z": z
            }
            Reporter(url, params).start()




class CanonnRealtimeAPI(Module):
    """Проверяет, интересны"""
    _instance = None
    _hdtracker = HDDetector()
    url = canonn_realtime_url
    whitelist = dict()

    def __new__(cls):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.batch = list()
        self._batch_maxlen = 30         # каноны рекомендуют 40 во избежаение таймаута, мы перестрахуемся
        WhitelistUpdater().start()


    def on_journal_entry(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        event = entry["event"]

        if event in ("Location", "Startup"):
            self._submit_client(journalEntry)
            return
        
        if not journalEntry.system:     # потому что некоторые ивенты, например, FSSSignalDiscovered, при старте игры идут до Location
            return                      # и EDMC в этот момент отдаёт system=None
        
        """
        Эта секция - ивенты, которые каноны принимают в свой /postEvent.
        При этом они держат "белый список" ивентов и критериев к ним, который, как предполагается,
        мы должны подтягивать при запуске плагина, потому что они оставляют за собой право его изменять.
        Мы же не хотим отправлять незнамо что, поэтому копируем список себе (пока что на гитхаб, потом на свой сервер),
        вырезав всё, чем не хотим делиться.
        При этом каноны убедительно просят группировать "одновременные" ивенты (напр., сигналы станций) в один запрос,
        поэтому сначала обрабатываем их, одновременно отсеивая свои флитаки.
        """
        if (
            event == "FSSSignalDiscovered"
            and entry.get("IsStation") == True
            and not (
                entry.get("SignalType") == "FleetCarrier"
                and entry.get("SignalName")[0:4] == "CEC "      # вы же привели названия флитаков в соответствие правилам фракции, господа сотрудники?
            )
            and entry["timestamp"] == self.batch[0].data["timestamp"]
        ):
            if len(self.batch) == self._batch_maxlen:
                self._dump_batch()
            self.batch.append(journalEntry)
        
        else:
            if len(self.batch) > 0:
                self._dump_batch()
            # проверяем всё остальное
            self._post_event(journalEntry)

        # проверяем таргоидские гиперперехваты
        self._hdtracker.journal_entry(journalEntry)


    def _submit_client(self, journalEntry: JournalEntry):
        debug("[CanonnAPI] sending client version.")
        url = f"{self.url}/submitClient"
        params = {
            "cmdr":     journalEntry.cmdr,
            "beta":     journalEntry.is_beta,
            "client":   journalEntry.client,
            "autoupdate": global_context.by_class(Release).no_auto_val == False
        }
        Reporter(url, params).start()


    def _post_event(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        for accepted_event in self.whitelist:
            for key, value in accepted_event["definition"].items():
                if entry.get(key) != value:
                    return
        # если все пары ключей-значений совпадают, каноны в этом заинтересованы
        debug("[CanonnAPI] Sending the {!r} event to Canonn.", entry["event"])
        url = f"{self.url}/postEvent"
        gamestate = self._get_gamestate(journalEntry)
        params = {
            "gamestate": gamestate,
            "rawEvents": [entry],
            "cmdrName":  journalEntry.cmdr
        }
        Reporter(url, params).start()

    
    def _dump_batch(self):
        debug("[CanonnAPI] Dumping the batch, len={}.", len(self.batch))
        url = f"{self.url}/postEvent"
        gamestate = self._get_gamestate(self.batch[0])
        params = {
            "gamestate": gamestate,
            "rawEvents": [entry.data for entry in self.batch],
            "cmdrName":  self.batch[0].cmdr
        }
        Reporter(url, params.copy()).start()
        self.batch.clear()
    
    
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
            "clientVersion":    journalEntry.client,
            "isBeta":           journalEntry.is_beta
        }

        # дополнительные, которые мы 100% знаем
        gamestate["platform"] = "PC"

        # дополнительные, которые мы, возможно, знаем
        if global_context.odyssey != None:
            gamestate["odyssey"] = global_context.odyssey
        
        if entry.get("BodyID"):
            gamestate["bodyId"] = entry["BodyID"]
        
        if journalEntry.state.get("BodyName"):
            gamestate["bodyName"] = journalEntry.state.get("BodyName")
        
        optional = ["Temperatire", "Gravity", "Latitude", "Longitude"]
        for field in optional:
            if journalEntry.state.get(field):
                gamestate[field.lower()] = journalEntry.state.get(field)

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