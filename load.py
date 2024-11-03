# -*- coding: utf-8 -*-
import csv
import functools
import os
import logging
import webbrowser
import traceback
import tkinter as tk
from datetime import datetime
from urllib.parse import quote_plus
from contextlib import closing
from queue import Queue
from semantic_version import Version

### third-party модули ###
import requests

### модули EDMC ###
import l10n
import myNotebook as nb
import plug
import edmc_data
from config import appname
from config import config as edmc_config

### модули плагина ###
from modules import (
    bgs,
    canonn_api,
    codex,
    friendfoe as FF,
    legacy,
    patrol,
    release,
    visualizer,
)
from modules.debug import Debug
from modules.lib import http
from modules.lib import context as contextlib
from modules.lib import journal, thread
from modules.release import Release
from modules.systems import SystemsModule
from modules.notifier import Notifier
import settings

_ = functools.partial(l10n.Translations.translate, context=__file__)

plugin_name = os.path.basename(os.path.dirname(__file__))

logger = logging.getLogger(f'{appname}.{plugin_name}')
if not logger.hasHandlers():
    level = logging.INFO
    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)


# хранилище данных плагина
context = contextlib.global_context
# алиас для совместимости с легаси кодом
this = context

this.log = logger

this.nearloc = {
    "Latitude": None,
    "Longitude": None,
    "Altitude": None,
    "Heading": None,
    "Time": None,
}


myPlugin = "EDMC-Triumvirate"

this.version = Version(settings.version)
this.SQNag = 0
this.client_version = "{}.{}".format(myPlugin, this.version)
this.body = None
this.body_name = None
this.systemAddress = None
this.odyssey = None
this.odyssey_events = settings.odyssey_events
this.pending_jump_system = None

this.SysFactionState = None
this.DistFromStarLS = None
this.SysFactionAllegiance = None  # variable for allegiance of
# controlling faction
this.Nag = 0
this.cmdr_SQID = None  # variable for allegiance check
this.CMDR = None
this.SQ = None
this.SRVmode, this.Fightermode = False, False
this.old_time = 0
this.fuel = 0
this.fuel_cons = 0.0
context.help_page_opened = False
context.latest_dashboard_entry = None


# фикс для старой ошибки конфига на линуксе
edmc_config.delete("Triumvirate.Canonn:HideCodex", suppress=True)
edmc_config.delete("Triumvirate.Canonn", suppress=True)


def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    # context.by_class(news.CECNews).draw_settings(frame, cmdr, is_beta, 1)
    context.by_class(release.Release).draw_settings(frame, cmdr, is_beta, 1)
    context.by_class(patrol.PatrolModule).draw_settings(frame, cmdr, is_beta, 2)
    Debug.plugin_prefs(frame, cmdr, is_beta, 3)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta, 4)
    context.by_class(bgs.BGS).draw_settings(frame, cmdr, is_beta, 5)
    context.by_class(visualizer.Visualizer).draw_settings(frame, cmdr, is_beta, 6)
    nb.Label(frame, text=settings.support_message,).grid(row=8, column=0, sticky="NW")

    return frame


def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    for mod in context.modules:
        mod.on_settings_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    Debug.prefs_changed()


def Alegiance_get(CMDR, SQ_old):
    SQ = this.cmdr_SQID
    if CMDR != this.CMDR:
        logger.debug("Community Check started")
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTXE8HCavThmJt1Wshy3GyF2ZJ-264SbNRVucsPUe2rbEgpm-e3tqsX-8K2mwsG4ozBj6qUyOOd4RMe/pub?gid=1832580214&single=true&output=tsv"
        with closing(requests.get(url, stream=True)) as r:
            try:
                reader = csv.reader(r.content.splitlines(),
                                    delimiter='\t')  # .decode('utf-8')
                next(reader)
            except:
                reader = csv.reader(r.content.decode(
                    'utf-8').splitlines(), delimiter='\t')
                next(reader)

            for row in reader:
                cmdr, squadron, SQID = row

                if cmdr == CMDR:
                    try:
                        SQ = SQID
                        logger.debug(f"your SQID is {SQ}")
                    except:
                        logger.debug("Set SQID Failed")

        if SQ != None:
            logger.debug("SQ ID IS OK")
            this.CMDR = CMDR
            this.patrol.sqid = SQ  # Функция для отправки данных о
            # сквадроне в модули, использовать как
            # шаблон
            return SQ
        else:
            if this.Nag == 0:
                logger.debug("SQID need to be instaled")
                url = "https://docs.google.com/forms/d/e/1FAIpQLSeERKxF6DlrQ3bMqFdceycSlBV0kwkzziIhYD0ctDzrytm8ug/viewform?usp=pp_url"
                url += "&entry.42820869=" + quote_plus(CMDR)
                this.Nag = this.Nag + 1
                logger.debug(f"SQID {url}")
                webbrowser.open(url)
    else:
        return SQ_old


