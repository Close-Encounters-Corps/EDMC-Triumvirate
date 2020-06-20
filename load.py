# -*- coding: utf-8 -*-
import csv
import functools
import json
import sys
import webbrowser
from contextlib import closing
from datetime import datetime

### модули EDMC ###
import l10n
import myNotebook as nb
import plug
from ttkHyperlinkLabel import HyperlinkLabel
from config import config

### third-party модули ###
import requests

### модули плагина ###
from modules import clientreport, codex, factionkill
from modules import friendfoe as FF
from modules import (
    allowlist,
    fssreports,
    hdreport,
    journaldata,
    legacy,
    materialReport,
    news,
    nhss,
    patrol,
    release,
    sos
)
from modules.debug import Debug, debug, error
from modules.player import Player
from modules.release import Release
from modules.systems import SystemsModule
from modules.lib import cmdr as cmdrlib
from modules.lib import context as contextlib
from modules.lib import thread, journal
import settings

import tkinter.ttk
import tkinter as tk
from tkinter import Frame
from urllib.parse import quote_plus

_ = functools.partial(l10n.Translations.translate, context=__file__)

# хранилище данных плагина
context = contextlib.global_context
# алиас для совместимости с легаси кодом
this = context

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
this.fuel_cons = 0
this.AllowEasternEggs = None


def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    this.AllowEasternEggsButton = tk.IntVar(value=config.getint("AllowEasterEggs"))
    this.AllowEasternEggs = this.AllowEasternEggsButton.get()
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    context.by_class(news.CECNews).draw_settings(frame, cmdr, is_beta, 1)
    context.by_class(release.Release).draw_settings(frame, cmdr, is_beta, 2)
    context.by_class(patrol.PatrolModule).draw_settings(frame, cmdr, is_beta, 3)
    Debug.plugin_prefs(frame, cmdr, is_beta, 4)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta, 5)
    nb.Checkbutton(
        frame, text="Включить пасхалки", variable=this.AllowEasternEggsButton
    ).grid(row=6, column=0, sticky="NW")
    hdreport.HDInspector(frame, cmdr, is_beta, this.client_version, 7)
    nb.Label(frame, text=settings.support_message,).grid(row=9, column=0, sticky="NW")

    return frame


def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    for mod in context.modules:
        mod.on_settings_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    config.set("AllowEasterEggs", this.AllowEasternEggsButton.get())
    this.AllowEasternEggs = this.AllowEasternEggsButton.get()

    Debug.prefs_changed()


def Alegiance_get(CMDR, SQ_old):
    if CMDR != this.CMDR:
        debug("Community Check started")
        commander = cmdrlib.find_cmdr(CMDR)
        if commander is not None:
            this.SQ = commander.sqid
        if this.SQ is not None:
            debug("SQ ID IS OK")
            this.CMDR = CMDR
            context.by_class(patrol.PatrolModule).sqid = this.SQ
            # Функция для отправки данных о
            # сквадроне в модули, использовать как
            # шаблон
            return this.SQ
        else:
            if this.Nag == 0:
                debug("SQID need to be instaled")
                url = "https://docs.google.com/forms/d/e/1FAIpQLSeERKxF6DlrQ3bMqFdceycSlBV0kwkzziIhYD0ctDzrytm8ug/viewform?usp=pp_url"
                url += "&entry.42820869=" + quote_plus(CMDR)
                this.Nag = this.Nag + 1
                debug("SQID " + str(url))
                webbrowser.open(url)
    else:
        return SQ_old


def plugin_start3(plugin_dir):
    """
    EDMC вызывает эту функцию при первом запуске плагина (Python 3).
    """
    this.plugin_dir = plugin_dir
    # префикс логов
    Debug.set_client("Triumvirate")
    codex.CodexTypes.plugin_start(plugin_dir)
    # в логах пишется с префиксом Triumvirate
    Debug.p("Plugin (v{}) loaded successfully.".format(this.version))
    return "Triumvirate-{}".format(this.version)


def plugin_start(plugin_dir):
    """
    EDMC вызывает эту функцию при первом запуске плагина в режиме Python 2.
    """
    raise EnvironmentError("Плагин несовместим с версиями EDMC младше 3.50 beta0.")


def plugin_stop():
    """
    EDMC is closing
    """
    debug("Stopping the plugin")
    for mod in context.modules:
        mod.close()
    thread.Thread.stop_all()


class EDMCLink(HyperlinkLabel):
    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Пожалуйста, поставьте EDMC версии 3.5 или выше по этой ссылке",
            url="https://github.com/Marginal/EDMarketConnector/releases",
            popup_copy=True,
            # wraplength=50, # updated
            # in __configure_event below
            anchor=tk.NW,
        )
        # self.bind('<Configure>',
        # self.__configure_event)

    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)


def kill_notification():
    this.wrongEDMCBanner.destroy()
    this.wrongEDMCBannerInstructions.destroy()
    this.hyperlink.destroy()
    this.button.destroy()


def plugin_app(parent):
    this.parent = parent

    frame = this.frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)

    table = tk.Frame(frame)
    table.columnconfigure(1, weight=1)
    table.grid(sticky="NSEW")
    this.codexcontrol = codex.CodexTypes(table, 0)
    this.systems_module = SystemsModule()
    this.modules = [
        patrol.PatrolModule(table, 3),
        sos.SosModule(),
        allowlist.AllowlistModule(parent),
        this.systems_module,
        release.Release(this.plugin_dir, table, this.version, 2),
        nhss.NHSSModule(),
        news.CECNews(table, 1)
    ]
    this.hyperdiction = hdreport.hyperdictionDetector.setup(table, 4)
    this.AllowEasterEggs = tk.IntVar(value=config.getint("AllowEasterEggs"))

    return frame


