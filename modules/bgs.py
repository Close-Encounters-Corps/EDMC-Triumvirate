import requests, traceback, json, os, sqlite3, re, threading
import tkinter as tk

from datetime import datetime, timezone
from collections import deque
from tkinter import font, ttk

from .debug import debug, error, info
from .lib.journal import JournalEntry
from .lib.module import Module
from .lib.conf import config
from .lib.thread import Thread, BasicThread
from .lib.context import global_context
from .player import Player
from .legacy import Reporter, URL_GOOGLE

import sys
if sys.maxsize >= 2**31:        # maxsize на 32 битах = 2**31-1
    from thirdparty.PIL64 import Image, ImageTk
else:
    from thirdparty.PIL import Image, ImageTk


class BGS(Module):
    _missions_tracker = None
    _cz_tracker = None
    _systems = list()
    _data_send_queue = deque()      # по логике нужна queue, но не хочу ещё один импорт тащить

    @classmethod
    def on_start(cls, plugin_dir: str):
        cls._plugin_dir = plugin_dir
        BGS._missions_tracker = Missions_Tracker()
        BGS._cz_tracker = CZ_Tracker()
        BGS.Systems_Updater().start()

    class Systems_Updater(Thread):
        def __init__(self):
            super().__init__(name="BGS systems list updater")
        def do_run(self):
            url = "https://api.github.com/gists/7455b2855e44131cb3cd2def9e30a140"
            attempts = 0
            while True:
                attempts += 1
                response = requests.get(url)
                if response.status_code == 200:
                    BGS._systems = str(response.json()["files"]["systems"]["content"]).split('\n')
                    info("[BGS.setup] Got list of systems to track.")
                    BGS._send_all()
                    return
                error("[BGS.setup] Couldn't get list of systems to track, response code {} ({} attempts)", response.status_code, attempts)
                self.sleep(10)

    @classmethod
    def on_journal_entry(cls, journalEntry: JournalEntry):
        try:
            entry = journalEntry.as_dict()
            cls._missions_tracker.process_entry(entry["cmdr"], entry["system"], entry["station"], entry["data"])
            cls._cz_tracker.process_entry(entry["cmdr"], entry["system"], entry["data"])
        except:
            error(traceback.format_exc())

    @classmethod
    def stop(cls):
        cls._missions_tracker.stop()

    @classmethod
    def _send(cls, url: str, params: dict, affected_systems: list):
        if not cls._systems:
            cls._data_send_queue.append({
                "url": url,
                "params": params,
                "systems": affected_systems
            })
            debug("[BGS.send] We still haven't got a list of systems to track, entry added to the queue.")
        else:
            for system in affected_systems:
                if system in cls._systems:
                    Reporter(url, params).start()
                    info("[BGS.send]: BGS information sent.")

    @classmethod
    def _send_all(cls):
        counter = 0
        for entry in cls._data_send_queue:
            for system in entry["systems"]:
                if system in cls._systems:
                    Reporter(entry["url"], entry["params"]).start()
                    counter += 1
        info(f"[BGS.send_all] {counter} pending entries sent.")
        cls._data_send_queue.clear()


