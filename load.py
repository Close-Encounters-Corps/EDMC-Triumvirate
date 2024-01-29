# -*- coding: utf-8 -*-
import csv
import functools
import tkinter as tk
from datetime import datetime
from urllib.parse import quote_plus
from contextlib import closing
import os
import logging
import webbrowser

### third-party модули ###
import requests

### модули EDMC ###
import l10n
import myNotebook as nb
import plug
from config import appname

### модули плагина ###
from modules import clientreport, codex, factionkill
from modules import friendfoe as FF
from modules import (
    fssreports,
    hdreport,
    journaldata,
    legacy,
    message_label,
    patrol,
    release
)
from modules.debug import Debug
from modules.lib import canonn_api, http
from modules.lib import context as contextlib
from modules.lib import journal, thread
from modules.player import Player
from modules.release import Release
from modules.systems import SystemsModule
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

this.version = settings.version
this.SQNag = 0
this.client_version = "{}.{}".format(myPlugin, this.version)
this.body = None
this.body_name = None

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
    hdreport.HDInspector(frame, cmdr, is_beta, this.client_version, 6)
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
    global SQ
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
    Debug.setup(logger)
    this.plugin_dir = plugin_dir
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
    legacy.bgs.stop()
    for mod in context.modules:
        mod.close()
    thread.Thread.stop_all()


def kill_notification():
    this.wrongEDMCBanner.destroy()
    this.wrongEDMCBannerInstructions.destroy()
    this.hyperlink.destroy()
    this.button.destroy()


def plugin_app(parent):
    this.parent = parent

    frame = this.frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)

    rows = tk.Frame(frame)
    rows.grid_columnconfigure(1, weight=1)
    rows.grid(sticky="NSEW")


    table = tk.Frame(rows)
    table.columnconfigure(2, weight=1)
    table.grid(sticky="NSEW")
    this.codexcontrol = codex.CodexTypes(table, 0)
    this.systems_module = SystemsModule()
    this.canonn_rt_api = canonn_api.CanonnRealtimeApi()
    rel = release.Release(this.plugin_dir, table, this.version, 1)
    this.patrol = patrol.PatrolModule(table, 2)
    this.modules = [
        rel,
        this.patrol,
        this.systems_module,
        clientreport.ClientReportModule()
    ]
    this.hyperdiction = hdreport.hyperdictionDetector.setup(table, 4)
    # лейбл, в котором содержится текст из вывода модулей
    this.message_label = message_label.MessageLabel(rows, row=5)
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
    # capture some stats when we launch
    # not read for that yet
    startup_stats(cmdr)

    if entry["event"] == "Scan" and entry["ScanType"] in {"Detailed", "AutoScan"}:
        thread.BasicThread(target=lambda: submit_expedition(cmdr, entry)).start()

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

    if entry.get("event") == "FSDJump":
        this.DistFromStarLS = None
        this.body = None

    if "Body" in entry:
        this.body = entry["Body"]
        logger.debug(f"Body: {this.body}")

    if entry["event"] == "JoinedSquadron":
        Squadronsend(cmdr, entry["SquadronName"])

    thread.BasicThread(
        target=lambda: journal_entry_wrapper(
            cmdr,
            is_beta,
            system,
            this.SysFactionState,
            this.SysFactionAllegiance,
            this.DistFromStarLS,
            station,
            entry,
            state,
            this.body_name,
            this.nearloc["Latitude"],
            this.nearloc["Longitude"],
            this.client_version,
        )
    ).start()

def submit_expedition(cmdr, entry: dict):
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
        url+="&entry.254549730="+quote_plus(this.version)
        url+="&entry.1622540328="+quote_plus(addr)
        if addr6 != addr:
            url+="&entry.488844173="+quote_plus(addr6)
        else:
            url+="&entry.488844173="+quote_plus("0")
        url+="&entry.1210213202="+str(Release.get_auto())

        legacy.Reporter(url).start()

def journal_entry_wrapper(
    cmdr,
    is_beta,
    system,
    SysFactionState,
    SysFactionAllegiance,
    DistFromStarLS,
    station,
    entry,
    state,
    body,
    lat,
    lon,
    client
):
    """
    Detect journal events
    """
    x, y, z = None, None, None
    if system:
        val = this.systems_module.get_system_coords(system)
        if val is not None:
            x, y, z = val

    journal_entry = journal.JournalEntry(
        cmdr=cmdr,
        is_beta=is_beta,
        system=system,
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
    factionkill.submit(cmdr, is_beta, system, station, entry, client)
    hdreport.submit(cmdr, is_beta, system, station, entry, client)
    codex.submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    fssreports.submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    journaldata.submit(cmdr, is_beta, system, station, entry, client, body, lat, lon)
    if journal_entry.data["event"] in {"SendText", "ReceiveText"}:
        for mod in context.enabled_modules:
            # TODO переписать на менеджер контекста?
            try:
                val = mod.on_chat_message(journal_entry)
            except:
                logger.error(f"Error while sending chat message to module {mod}", exc_info=1)
            status_message = status_message or val
    else:
        for mod in context.enabled_modules:
            val = mod.on_journal_entry(journal_entry)
            status_message = status_message or val
    this.codexcontrol.journal_entry(
        cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client
    )
    codex.saaScan.journal_entry(
        cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client
    )

    # legacy logging to google sheets
    legacy.statistics(cmdr, is_beta, system, station, entry, state)
    legacy.CodexEntry(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    legacy.AXZone(cmdr, is_beta, system, x, y, z, station, entry, state)
    legacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    legacy.NHSS.submit(cmdr, is_beta, system, x, y, z, station, entry, client)
    legacy.bgs.process_entry(cmdr, system, station, entry)
    legacy.GusonExpeditions(cmdr, is_beta, system, entry)
    if status_message is not None:
        this.message_label.text = status_message

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

    this.landed = entry["Flags"] & 1 << 1 and True or False
    this.SCmode = entry["Flags"] & 1 << 4 and True or False
    this.SRVmode = entry["Flags"] & 1 << 26 and True or False
    this.Fightermode = entry["Flags"] & 1 << 25 and True or False
    this.landed = this.landed or this.SRVmode
    # print 'LatLon =
    # {}'.format(entry['Flags'] &
    # 1<<21 and True or False)
    # print entry
    if entry["Flags"] & 1 << 21 and True or False:
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

def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    for mod in context.enabled_modules:
        mod.on_cmdr_data(data, is_beta)