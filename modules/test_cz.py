from collections import deque
from datetime import datetime
import threading
import traceback
import json

from tkinter.messagebox import askyesnocancel
from urllib.parse import quote_plus

from legacy import Reporter

URL_GOOGLE = 'https://docs.google.com/forms/d/e'

#from .debug import debug, error
def debug(string):
    print(f"DEBUG: {string}")

def error(string):
    print(f"ERROR: {string}")


class CZ_Tracker():
    def __init__(self):
        self.threadlock = threading.Lock()
        self.in_conflict = False


    def check_event(self, cmdr, system, entry):
        self.threadlock.acquire()
        self.cmdr = cmdr
        self.system = system

        try:
            event = entry["event"]
            # вход в зону конфликта
            if event == "SupercruiseDestinationDrop" and "$Warzone_PointRace" in entry["Type"]:
                self.__start_conflict(cmdr, system, entry)
            if self.in_conflict == True:
                # для определения сторон конфликта
                if event == "ShipTargeted" and entry["TargetLocked"] == True and entry["ScanStage"] == 3:
                    self.__ship_scan(entry)
                elif event == "FactionKillBond":
                    self.__kill(entry)
                # для определения победителя
                elif event == "ReceiveText":
                    self.__patrol_message(entry)
                # досрочный выход из кз: завершение игры, круиз, прыжок, смерть, выход в меню
                elif event in ("Shutdown", "SupercruiseEntry", "FSDJump", "Died") or (event == "Music" and entry["MusicTrack"] == "MainMenu"):
                    self.__end_conflict()

        except:
            error(traceback.format_exc())
        self.threadlock.release()
    

    def __start_conflict(self, cmdr, system, entry):
        debug("START_CONFLICT: detected entering a conflict zone")
        self.in_conflict = True
        self.cmdr = cmdr
        self.system = system
        self.cz_info = {
            "intensity": entry["Type"][19:entry["Type"].find(":")],
            "factions": [],
            "win_messages_count": 0,
            "player_fights_for": None,
            "time_start": datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
            "time_finish": None
        }
        self.end_messages = deque(5*[None], 5)
        debug("START_CONFLICT: CZ_Tracker prepared")


    def __ship_scan(self, entry):
        debug("SHIP_SCAN: detected \"ShipTargeted\" with scan stage 3")
        if "$ShipName_Military" in entry["PilotName"]:
            debug(f"SHIP_SCAN: military ship, faction \"{entry['Faction']}\", allegience - {entry['PilotName'][19:-1]}")
            for faction in self.cz_info["factions"]:
                if faction["name"] == entry["Faction"]:
                    debug("SHIP_SCAN: faction already in the list, checking allegience")
                    if faction["allegience"] == None:
                        faction["allegience"] = entry["PilotName"][19:-1]
                        debug("SHIP_SCAN: allegience added to the faction info")
                    else:
                        debug("SHIP_SCAN: allegience already in the list")
                    return

            debug("SHIP_SCAN: faction not in the list, adding")
            faction_name = entry["Faction"]
            faction_allegience = entry["PilotName"][19:-1]
            self.cz_info["factions"].append({
                "name": faction_name,
                "allegience": faction_allegience,
            })
        else:
            debug("SHIP_SCAN: not a military ship")
            

    def __kill(self, entry):
        debug(f"KILL: detected \"FactionKillBond\", awarding \"{entry['AwardingFaction']}\", victim \"{entry['VictimFaction']}\"")
        if self.cz_info["player_fights_for"] == None:
            self.cz_info["player_fights_for"] = entry["AwardingFaction"]
            debug(f"KILL: \"player_fights_for\" was None, now set to \"{entry['AwardingFaction']}\"")
        
        for faction in (entry["AwardingFaction"], entry["VictimFaction"]):
            debug(f"KILL: checking if \"{faction}\" is in the list")
            found = False
            for saved_faction in self.cz_info["factions"]:
                if saved_faction["name"] == faction:
                    debug("KILL: it is")
                    found = True
                    break
            if not found:
                debug("KILL: it is not, adding (allegience = None)")
                self.cz_info["factions"].append({
                    "name": faction,
                    "allegience": None,
                })
        
    
    def __patrol_message(self, entry):
        # логика следующая: получаем 5 "патрулирующих" сообщений за 5 секунд - 
        # считаем конфликт завершённым
        if "$Military_Passthrough" in entry["Message"]:
            debug("PATROL_MESSAGE: detected \"$Military_Passthrough\" message")
            timestamp = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            self.end_messages.append(timestamp)
            debug("PATROL_MESSAGE: time added to the deque")
            try:
                if (self.end_messages[4] - self.end_messages[0]).seconds <= 5:
                    debug("PATROL_MESSAGE: detected 5 messages in 5 seconds, calling END_CONFLICT")
                    allegience = entry["From"][19:-1]
                    self.__end_conflict(allegience)
            except TypeError:       # если сообщений <5, [4] будет None
                pass

    
    def __end_conflict(self, allegience = None):
        if allegience != None:
            self.cz_info["time_finish"] = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            debug("END_CONFLICT: time_finish set, proceeding to calculate the result")
            factions = [faction for faction in self.cz_info["factions"]]

            # если принадлежность одинакова: спрашиваем игрока, отсылаем с учётом его выбора
            if factions[0]["allegience"] == factions[1]["allegience"]:
                debug(f"END_CONFLICT: allegience is the same ({factions[0]['allegience']}), asking user for confirmation")
                confirmation = self.__confirm_unknown()
                debug(f"END_CONFLICT: got response \"{confirmation}\"")
                if confirmation == True:
                    debug(f"END_CONFLICT: calling SEND_RESULT with {self.cz_info['player_fights_for']} as the winner")
                    self.__send_result(self.cz_info["player_fights_for"], True)
                elif confirmation == False:
                    enemy = None
                    for faction in self.cz_info["factions"]:
                        if faction["name"] != self.cz_info["player_fights_for"]:
                            enemy = faction["name"]
                            break
                    debug(f"END_CONFLICT: calling SEND_RESULT with {enemy} as the winner")
                    self.__send_result(enemy, True)
                # на случай "отмены"
                else:
                    debug("END_CONFLICT: calling SEND_RESULT with no arguments")
                    self.__send_result()
            
            # одна из принадлежностей не установлена:
            elif None in (factions[0]["allegience"], factions[1]["allegience"]):
                debug(f"END_CONFLICT: allegience of one of the factions is unknown")
                with_allegience, without_allegience = (factions[0], factions[1]) if factions[0]["allegience"] is not None else (factions[1], factions[0])

                # принадлежность победителя совпадает с единственной известной: мы не уверены, что победили не вторые.
                # уточняем у игрока, отсылаем с учётом его выбора
                if with_allegience["allegience"] == allegience:
                    debug(f"END_CONFLICT: known allegience coincides with the winner's one, asking user for confirmation")
                    confirmation = self.__confirm_unknown()
                    debug(f"END_CONFLICT: got response \"{confirmation}\"")
                    if confirmation == True:
                        debug(f"END_CONFLICT: calling SEND_RESULT with {self.cz_info['player_fights_for']} as the winner")
                        self.__send_result(self.cz_info["player_fights_for"], True)
                    elif confirmation == False:
                        enemy = None
                        for faction in self.cz_info["factions"]:
                            if faction["name"] != self.cz_info["player_fights_for"]:
                                enemy = faction["name"]
                                break
                        debug(f"END_CONFLICT: calling SEND_RESULT with {enemy} as the winner")
                        self.__send_result(enemy, True)
                    # на случай "отмены"
                    else:
                        debug("END_CONFLICT: calling SEND_RESULT with no arguments")
                        self.__send_result()

                # принадлежность победителя не совпадает с единственной известной => это 100% вторая фракция
                else:
                    debug(f"END_CONFLICT: known allegience DOES NOT coincide with the winner's one, asking user for confirmation")
                    confirmation = self.__confirm_known(without_allegience['name'])
                    debug(f"END_CONFLICT: got response \"{confirmation}\"")
                    if confirmation == True:
                        debug(f"END_CONFLICT: calling SEND_RESULTS with {without_allegience} as the winner")
                        self.__send_result(without_allegience, True)
                    elif confirmation == False:
                        debug(f"END_CONFLICT: calling SEND_RESULTS with {with_allegience} as the winner")
                        self.__send_result(with_allegience, True)
                    # на случай "отмены"
                    else:
                        debug(f"END_CONFLICT: calling SEND_RESULT with {without_allegience} as the winner, but not confirmed")
                        self.__send_result(without_allegience, False)
            
            # обе принадлежности установлены, они разные, понять, кто победил, не составляет труда
            else:
                debug("END_CONFLICT: both allegiences are known")
                for faction in self.cz_info["factions"]:
                    if faction["allegience"] == allegience:
                        debug(f"END_CONFLICT: {faction['name']} is most likely the winner, asking user for confirmation")
                        confirmation = self.__confirm_known(faction['name'])
                        debug(f"END_CONFLICT: got response \"{confirmation}\"")
                        if confirmation == True:
                            debug(f"END_CONFLICT: calling SEND_RESULTS with {faction['name']} as the winner")
                            self.__send_result(faction["name"], True)
                            break
                        elif confirmation == False:
                            enemy = None
                            for another in self.cz_info["factions"]:
                                if another["name"] != faction["name"]:
                                    enemy = another["name"]
                                    break
                            debug(f"END_CONFLICT: calling SEND_RESULTS with {enemy} as the winner")
                            self.__send_result(enemy, True)
                            break
                        # на случай "отмены"
                        else:
                            debug(f"END_CONFLICT: calling SEND_RESULT with {faction['name']} as the winner, but not confirmed")
                            self.__send_result(faction["name"], False)
                            break

            debug("END_CONFLICT: resetting CZ_Tracker")
        else:
            debug("END_CONFLICT: detected premature leaving, CZ_Tracker is reset")
        self.__init__()
        self.threadlock.acquire()


    def __confirm_known(self, winner: str):
        message = str("Зафиксировано окончание зоны конфликта.\n" +
            "Подтвердите правильность полученных данных:\n" +
            f"Напряжённость конфликта: {self.cz_info['intensity']}\n" +
            "Участвующие фракции:\n" +
            f"  - {self.cz_info['factions'][0]['name']}\n" +
            f"  - {self.cz_info['factions'][1]['name']}\n" +
            f"Фракция-победитель: {winner}"
        )
        return askyesnocancel("Завершение зоны конфликта", message)
    

    def __confirm_unknown(self):
        message = str("Зафиксировано окончание зоны конфликта.\n" +
            "Подтвердите правильность полученных данных:\n" +
            f"Время конфликта: {self.cz_info['time_start'].time()}-{self.cz_info['time_finish'].time()}\n" +
            f"Напряжённость конфликта: {self.cz_info['intensity']}\n" +
            "Участвующие фракции:\n" +
            f"  - {self.cz_info['factions'][0]['name']}\n" +
            f"  - {self.cz_info['factions'][1]['name']}\n" +
            "Фракция-победитель: НЕ ОПРЕДЕЛЕНА\n" +
            f"Вы сражались на стороне: {self.cz_info['player_fights_for']}\n\n" +
            f"Выберите \"Да\" в случае, если победила сторона, на которой вы сражались."
        )
        return askyesnocancel("Завершение зоны конфликта", message)


    def __send_result(self, winner = None, confirmed = False):
        debug("SEND_RESULT: forming response")
        url_params = {
                "entry.276599870": self.cz_info["time_start"].strftime("%d.%m.%Y %H:%M:%M"),
                "entry.107026375": self.cz_info["time_finish"].strftime("%d.%m.%Y %H:%M:%M"),
                "entry.856417302": self.cmdr,
                "entry.1329741081": self.system,
                "entry.2083736029": "Space",
                "entry.1314212673": self.cz_info["intensity"],
                "entry.1076602401": winner if winner != None else "[UNKNOWN]",
                "entry.1746398448": "logs",
                "entry.1916160623": "Yes" if confirmed else "No"
            }
        url = f'{URL_GOOGLE}/1FAIpQLScfYudjfdwa2c7Y1pEQpyoERuB-kbYvX-J7vLWB8J-JtsngBg/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(str(v), safe=str())}" for k, v in url_params.items()])}'
        debug("SEND_RESULT: link: " + url)
        Reporter(url).start()
        debug("SEND_RESULT: successfully sent to google sheet")
            


tracker = CZ_Tracker()
with open("C:\\Users\\user\\Documents\\code\\EDMC-Triumvirate\\modules\\test.log") as log:
    for line in log:
        entry = json.loads(line)
        tracker.check_event("CMDR", "SYSTEM", entry)