class Missions_Tracker:
    def __new__(cls):
        if BGS._missions_tracker is None:
            BGS._missions_tracker = super().__new__(cls)
        return BGS._missions_tracker
    
    def __init__(self):
        path = os.path.join(BGS._plugin_dir, "data", "missions.db")
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self._query("CREATE TABLE IF NOT EXISTS missions (id, payload)")
        self.station_owner = ""
        self.redeemed_factions = []

    def stop(self):
        self._prune_expired()
        self.db.close()
    
    def _query(self, query: str, *args, fetchall: bool = False):
        with self.lock:
            cur = self.db.cursor()
            query = query.strip()
            q_type = query[:query.find(' ')].upper()
            cur.execute(query, args)
            if q_type == "SELECT":
                if fetchall:
                    result = cur.fetchall()
                else:
                    result = cur.fetchone()
            else:
                self.db.commit()
            cur.close()
        return result if q_type == "SELECT" else None
    
    def _prune_expired(self):
        info("[BGS.prune_expired] Clearing the database from expired missions.")
        expired_missions = []
        now = datetime.now(timezone.utc)
        missions_list = self._query("SELECT id, payload FROM missions", fetchall=True)
        for id, payload in missions_list:
            mission = json.loads(payload)
            if "Megaship" not in mission["type"]:
                expires = datetime.fromisoformat(mission["expires"])
                if expires <= now:
                    expired_missions.append(id)
        for id in expired_missions:
            self._query("DELETE FROM missions WHERE id = ?", id)
            debug("[BGS.prune_expired] Mission {} was deleted.", id)
        info("[BGS.prune_expired] Done.")


    def process_entry(self, cmdr, system, station, entry):
        event = entry["event"]
        # стыковка/вход в игру на станции
        if event == "Docked" or (event == "Location" and entry["Docked"] == True):
            self._docked(entry)
        # принятие миссии
        elif event == "MissionAccepted" and (
            system in BGS._systems
            or not BGS._systems
        ):
            self._mission_accepted(entry, system)
        # сдача миссии
        elif event == "MissionCompleted":
            self._mission_completed(entry, cmdr)
        # провал миссии
        elif event == "MissionFailed":
            self._mission_failed(entry, cmdr)
        # отказ от миссии
        elif event == "MissionAbandoned":
            self._mission_abandoned(entry)
        # ваучеры
        elif event == "RedeemVoucher" and (
            system in BGS._systems
            or not BGS._systems
        ):
            self._redeem_voucher(entry, cmdr, system)
        # картография
        elif "SellExplorationData" in event and (
            system in BGS._systems
            or not BGS._systems
        ):
            self._exploration_data(entry, cmdr, system, station)
        

    def _docked(self, entry):
        self.station_owner = entry["StationFaction"]["Name"]
        self.redeemed_factions = []
        debug("[BGS.set_faction]: detected {!r}, station_owner set to {!r}", entry["event"], self.station_owner)


    def _mission_accepted(self, entry, system):
        mission = {
            "timestamp": entry["timestamp"],
            "ID": entry["MissionID"],
            "expires": entry.get("Expiry", ""),
            "type": entry["Name"],
            "system": system,
            "faction": entry["Faction"],
            "system2": entry.get("DestinationSystem", "") if entry.get("TargetFaction") else "",
            "faction2": entry.get("TargetFaction", ""),
        }
        self._query("INSERT INTO missions (id, payload) VALUES (?, ?)", mission["ID"], json.dumps(mission))
        debug("[BGS.mission_accepted] Mission {!r} was accepted and saved to the database.", mission["ID"])


    def _mission_completed(self, entry, cmdr):
        mission_id = entry["MissionID"]
        result = self._query("SELECT payload FROM missions WHERE id = ?", mission_id)
        if result is None:
            debug("[BGS.mission_completed] Mission {!r} was completed, but not found in the database.", mission_id)
            return
        self._query("DELETE FROM missions WHERE id = ?", mission_id)
        debug("[BGS.mission_completed] Mission {!r} was completed and deleted from the database.", mission_id)

        mission = json.loads(result[0])
        inf_changes = dict()
        for item in entry["FactionEffects"]:
            # Название второй фракции может быть не прописано в MissionCompleted.
            # Если оно было в MissionAccepted, копируем оттуда.
            if item["Faction"] == "" and mission["faction2"] != "":
                item["Faction"] = mission["faction2"]
            # inf_changes = { faction (str): influence_change (int) }
            inf_changes[item["Faction"]] = len(item["Influence"][0]["Influence"])
            if item["Influence"][0]["Trend"] == "DownBad":
                inf_changes[item["Faction"]] *= -1
        
        url = f'{URL_GOOGLE}/1FAIpQLSdlMUq4bcb4Pb0bUTx9C6eaZL6MZ7Ncq3LgRCTGrJv5yNO2Lw/formResponse'
        url_params = {
            "entry.1839270329": cmdr,
            "entry.1889332006": mission["type"],
            "entry.350771392": "COMPLETED",
            "entry.592164382": mission["system"],
            "entry.1812690212": mission["faction"],
            "entry.179254259": inf_changes[mission["faction"]],
            "entry.739461351": mission["system2"],
            "entry.887402348": mission["faction2"],
            "entry.1755429366": inf_changes.get(mission["faction2"], ""),
            "usp": "pp_url",
        }
        BGS._send(url, url_params, [mission["system"], mission["system2"]])


    def _mission_failed(self, entry, cmdr):
        mission_id = entry["MissionID"]
        result = self._query("SELECT payload FROM missions WHERE id = ?", mission_id)
        if result is None:
            debug("[BGS.mission_failed] Mission {!r} was failed, but not found in the database.", mission_id)
            return
        self._query("DELETE FROM missions WHERE id = ?", mission_id)
        debug("[BGS.mission_failed] Mission {!r} was failed and deleted from the database.", mission_id)

        failed_mission = json.loads(result[0])
        url = f'{URL_GOOGLE}/1FAIpQLSdlMUq4bcb4Pb0bUTx9C6eaZL6MZ7Ncq3LgRCTGrJv5yNO2Lw/formResponse'
        url_params = {
            "entry.1839270329": cmdr,
            "entry.1889332006": failed_mission["type"],
            "entry.350771392": "FAILED",
            "entry.592164382": failed_mission["system"],
            "entry.1812690212": failed_mission["faction"],
            "entry.179254259": -2,
            "entry.739461351": failed_mission["system2"],
            "entry.887402348": failed_mission["faction2"],
            "entry.1755429366": "-2" if failed_mission["system2"] != "" else "",
            "usp": "pp_url",
        }
        BGS._send(url, url_params, [failed_mission["system"], failed_mission["system2"]])


    def _mission_abandoned(self, entry):
        mission_id = entry["MissionID"]
        result = self._query("SELECT payload FROM missions WHERE id = ?", mission_id)
        if result is None:
            debug("[BGS.mission_abandoned] Mission {!r} was abandoned, but not found in the database.", mission_id)
            return
        
        mission = json.loads(result[0])
        if "Megaship" not in mission["type"]:
            self._query("DELETE FROM missions WHERE id = ?", mission_id)
            debug("[BGS.mission_abandoned] Mission {!r} was abandoned and deleted from the database.", mission_id)


    def _redeem_voucher(self, entry, cmdr, system):
        # Игнорируем флитаки, юристов и лишние типы выплат.
        if (self.station_owner == "FleetCarrier"
            or "BrokerPercentage" in entry
            or entry["Type"] not in ("bounty", "CombatBond")
        ):
            return
        
        url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse'
        if entry["Type"] == "bounty":
            debug("[BGS.redeem_voucher] Redeeming bounties:")
            for faction in entry["Factions"]:
                if faction["Faction"] not in self.redeemed_factions:
                    debug("[BGS.redeem_voucher] Faction {!r}, amount: {}", faction["Faction"], faction["Amount"])
                    url_params = {
                        "entry.503143076": cmdr,
                        "entry.1108939645": entry["Type"],
                        "entry.127349896": system,
                        "entry.442800983": "",
                        "entry.48514656": faction["Faction"],
                        "entry.351553038": faction["Amount"],
                        "usp": "pp_url",
                    }
                    self.redeemed_factions.append(faction["Faction"])    
        else:
            debug("[BGS.redeem_voucher] Redeeming bonds: faction {!r}, amount: {}", entry["Faction"], entry["Amount"])
            url_params = {
                "entry.503143076": cmdr,
                "entry.1108939645": entry["Type"],
                "entry.127349896": system,
                "entry.442800983": "",
                "entry.48514656": entry["Faction"],
                "entry.351553038": entry["Amount"],
                "usp": "pp_url",
            }
        BGS._send(url, url_params, [system])


    def _exploration_data(self, entry, cmdr, system, station):
        if self.station_owner != "FleetCarrier":
            url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse'
            url_params = {
                "entry.503143076": cmdr,
                "entry.1108939645": "SellExpData",
                "entry.127349896": system,
                "entry.442800983": station,
                "entry.48514656": self.station_owner,
                "entry.351553038": entry["TotalEarnings"],
                "usp": "pp_url"
            }
            debug("[BGS.exploration_data]: Sold exploration data for {} credits, station's owner: {!r}",
                entry["TotalEarnings"],
                self.station_owner)
            BGS._send(url, url_params, [system])