def plugin_start3(plugin_dir):
    """
    EDMC вызывает эту функцию при первом запуске плагина (Python 3).
    """
    this.plugin_dir = plugin_dir
    Debug.setup(logger)
    this.journal_entry_processor = JournalEntryProcessor()
    this.journal_entry_processor.start()
    # префикс логов
    codex.CodexTypes.plugin_start(plugin_dir)
    # в логах пишется с префиксом Triumvirate
    logger.info(f"Plugin (v{this.version}) loaded successfully.")
    return f"Triumvirate-{this.version}"



def plugin_start(plugin_dir):
    """
    EDMC вызывает эту функцию при первом запуске плагина в режиме Python 2.
    """
    raise EnvironmentError("Плагин несовместим с версиями EDMC младше 3.50 beta0.")


def plugin_stop():
    """
    EDMC is closing
    """
    logger.debug("Stopping the plugin")
    for mod in context.modules:
        mod.on_close()
    thread.Thread.stop_all()


def kill_notification():
    this.wrongEDMCBanner.destroy()
    this.wrongEDMCBannerInstructions.destroy()
    this.hyperlink.destroy()
    this.button.destroy()


def plugin_app(parent):
    this.parent = parent

    frame = tk.Frame(parent)
    frame.grid_columnconfigure(0, weight=1)

    # TODO: перейти на использование списка модулей из ModuleMeta
    this.visualizer = visualizer.Visualizer(frame, 0)
    this.codexcontrol = codex.CodexTypes(frame, 1)
    this.systems_module = SystemsModule()
    this.canonn_rt_api = canonn_api.CanonnRealtimeAPI()
    rel = release.Release(this.plugin_dir, frame, this.version, 2)
    this.patrol = patrol.PatrolModule(frame, 3)
    this.bgs_module = bgs.BGS()
    this.modules = [
        rel,
        this.patrol,
        this.systems_module,
        this.bgs_module,
        this.canonn_rt_api,
        this.visualizer
    ]

    # фрейм с различными уведомлениями из модулей
    this.notifier = Notifier(frame, row=4)

    for mod in context.modules:
        mod.on_start(context.plugin_dir)
    
    return frame


def Squadronsend(CMDR, entry):
    if this.SQNag == 0:
        logger.debug("SQName need to be sended")
        url = "https://docs.google.com/forms/d/e/1FAIpQLScZvs3MB2AK6pPwFoSCpdaarfAeu_P-ineIhtO1mOPgr09q8A/formResponse?usp=pp_url"
        url += "&entry.558317192=" + quote_plus(CMDR)
        url += "&entry.1042067605=" + quote_plus(entry)
        this.SQNag = this.Nag + 1

        legacy.Reporter(url).start()


def journal_entry(cmdr, is_beta, system, station, entry, state):
    this.journal_entry_processor(
        cmdr, is_beta, system, station, entry, state,
        this.body_name,                 # эти три параметра обновляются через dashboard_entry и
        this.nearloc["Latitude"],       # могут измениться к моменту, как мы дойдём до обработки записи в очереди.
        this.nearloc["Longitude"]       # почему не берём body_name из state - см. https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#journal-entry
    )