def Squadronsend(CMDR, entry):
    if this.SQNag == 0:
        debug("SQName need to be sended")
        url = "https://docs.google.com/forms/d/e/1FAIpQLScZvs3MB2AK6pPwFoSCpdaarfAeu_P-ineIhtO1mOPgr09q8A/formResponse?usp=pp_url"
        url += "&entry.558317192=" + quote_plus(CMDR)
        url += "&entry.1042067605=" + quote_plus(entry)
        this.SQNag = this.Nag + 1

        legacy.Reporter(url).start()


def journal_entry(cmdr, is_beta, system, station, entry, state):
    """

    """
    # capture some stats when we launch
    # not read for that yet
    startup_stats(cmdr)

    if "SystemFaction" in entry:
        """ "SystemFaction": { “Name”:"Mob of Eranin", "FactionState":"CivilLiberty" } }"""
        SystemFaction = entry.get("SystemFaction")
        # debug(SystemFaction)
        try:
            this.SysFactionState = SystemFaction["FactionState"]
        except:
            this.SysFactionState = None
        debug("SysFaction's state is" + str(this.SysFactionState))

    if "SystemAllegiance" in entry:

        SystemAllegiance = entry.get("SystemAllegiance")
        debug(SystemAllegiance)
        try:
            this.SysFactionAllegiance = SystemAllegiance
        except:
            this.SysFactionAllegiance = None
        debug("SysFaction's allegiance is" + str(this.SysFactionAllegiance))

    if "DistFromStarLS" in entry:
        """"DistFromStarLS":144.821411"""
        try:
            this.DistFromStarLS = entry.get("DistFromStarLS")
        except:
            this.DistFromStarLS = None
        debug("DistFromStarLS=" + str(this.DistFromStarLS))

    if entry.get("event") == "FSDJump":
        this.DistFromStarLS = None
        this.body = None

    if "Body" in entry:
        this.body = entry["Body"]
        debug("Body: {}", this.body)

    if entry["event"] == "JoinedSquadron":
        Squadronsend(cmdr, entry["SquadronName"])

    x, y, z = None, None, None
    if system:
        val = this.systems_module.get_system_coords(system)
        if val is not None:
            x, y, z = val

    return journal_entry_wrapper(
        cmdr,
        is_beta,
        system,
        this.SysFactionState,
        this.SysFactionAllegiance,
        this.DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        this.body_name,
        this.nearloc["Latitude"],
        this.nearloc["Longitude"],
        this.client_version,
    )


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
    x,
    y,
    z,
    body,
    lat,
    lon,
    client,
):
    """
    Detect journal events
    """
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
        client=client
    )
    status_message = None
    factionkill.submit(cmdr, is_beta, system, station, entry, client)
    hdreport.submit(cmdr, is_beta, system, station, entry, client)
    codex.submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    fssreports.submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    journaldata.submit(cmdr, is_beta, system, station, entry, client, body, lat, lon)
    clientreport.submit(cmdr, is_beta, client, entry)
    if journal_entry.data["event"] in {"SendText", "ReceiveText"}:
        for mod in context.enabled_modules:
            # TODO переписать на менеджер контекста?
            try:
                val = mod.on_chat_message(journal_entry)
            except Exception as e:
                error("Error while sending chat message to module {}: {}".format(
                    mod, e
                ))
            status_message = status_message or val
    else:
        for mod in context.enabled_modules:
            val = mod.on_journal_entry(journal_entry)
            status_message = status_message or val
    this.codexcontrol.journal_entry(
        cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client
    )
    materialReport.submit(
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
        station,
        entry,
        x,
        y,
        z,
        body,
        lat,
        lon,
        client,
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
    legacy.BGS().TaskCheck(cmdr, is_beta, system, station, entry, client)
    Easter_Egs(entry)
    return status_message


def Easter_Egs(entry):
    if this.AllowEasternEggs == True:
        debug("Easter Check")
        if (
            entry["event"] == "HullDamage"
            and entry["PlayerPilot"] == True
            and entry["Fighter"] == False
        ):  # and entry['PlayerPilot'] == True and entry["Fighter"] == False
            if entry["Health"] < 0.3:
                debug("plaing sound")
                Player(this.plugin_dir, ["sounds\\hullAlarm.wav"]).start()


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
    debug("Dashboard entry: {}", entry)
    if this.plug_start == 0:
        this.plug_start = 1
        this.fuel = entry["Fuel"]
        this.old_time = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")	
    try:
        debug("Checking fuel consumption " + str(this.FuelCount))
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
    debug(this.body_name)
    this.cmdr_SQID = Alegiance_get(cmdr, this.cmdr_SQID)
    # debug(this.cmdr_SQID)

def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    for mod in context.enabled_modules:
        mod.on_cmdr_data(data, is_beta)


def startup_stats(cmdr):
    try:
        this.first_event
    except:
        this.first_event = True
        auto_update = 1 if this.by_class(Release).no_auto.get() == 0 else 0
        url = "https://docs.google.com/forms/d/1h7LG5dEi07ymJCwp9Uqf_1phbRnhk1R3np7uBEllT-Y/formResponse?usp=pp_url"
        url += "&entry.1181808218=" + quote_plus(cmdr)
        url += "&entry.254549730=" + quote_plus(this.version)
        url += "&entry.1210213202=" + quote_plus(str(auto_update))

        legacy.Reporter(url).start()