class CZ_Tracker:
    def __new__(cls):
        if BGS._cz_tracker is None:
            BGS._cz_tracker = super().__new__(cls)
        return BGS._cz_tracker
    
    def __init__(self):
        self.in_conflict = False
        self.safe = False       # на случай, если плагин запускается посреди игры, и мы не знаем режим
        self.on_foot = None     # не тип конфликта, а именно режим игры. ТРП тоже считается


    def process_entry(self, cmdr, system, entry):
        event = entry["event"]
        # проверка режима игры
        if event == "LoadGame":
            self.safe = entry["GameMode"] != "Open"
            debug("CZ_Tracker: safe set to {!r}", self.safe)
            return

        # отслеживание режима игрока (космос/ноги)
        if (event in ("DropshipDeploy", "Disembark", "LaunchSRV")
            or event == "Location" and (entry.get("InSRV") or entry.get("OnFoot"))
        ):
            self.on_foot = True
            debug("CZ_Tracker: on foot")
        elif (event == "DockSRV" 
            or event == "Embark" and entry["SRV"] == False
            or event == "Location" and not(entry.get("InSRV") or entry.get("OnFoot"))
        ):
            self.on_foot = False
            debug("CZ_Tracker: on ship")

        # релог в пеших кз
        # ApproachSettlement в логах идёт раньше Location, и EDMC отдаёт system = None в этот момент
        # в самом ApproachSettlement названия системы нет, но есть название тела
        if event == "ApproachSettlement" and system == None:
            pattern = r"\s([A-Z]\s)?\d{1,3}(\s[a-z])?$"
            system = re.sub(pattern, "", entry["BodyName"])
        
        if system in BGS._systems or not BGS._systems:
            if self.in_conflict == False:
                # начало конфликта (космос)
                if event == "SupercruiseDestinationDrop" and "$Warzone_PointRace" in entry["Type"]:
                    self._start_conflict(cmdr, system, entry, "Space")
                # начало конфликта (ноги)
                elif (event == "ApproachSettlement"
                    and entry["StationFaction"].get("FactionState", "") in ("War", "CivilWar")
                    and "dock" not in entry["StationServices"]):
                    self._start_conflict(cmdr, system, entry, "Foot")
            else:
                # убийство
                if event == "FactionKillBond":
                    self._kill(entry)
                # сканирование корабля
                elif event == "ShipTargeted" and entry["TargetLocked"] == True and entry["ScanStage"] == 3:
                    self._ship_scan(entry)
                # отслеживание сообщений, потенциальное завершение конфликта
                elif event == "ReceiveText":
                    self._patrol_message(entry)
                # завершение конфликта: прыжок
                elif event == "StartJump":
                    self._end_conflict()
                # завершение конфликта: возврат на шаттле (ноги)
                elif event == "BookDropship" and entry["Retreat"] == True:
                    self._end_conflict()
                # релог в пешей кз
                elif event == "Music" and entry["MusicTrack"] == "MainMenu" and self.on_foot == True:
                    self._end_conflict()
                # досрочный выход
                elif (event in ("Shutdown", "Died", "CancelDropship", "SelfDestruct") or        # это для любых кз
                        event == "Music" and entry["MusicTrack"] == "MainMenu"):      # а это уже только в космосе будет работать
                    self._reset()

        
    def _start_conflict(self, cmdr, system, entry, c_type):
        debug("CZ_Tracker: detected entering a conflict zone, {!r} type.", c_type)
        self.in_conflict = True
        self.end_messages = dict()      # например, {"independent": deque(), "federal": deque()}

        if c_type == "Space":
            self.info = {
                "cmdr": cmdr,
                "system": system,
                "conflict_type": "Space",
                "allegiances": {},
                "player_fights_for": None,
                "kills": 0,
                "kills_limit": 5,
                "start_time": datetime.fromisoformat(entry["timestamp"]),
                "end_time": None
            }
            intensity = entry["Type"]
            intensity = intensity[19:intensity.find(":")]
            if intensity == "Med":
                intensity = "Medium"
            self.info["intensity"] = intensity

        elif c_type == "Foot":
            self.info = {
                "cmdr": cmdr,
                "system": system,
                "conflict_type": "Foot",
                "location": entry["Name"],
                "intensity": None,
                "allegiances": {},
                "player_fights_for": None,
                "kills": 0,
                "kills_limit": 20,
                "start_time": datetime.fromisoformat(entry["timestamp"]),
                "end_time": None,
            }

        debug("CZ_Tracker prepared.")


    def _kill(self, entry):
        if not self.info["player_fights_for"]:
            self.info["player_fights_for"] = entry["AwardingFaction"]

        for conflict_side in (entry["AwardingFaction"], entry["VictimFaction"]):
            if conflict_side not in self.info["allegiances"]:
                self.info["allegiances"][conflict_side] = None
                debug("CZ_Tracker: faction {!r} added to the list.", conflict_side)

        if self.info["conflict_type"] == "Foot" and not self.on_foot:
            self.info["kills"] += 4
            debug("CZ_Tracker: detected a kill from a ship in a foot combat zone. Awarding {!r}, victim {!r}. {}(+4) kills.",
                entry["AwardingFaction"],
                entry["VictimFaction"],
                self.info["kills"])
        else:
            self.info["kills"] += 1
            debug("CZ_Tracker: detected FactionKillBond, awarding {!r}, victim {!r}. {} kills.",
                entry["AwardingFaction"],
                entry["VictimFaction"],
                self.info["kills"])
            
        # определение интенсивности пешей кз
        if (
            not self.info["intensity"]
            and self.info["conflict_type"] == "Foot"
            and self.on_foot
        ):
            reward = entry["Reward"]
            if 1896 <= reward < 4172:
                self.info["intensity"] = "Low"
            elif 11858 <= reward <= 33762:
                self.info["intensity"] = "Medium"
            elif 39642 <= reward <= 87362:
                self.info["intensity"] = "High"
            debug("CZ_Tracker: intensity set to {!r}", self.info["intensity"])
    

    def _ship_scan(self, entry):
        if "$ShipName_Military" in entry["PilotName"]:
            conflict_side = entry["Faction"]
            allegiance = entry["PilotName"][19:-1]
            if conflict_side not in self.info["allegiances"]:
                self.info["allegiances"][conflict_side] = allegiance
                debug("CZ_Tracker: detected military ship scan. Faction {!r} added to the list, allegiance {!r}.", conflict_side, allegiance)

    
    def _patrol_message(self, entry):
        # Логика следующая: получаем 5 "патрулирующих" сообщений от одной стороны за 15 секунд - считаем конфликт завершённым.
        # По имени фильтруем, чтобы случайно не поймать последним такое сообщение, например, от спецкрыла
        # и сломать определение принадлежности победителя.
        if "$Military_Passthrough" in entry["Message"] and "$ShipName_Military" in entry["From"]:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            allegiance = entry["From"][19:1]
            debug("CZ_Tracker: detected patrol message sent from {!r} ship.", allegiance)

            if not self.end_messages.get(allegiance):
                self.end_messages[allegiance] = deque(5*[None], 5)
            queue = self.end_messages[allegiance]
            queue.append(timestamp)
            
            if queue[0] != None:
                if (queue[4] - queue[0]).seconds <= 15:
                    debug("CZ_Tracker: got 5 patrol messages in 15 seconds, calling END_CONFLICT.")
                    self._end_conflict(allegiance)


    def _end_conflict(self, winners_allegiance: str | None = None):
        debug("CZ_Tracker: END_CONFLICT called, calculating the result.")
        self.info["end_time"] = datetime.now(timezone.utc)
        factions_list = list(self.info["allegiances"].items())
        presumed_winner = "[UNKNOWN]"

        if winners_allegiance and self.safe:        # если мы получили принадлежность из патрулирующих сообщений и не в опене
            '''
            Что дальше вообще происходит. Объяснение в первую очередь для меня самого, потому что через неделю забуду ведь.
            Если принадлежность обеих фракций одинаковая - победителя не установить. Игнорируем этот вариант.
            Если принадлежность разная, есть 2 варианта:
            1 - принадлежность обеих фракций известна. Всё просто, тупо сравниваем их с принадлежностью победителя.
            2 - у одной из фракций принадлежность неизвестна. Тут чуть сложнее:
                а) если единственная известная принадлежность совпадает с принадлежностью победителя - мы не можем быть уверены,
                    что у второй фракции принадлежность отличается. Предсказание невозможно.
                б) единственная известная принадлежность не совпадает с принадлежностью победителя - тогда это точно вторые.
            '''
            if factions_list[0][1] != factions_list[1][1]:
                if None not in (factions_list[0][1], factions_list[1][1]):
                    for index, faction in enumerate(factions_list):
                        if faction[1] == winners_allegiance:
                            presumed_winner = factions_list[index][0]
                else:
                    for index, faction in enumerate(factions_list):
                        if faction[1] != None and faction[1] != winners_allegiance:
                            presumed_winner = factions_list[index-1][0]         # index-1 будет либо 0, либо -1, что при двух фракциях == 1

        elif self.info["kills"] < self.info["kills_limit"]:
            debug("CZ_Tracker: not enough kills ({}/{}), resetting.", self.info["kills"], self.info["kills_limit"])
            self._reset()
            return
        
        # предсказание победителя
        # мы не можем наверняка сказать, что фракция игрока победила, но будем *предполагать* такой исход
        if (
            presumed_winner == "[UNKNOWN]"
            and self.info["kills"] >= self.info["kills_limit"]
            and self.safe
        ):
            debug("CZ_Tracker: predicting the winner.")
            presumed_winner = self.info["player_fights_for"]

        debug("CZ_Tracker: presumed winner set to {!r}.", presumed_winner)

        if presumed_winner != self.info["player_fights_for"]:
            debug("CZ_Tracker: presumed winner isn't the player's side, asking for confirmation.")
            info_copy = self.info.copy()
            self._ask_user(info_copy, presumed_winner)
        else:
            actual_winner = presumed_winner
            debug("CZ_Tracker: actual winner set to {!r}.", actual_winner)
            self._send_results(self.info, presumed_winner, actual_winner)
        
        self._reset()


    @staticmethod
    def _ask_user(info: dict, presumed_winner: str):
        BasicThread(target=lambda: CZ_Tracker.Notification(info, presumed_winner), name="cz notification").start()
    

    @staticmethod
    def _send_results(info: dict, presumed: str, actual: str):
        match info.get("intensity"):
            case "Low":     weight = 0.25
            case "Medium":  weight = 0.5
            case "High":    weight = 1
            case _:         weight = 0.25
        url = f'{URL_GOOGLE}/1FAIpQLSepTjgu1U8NZXskFbtdCPLuAomLqmkMAYCqk1x0JQG9Btgb9A/formResponse'
        url_params = {
                "entry.1673815657": info["start_time"].strftime("%d.%m.%Y %H:%M:%M"),
                "entry.1896400912": info["end_time"].strftime("%d.%m.%Y %H:%M:%M"),
                "entry.1178049789": info["cmdr"],
                "entry.721869491": info["system"],
                "entry.1671504189": info["conflict_type"],
                "entry.461250117": info.get("location", ""),
                "entry.428944810": info.get("intensity", ""),
                "entry.1396326275": str(weight).replace('.', ','),
                "entry.1674382418": presumed,
                "entry.1383403456": actual,
                "usp": "pp_url",
            }
        BGS._send(url, url_params, [info["system"]])


    def _reset(self):
        self.in_conflict = False
        self.info = None
        self.end_messages = None
        debug("CZ_Tracker was resetted to the initial state.")


    class Notification(tk.Toplevel):
        def __init__(self, info: dict, presumed_winner: str):
            super().__init__()
            self.info = info
            self.factions = [faction for faction, _ in info["allegiances"].items()]
            self.presumed = presumed_winner

            screen_height = self.winfo_screenheight()
            if screen_height <= 1080:
                self.scale = 1
            else:
                self.scale = screen_height / 1080

            self.title("Результаты зоны конфликта")
            self.resizable(False, False)
            self.geometry(config.get_str("CZ.Notification.position"))
            self.default_font = font.nametofont("TkDefaultFont").actual()["family"]

            Player(BGS._plugin_dir, ["sounds/cz_notification.wav"]).start()
            self.image_path = os.path.join(BGS._plugin_dir, "icons", "cz_notification.png")

            self.topframe = ttk.Frame(self, padding=3)
            self.bottomframe = ttk.Frame(self, padding=3)
            self.topframe.grid(row=0, column=0, sticky="NWE")
            self.bottomframe.grid(row=1, column=0, sticky="SWE")

            # topframe
            self.toplabel = ttk.Label(
                self.topframe,
                text="Зафиксировано завершение зоны конфликта",
                font=(self.default_font, int(15*self.scale))
            )
            self.bottomlabel = ttk.Label(
                self.topframe,
                text="Выберите победившую фракцию:",
                font=(self.default_font, int(12*self.scale))
            )
            self.msgframe = self._get_msgframe(self.topframe)

            self.toplabel.grid(row=0, column=0, columnspan=2, sticky="N")
            self.msgframe.grid(row=1, column=0, sticky="W")
            self.bottomlabel.grid(row=2, column=0, columnspan=2, sticky="S")

            # bottomframe
            ttk.Style().configure("notif.TButton", font=(self.default_font, int(10*self.scale)), padding=4, width=1)
            self.leftbutton = ttk.Button(
                self.bottomframe,
                text=self.factions[0],
                style="notif.TButton",
                command=lambda: self._result(self.factions[0])
            )
            self.rightbutton = ttk.Button(
                self.bottomframe,
                text=self.factions[1],
                style="notif.TButton",
                command=lambda: self._result(self.factions[1])
            )
            self.cancelbutton = ttk.Button(
                self.bottomframe,
                text="Никто (досрочный выход из зоны конфликта/ложное срабатывание)",
                style="notif.TButton",
                command=lambda: self._result()
            )
            self.bottomframe.columnconfigure(0, weight=1)
            self.bottomframe.columnconfigure(1, weight=1)
            self.leftbutton.grid(row=0, column=0, sticky="NSWE")
            self.rightbutton.grid(row=0, column=1, sticky="NSWE")
            self.cancelbutton.grid(row=1, column=0, columnspan=2, sticky="NSWE")

        
        def _get_msgframe(self, parent) -> ttk.Frame:
            frame = ttk.Frame(parent)
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=1)

            ttk.Style().configure("msgtext.TLabel", font=(self.default_font, int(9*self.scale)), justify="left")
            is_foot = (self.info["conflict_type"] == "Foot")
            match self.info.get("intensity"):
                case "Low":     intensity = "низкая"
                case "Medium":  intensity = "средняя"
                case "High":    intensity = "высокая"
                case _:         intensity = "НЕ ОПРЕДЕЛЕНА"

            ttk.Label(
                frame,
                text="Подтвердите правильность полученных данных:", 
                font=(self.default_font, int(12*self.scale)),
            ).grid(row=0, column=0, columnspan=2, sticky="W")

            leftframe = tk.Frame(frame)
            rightframe= tk.Frame(frame)

            # левый столбец
            ttk.Label(leftframe, style="msgtext.TLabel", text="Система:").grid(row=0, column=0, sticky="NW")
            ttk.Label(leftframe, style="msgtext.TLabel", text="Поселение:").grid(row=1, column=0, sticky="NW") if is_foot else None
            ttk.Label(leftframe, style="msgtext.TLabel", text="Напряжённость:").grid(row=1+is_foot, column=0, sticky="NW")
            ttk.Label(leftframe, style="msgtext.TLabel", text="Участвующие фракции:\n").grid(row=2+is_foot, column=0, sticky="NW")
            ttk.Label(leftframe, style="msgtext.TLabel", text="Предполагаемый победитель:").grid(row=3+is_foot, column=0, sticky="NW")
            ttk.Label(leftframe, style="msgtext.TLabel", text="Вы сражались на стороне:").grid(row=4+is_foot, column=0, sticky="NW")

            # правый столбец
            ttk.Label(rightframe, style="msgtext.TLabel", text=self.info["system"]).grid(row=0, column=0, sticky="NW")
            ttk.Label(rightframe, style="msgtext.TLabel", text=self.info["location"]).grid(row=1, column=0, sticky="NW") if is_foot else None
            ttk.Label(rightframe, style="msgtext.TLabel", text=intensity).grid(row=1+is_foot, column=0, sticky="NW")
            ttk.Label(rightframe, style="msgtext.TLabel", text=str(self.factions[0]+"\n"+self.factions[1])).grid(row=2+is_foot, column=0, sticky="NW")
            ttk.Label(rightframe, style="msgtext.TLabel", text=self.presumed).grid(row=3+is_foot, column=0, sticky="NW")
            ttk.Label(rightframe, style="msgtext.TLabel", text=self.info["player_fights_for"]).grid(row=4+is_foot, column=0, sticky="NW")

            leftframe.grid(row=1, column=0, sticky="NSWE")
            rightframe.grid(row=1, column=1, sticky="NSWE")

            # иконка
            self.update()               # для получения leftframe.winfo_height()
            self.image = Image.open(self.image_path)
            img_scale = leftframe.winfo_reqheight() / self.image.height
            self.image = self.image.resize((int(self.image.width*img_scale), int(self.image.height*img_scale)))
            self.image = ImageTk.PhotoImage(self.image)
            self.canvas = tk.Canvas(
                frame,
                height=self.image.height(),
                width=self.image.width(),
            )
            # (2,2) из-за каких-то непонятных мне отступов у canvas-а, режущих картинку
            self.canvas.create_image(2, 2, anchor="nw", image=self.image)
            self.canvas.grid(row=1, column=2, sticky="NSWE", padx=int(15*self.scale))

            return frame
        
        
        def _result(self, actual_winner: str = None):
            if actual_winner:
                debug("CZ_Tracker: actual winner set to {!r}.", actual_winner)
                CZ_Tracker._send_results(self.info, self.presumed, actual_winner)
            else:
                debug("CZ_Tracker: user canceled the choice.")
            self.destroy()