class JournalEntryProcessor(thread.Thread):
    def __init__(self):
        super().__init__(name="Triumvirate journal entry processor")
        self.queue = Queue()

    def __call__(self, cmdr, is_beta, system, station, entry, state, body_name, lat, lon):
        self.queue.put((cmdr, is_beta, system, station, entry, state, body_name, lat, lon))

    def do_run(self):
        while True:
            if self.queue.empty():
                self.sleep(1)
            else:
                try:
                    self.__process_entry()
                except:
                    logger.error(traceback.format_exc())
                    # TODO: отправка логов
            
    def __process_entry(self):
        cmdr, is_beta, system, station, entry, state, body, lat, lon = self.queue.get(block = False)
        SysFactionState = this.SysFactionState,
        SysFactionAllegiance = this.SysFactionAllegiance
        DistFromStarLS = this.DistFromStarLS
        client = this.client_version

        # capture some stats when we launch
        # not read for that yet
        startup_stats(cmdr)

        # отключено, потому что API не работает, а логи засоряются
        #if entry["event"] == "Scan" and entry["ScanType"] in {"Detailed", "AutoScan"}:
            #thread.BasicThread(target=lambda: submit_expedition(cmdr, entry)).start()

        if this.odyssey == None:
            if entry["event"] == "LoadGame":        # ВАЖНО: Fileheader даёт Odyssey=true и в Горизонтах тоже
                this.odyssey = entry.get("Odyssey", False)
            # ивенты, возможные лишь в Одиссее
            elif entry["event"] in this.odyssey_events:
                this.odyssey = True
        
        if "SystemFaction" in entry:
            """ "SystemFaction": { “Name”:"Mob of Eranin", "FactionState":"CivilLiberty" } }"""
            SystemFaction = entry.get("SystemFaction")
            try:
                this.SysFactionState = SystemFaction["FactionState"]
            except:
                this.SysFactionState = None
            logger.debug("SysFaction's state is" + str(this.SysFactionState))

        if "SystemAllegiance" in entry:
            SystemAllegiance = entry.get("SystemAllegiance")
            logger.debug(SystemAllegiance)
            try:
                this.SysFactionAllegiance = SystemAllegiance
            except:
                this.SysFactionAllegiance = None
            logger.debug("SysFaction's allegiance is" + str(this.SysFactionAllegiance))

        if "DistFromStarLS" in entry:
            """"DistFromStarLS":144.821411"""
            try:
                this.DistFromStarLS = entry.get("DistFromStarLS")
            except:
                this.DistFromStarLS = None
            logger.debug("DistFromStarLS=" + str(this.DistFromStarLS))

        # иногда FSDJump приходит позже, чем нам хотелось бы, и имеющаяся у нас система не совпадает с реальной
        if (
            "SystemAddress" in entry
            and this.systemAddress != entry["SystemAddress"]
            and entry["event"] != "NavRoute"
        ):
            if entry["event"] == "StartJump":
                # мы ещё в актуальной системе, но сохраним ту, в которую прыгаем
                this.pending_jump_system = entry.get("StarSystem")
            else:
                # мы уже прыгнули, но FSDJump в логах пока не получили
                this.systemAddress = entry["SystemAddress"]
                system = this.pending_jump_system or system     # чисто на всякий случай
            
        systemAddress = this.systemAddress

        if entry.get("event") == "FSDJump":
            this.DistFromStarLS = None
            this.body = None
            this.pending_jump_system = None

        if "Body" in entry:
            this.body = entry["Body"]
            logger.debug(f"Body: {this.body}")

        if entry["event"] == "JoinedSquadron":
            Squadronsend(cmdr, entry["SquadronName"])

        x, y, z = None, None, None
        if system:
            val = this.systems_module.get_system_coords(system)
            if val is not None:
                x, y, z = val

        journal_entry = journal.JournalEntry(
            cmdr=cmdr,
            is_beta=is_beta,
            system=system,
            systemAddress=systemAddress,
            sys_faction_state=SysFactionState,
            sys_faction_allegiance=SysFactionAllegiance,
            dist_from_star=DistFromStarLS,
            station=station,
            data=entry,
            state=state,
            x=x,
            y=y,
            z=z,
            body=body,
            lat=lat,
            lon=lon,
            client=client,
        )
        status_message = None
        if journal_entry.data["event"] in {"SendText", "ReceiveText"}:
            for mod in context.enabled_modules:
                # TODO переписать на менеджер контекста?
                try:
                    val = mod.on_chat_message(journal_entry)
                except:
                    logger.error(f"Error while sending chat message to module {mod}", exc_info=1)
                    # TODO: отправка логов
                status_message = status_message or val
        else:
            for mod in context.enabled_modules:
                try:
                    val = mod.on_journal_entry(journal_entry)
                except:
                    event = entry["event"]
                    logger.error(f"Error while processing a {event} event in module {mod}", exc_info=1)
                    # TODO: отправка логов
                status_message = status_message or val
        this.codexcontrol.journal_entry(
            cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client
        )

        # legacy logging to google sheets
        legacy.GusonExpeditions(cmdr, is_beta, system, entry)
        if status_message is not None:
            this.notifier.send(status_message)


def submit_expedition(cmdr, entry: dict):   # не работает
    resp = http.WebClient(
        settings.cec_url
    ).post("/api/expeditions/v1/scan/submit", json={
        "cmdr": cmdr,
        "log": entry
    })
    if not resp.ok:
        logger.error("Ошибка при запросе к %s:\n%s", resp.request.url, resp.text)


def startup_stats(cmdr):
    try:
        this.first_event
    except:
        this.first_event = True

        addr = requests.get('https://api.ipify.org').text
        try:
            addr6 = requests.get('https://api6.ipify.org').text
        except:
            addr6 = addr
        url="https://docs.google.com/forms/d/1h7LG5dEi07ymJCwp9Uqf_1phbRnhk1R3np7uBEllT-Y/formResponse?usp=pp_url"
        url+="&entry.1181808218="+quote_plus(cmdr)
        url+="&entry.254549730="+quote_plus(str(this.version))
        url+="&entry.1622540328="+quote_plus(addr)
        if addr6 != addr:
            url+="&entry.488844173="+quote_plus(addr6)
        else:
            url+="&entry.488844173="+quote_plus("0")
        url+="&entry.1210213202="+str(Release.get_auto())

        legacy.Reporter(url).start()


def fuel_consumption(entry, old_fuel, old_timestamp, old_fuel_cons):
    # debug(old_timestamp==entry["timestamp"])
    if entry["timestamp"] != old_timestamp and old_fuel != 0:
        try:
            fuel_cons = (
                (old_fuel["FuelMain"] + old_fuel["FuelReservoir"])
                - (entry["Fuel"]["FuelMain"] + entry["Fuel"]["FuelReservoir"])
            ) / float(
                (
                    datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                    - old_timestamp
                ).total_seconds()
            )
        except ZeroDivisionError:
            return old_fuel_cons
        # debug("Fuel consumption is
        # "+str(fuel_cons))
        return fuel_cons
    else:
        # debug("Can't calculate fuel
        # consumption")
        return old_fuel_cons


this.FuelCount = 9
this.plug_start = False


def dashboard_entry(cmdr, is_beta, entry):
    context.latest_dashboard_entry = entry
    if this.plug_start == 0:
        this.plug_start = 1
        this.old_time = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    try:
        # logger.debug(f"Checking fuel consumption {this.FuelCount}")
        if entry.get("Fuel") is not None:
            if this.FuelCount == 10:
                this.fuel_cons = fuel_consumption(
                    entry, this.fuel, this.old_time, this.fuel_cons
                )
                this.old_time = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                this.fuel = entry["Fuel"]
                this.FuelCount = 0
            else:
                this.FuelCount += 1
    except NameError:
        # debug("Can't check fuel
        # consumption, waiting for
        # data")
        this.fuel_cons = 0

    # debug("Dashboard update
    # "+str(entry["Fuel"]))

    this.landed = bool(entry["Flags"] & edmc_data.FlagsLanded)
    this.inSupercruise = bool(entry["Flags"] & edmc_data.FlagsSupercruise)
    this.onSRV = bool(entry["Flags"] & edmc_data.FlagsInSRV)
    this.onFighter = bool(entry["Flags"] & edmc_data.FlagsInFighter)
    this.onFoot = bool(entry.get("Flags2", 0) & edmc_data.Flags2OnFoot)
    this.onSurface = this.landed or this.SRVmode or this.onFoot
    # print 'LatLon =
    # {}'.format(entry['Flags'] &
    # 1<<21 and True or False)
    # print entry
    if entry["Flags"] & edmc_data.FlagsHasLatLong:
        if "Latitude" in entry:
            this.nearloc["Latitude"] = entry["Latitude"]
            this.nearloc["Longitude"] = entry["Longitude"]
    else:
        this.nearloc["Latitude"] = None
        this.nearloc["Longitude"] = None
    if entry.get("BodyName"):
        this.body_name = entry.get("BodyName")
    else:
        this.body_name = None
    this.cmdr_SQID = Alegiance_get(cmdr, this.cmdr_SQID)
    # logger.debug(this.body_name)

    for mod in context.enabled_modules:
        try:
            mod.on_dashboard_entry(cmdr, is_beta, entry)
        except:
            logger.error(f"Error while sending a dashboard entry to module {mod}", exc_info=1)


def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    for mod in context.enabled_modules:
        mod.on_cmdr_data(data, is_beta)