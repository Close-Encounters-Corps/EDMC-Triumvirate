# -*- coding: utf-8 -*-
"""
Модуль патруля. Отвечает за отображение информации о системе
и о ближайших интересных системах на основании EDSM и данных из логов.

Как примерно работает:

При первой записи из журнала (с данными о системе), при первых данных о командире
или при изменении настроек начинает периодически выкачиваться база POI EDMC
и обновляться соответствующие поля.

Фоновый поток обновления может быть остановлен, если в настройках отключить
все галочки патруля.
"""

import csv
import json
import math
import os
import re
import threading
import time
import tkinter as tk
import uuid
from contextlib import closing
from datetime import datetime
from tkinter import Frame
from urllib.parse import quote_plus

import requests

import myNotebook as nb
from l10n import Locale
from ttkHyperlinkLabel import HyperlinkLabel
import settings
from settings import ships, states

from .canonn import CanonnPatrols
from .patrol import build_patrol
from .edsm import get_edsm_patrol
from .bgs import BGSTasksOverride, new_bgs_patrol
from .. import legacy
from ..debug import debug as debug_base, error
from ..lib.conf import config
from ..lib.context import global_context
from ..lib.thread import Thread
from ..lib.journal import JournalEntry
from ..lib.spreadsheet import Spreadsheet
from ..lib.module import Module
from ..release import Release
from ..systems import Systems

# CYCLE = 60 * 1000 * 60  # 60 minutes
CYCLE = 60 * 1000  # 1 minute

DEFAULT_URL = ""
WRAP_LENGTH = 200


def debug(msg, *args):
    debug_base(f"[patrol] {msg}", *args)


def get_ship_type(key):
    key = key.lower()
    debug("Looking for ship '{}'", key)
    name = ships.get(key)
    return name if name else key


class UpdateThread(Thread):
    def __init__(self, widget):
        Thread.__init__(self)
        self.widget = widget

    def run(self):
        # download cannot contain any
        # tkinter changes
        while not self.STOP:
            self.widget.download()
            time.sleep(CYCLE / 1000)
        debug("Background thread stopped.")


def get(list, index):
    try:
        return list[index]
    except IndexError:
        return None


class PatrolLink(HyperlinkLabel):
    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Получение патруля",
            url=DEFAULT_URL,
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


class InfoLink(HyperlinkLabel):
    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Получение патруля",
            url=DEFAULT_URL,
            popup_copy=True,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW,
        )
        self.resized = False
        self.bind("<Configure>", self.__configure_event)

    def __reset(self):
        self.resized = False

    def __configure_event(self, event):
        "Handle resizing."

        if not self.resized:
            self.resized = True
            self.configure(wraplength=event.width)
            self.after(500, self.__reset)


class PatrolModule(Frame, Module):
    def __init__(self, parent, gridrow):
        super().__init__(parent)

        sticky = tk.EW + tk.N  # full width, stuck to the top

        self.ships = []
        self.bind("<<PatrolDone>>", self.update_ui)
        plugin_dir = global_context.plugin_dir
        self.IMG_PREV = tk.PhotoImage(
            file=os.path.join(plugin_dir, "icons", "left_arrow.gif")
        )
        self.IMG_NEXT = tk.PhotoImage(
            file=os.path.join(plugin_dir, "icons", "right_arrow.gif")
        )

        self.patrol_config = os.path.join(plugin_dir, "data", "EDMC-Triumvirate.patrol")

        self.canonnbtn = tk.IntVar(value=config.getint("HidePatrol"))
        self.factionbtn = tk.IntVar(value=config.getint("Hidefactions"))
        self.hideshipsbtn = tk.IntVar(value=config.getint("HideMyShips"))
        self.edsmbtn = tk.IntVar(value=config.getint("HideEDSM"))
        self.copypatrolbtn = tk.IntVar(value=config.getint("CopyPatrolAdr"))

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.HideMyShips = self.hideshipsbtn.get()
        self.CopyPatrolAdr = self.copypatrolbtn.get()
        self.edsm = self.edsmbtn.get()

        self.columnconfigure(1, weight=1)
        self.columnconfigure(4, weight=4)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        ## Text Instructions for the
        ## patrol
        self.label = tk.Label(self, text="Патруль:")
        self.label.grid(row=0, column=0, sticky=sticky)

        self.hyperlink = PatrolLink(self)
        self.hyperlink.grid(row=0, column=2)
        self.distance = tk.Label(self, text="...")
        self.distance.grid(row=0, column=3, sticky="NSEW")
        self.distance.grid_remove()

        ## Text Instructions for the
        ## patrol
        self.infolink = InfoLink(self)
        self.infolink.grid(row=1, column=0, sticky="NSEW", columnspan=5)
        self.infolink.grid_remove()

        # buttons for the patrol
        self.prev = tk.Button(
            self, text="Prev", image=self.IMG_PREV, width=14, height=14, borderwidth=0
        )
        # self.submit=tk.Button(self, text="Open")
        self.next = tk.Button(
            self, text="Next", image=self.IMG_NEXT, width=14, height=14, borderwidth=0
        )
        self.prev.grid(row=0, column=1, sticky="W")

        # self.submit.grid(row = 2, column = 1,sticky="NSW")
        self.next.grid(row=0, column=4, sticky="E")
        self.next.bind("<Button-1>", self.next_patrol)
        self.prev.bind("<Button-1>", self.prev_patrol)

        self.prev.grid_remove()
        self.next.grid_remove()

        self.excluded = {}

        self.patrol_name = None
        self.patrol_list = []
        self.capi_update = False
        self.patrol_count = 0
        self.patrol_pos = 0
        self.minutes = 0
        self.isvisible = False
        self.update_visibility()
        self.cmdr = ""
        self.nearest = {}

        self.system = ""

        self.body = ""
        self.lat = ""
        self.lon = ""

        self.started = False

        self._SQID = None  # Переменная для хранения информации об
        # сквадроне пилота
        self.sqid_evt = threading.Event()
        self.update_thread = None

        self.bind("<<PatrolDisplay>>", self.update_desc)

    def on_start(self, plugin_dir):
        pass

    def start_background_thread(self):
        if self.enabled and not self.update_thread:
            self.update_thread = UpdateThread(self)
            self.update_thread.start()
            self.started = True


    def update_desc(self, event):
        self.hyperlink["text"] = "Fetching {}".format(self.patrol_name)
        self.hyperlink["url"] = None

    def patrol_update(self):
        """Периодически скачивает в фоне новые данные."""
        self.start_background_thread()

    def next_patrol(self, event):
        """
        When the user clicks next it will hide the current patrol for the duration of the session
        It does this by setting an excluded flag on the patrl list
        """
        # if it the last patrol lets not
        # go any further.
        index = self.nearest.get("index")
        if index + 1 < len(self.patrol_list):
            debug("len {} ind {}", len(self.patrol_list), index)
            self.nearest["excluded"] = True
            self.patrol_list[index]["excluded"] = True
            self.update()
            if self.CopyPatrolAdr == 1:
                copyclip(self.nearest.get("system"))
            # if there are excluded
            # closer then we might need
            # to deal with it
            # self.prev.grid()

    def prev_patrol(self, event):
        """
        When the user clicks next it will unhide the previous patrol
        It does this by unsetting the excluded flag on the previous patrol
        """
        index = self.nearest.get("index")
        debug("prev {}".format(index))
        if index > 0:
            self.patrol_list[index - 1]["excluded"] = False
            self.update()
            if self.CopyPatrolAdr == 1:
                copyclip(self.nearest.get("system"))

    def update_ui(self, event=None):
        # rerun every 5 seconds
        self.after(5000, self.update_ui)
        self.update()

    def update(self):
        if not self.enabled:
            return

        capi_update = self.patrol_list and self.system and self.capi_update
        journal_update = self.patrol_list and self.system

        if journal_update or capi_update:
            self.sort_patrol()
            p = Systems.edsmGetSystem(self.system)
            self.nearest = self.get_nearest(p)
            self.hyperlink["text"] = self.nearest.get("system")
            self.hyperlink[
                "url"
            ] = "https://www.edsm.net/en/system?systemName={}".format(
                quote_plus(self.nearest.get("system"))
            )

            self.distance["text"] = "{}ly".format(
                Locale.stringFromNumber(getDistance(p, self.nearest.get("coords")), 2)
            )
            self.infolink["text"] = self.nearest.get("instructions")
            url = self.nearest.get("url")
            self.infolink["url"] = self.parseurl(url) if url else ""

            self.infolink.grid()
            self.distance.grid()
            self.prev.grid()
            self.next.grid()
            self.capi_update = False

        else:
            if self.system:
                self.hyperlink["text"] = "Получение патруля..."
            else:
                self.hyperlink["text"] = "Ожидание данных о местоположении..."
            self.infolink.grid_remove()
            self.distance.grid_remove()
            self.prev.grid_remove()
            self.next.grid_remove()

    def getStates(self, state_name, bgs):
        sa = []
        active_states = bgs.get(state_name)
        if active_states:
            sa = list(active_states[0].values())

        if sa:
            states = ",".join(sa)
            return states

    def getFactionData(self, faction, BGSOSys):
        """
            We will get Canonn faction data using an undocumented elitebgs api
            NB: It is possible this could get broken so need to contact CMDR Garud
        """

        patrol = []

        url = "https://elitebgs.app/frontend/factions?name={}".format(faction)
        j = requests.get(url).json()
        if j:
            for bgs in j.get("docs")[0].get("faction_presence"):
                val = new_bgs_patrol(bgs, faction, BGSOSys)
                if val:
                    patrol.append(val)

        return patrol

    def parseurl(self, url):
        """
        We will provided some sunstitute variables for the urls
        """
        r = url.replace("{CMDR}", self.cmdr)

        r = r.replace("{LAT}", str(self.lat or ""))
        r = r.replace("{LON}", str(self.lon or ""))
        r = r.replace("{BODY}", self.body or "")

        return r

    def keyval(self, k):
        x, y, z = Systems.edsmGetSystem(self.system)
        return getDistance((x, y, z), k.get("coords"))

    def sort_patrol(self):
        patrol_list = sorted(self.patrol_list, key=self.keyval)
        for num, val in enumerate(patrol_list):
            system = val.get("system")
            type = val.get("type")

            patrol_list[num]["index"] = num

        self.patrol_list = patrol_list

    @property
    def sqid(self):
        return self._SQID

    @sqid.setter
    def sqid(self, SQ):
        self._SQID = SQ or "None"
        self.sqid_evt.set()

    def download(self):
        debug("Waiting for SQID event...")
        self.sqid_evt.wait()
        debug("Downloading patrol data...")

        # if patrol list is populated
        # then was can save
        if self.patrol_list:
            self.save_excluded()
        else:
            self.load_excluded()

        # no point if we have no idea
        # where we are
        if not self.system:
            return
        patrol_list = []
        self.bgsSystemsAndfactions = {}
        if self.faction != 1:
            debug("Getting Faction Data")
            bgsoverride = BGSTasksOverride.new(self.sqid)
            BGSO, BGSOSys = bgsoverride.patrols, bgsoverride.systems

            patrol_list.extend(BGSO)
            if self.sqid == "SCEC":
                patrol_list.extend(
                    self.getFactionData("Close Encounters Corps", BGSOSys)
                )
            elif self.sqid == "EGPU":
                patrol_list.extend(
                    self.getFactionData("EG Union", BGSOSys)
                )
            elif self.sqid == "RPSG":
                patrol_list.extend(
                    self.getFactionData("Royal Phoenix Corporation", BGSOSys)
                )
            
            while None in patrol_list:
                patrol_list.remove(None)

        if self.ships and self.HideMyShips != 1:
            patrol_list.extend(self.ships)

        if self.canonn != 1:
            self.canonnpatrol = CanonnPatrols.new()
            patrol_list.extend(self.canonnpatrol)

        if self.edsm != 1:
            patrol_list.extend(get_edsm_patrol())

        # add exclusions from configuration
        for num, val in enumerate(patrol_list):
            system = val.get("system")
            type = val.get("type")

            if self.excluded.get(type):
                if self.excluded.get(type).get(system):
                    patrol_list[num]["excluded"] = self.excluded.get(type).get(system)

        # we will sort the patrol list
        self.patrol_list = patrol_list
        self.sort_patrol()

        debug("Patrol downloaded successfully.")
        self.started = True
        # poke an evennt safely
        self.event_generate("<<PatrolDone>>", when="tail")

    def draw_settings(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.canonnbtn = tk.IntVar(value=config.getint("HidePatrol"))
        self.factionbtn = tk.IntVar(value=config.getint("Hidefactions"))
        self.hideshipsbtn = tk.IntVar(value=config.getint("HideMyShips"))
        self.edsmbtn = tk.IntVar(value=config.getint("HideEDSM"))
        self.copypatrolbtn = tk.IntVar(value=config.getint("CopyPatrolAdr"))

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.HideMyShips = self.hideshipsbtn.get()
        self.edsm = self.edsmbtn.get()
        self.CopyPatrolAdr = self.copypatrolbtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text="Настройки патруля").grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Скрыть патруль", variable=self.canonnbtn).grid(
            row=1, column=0, sticky="NW"
        )
        nb.Checkbutton(frame, text="Скрыть BGS", variable=self.factionbtn).grid(
            row=1, column=1, sticky="NW"
        )
        nb.Checkbutton(
            frame, text="Скрыть данные ваших кораблей", variable=self.hideshipsbtn
        ).grid(row=2, column=1, sticky="NW")
        nb.Checkbutton(
            frame, text="Скрыть Galactic Mapping POI", variable=self.edsmbtn
        ).grid(row=2, column=0, sticky="NW")
        nb.Checkbutton(
            frame,
            text="Автоматически копировать \nпатруль в буфер обмена",
            variable=self.copypatrolbtn,
        ).grid(
            row=3, column=0, sticky="NW",
        )

        debug(
            "canonn: {}, faction: {} hideships {}, EDSM {}".format(
                self.canonn, self.faction, self.HideMyShips, self.edsm
            )
        )

        return frame

    def update_visibility(self):
        nopatrols = (
            self.canonn == 1
            and self.faction == 1
            and self.HideMyShips == 1
            and self.edsm == 1
        )

        if nopatrols:
            self.grid_remove()
            self.isvisible = False
        else:
            self.grid()
            self.isvisible = True

    def on_settings_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set("HidePatrol", self.canonnbtn.get())
        config.set("Hidefactions", self.factionbtn.get())
        config.set("HideMyShips", self.hideshipsbtn.get())
        config.set("HideEDSM", self.edsmbtn.get())
        config.set("CopyPatrolAdr", self.copypatrolbtn.get())

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.HideMyShips = self.hideshipsbtn.get()
        self.edsm = self.edsmbtn.get()
        self.CopyPatrolAdr = self.copypatrolbtn.get()

        self.update_visibility()

        if not self.enabled and self.update_thread:
            self.update_thread.STOP = True
            self.update_thread = None
        self.start_background_thread()
        debug(
            "canonn: {}, faction: {} hideships {} hideEDSM {}".format(
                self.canonn, self.faction, self.HideMyShips, self.edsm
            )
        )

    @property
    def enabled(self):
        return self.isvisible

    def on_journal_entry(self, entry: JournalEntry):
        # We don't care what the
        # journal entry is as long as
        # the system has changed.

        self.latest_entry = entry
        self.body = entry.body
        self.lat = entry.lat
        self.lon = entry.lon
        self.x = entry.coords.x
        self.y = entry.coords.y
        self.z = entry.coords.z

        if entry.system and not self.started:
            debug("Patrol download cycle commencing")
            self.started = True
            self.patrol_update()

        if entry.cmdr:
            self.cmdr = entry.cmdr
        event = entry.data.get("event")

        if entry.body:
            self.update()

        if entry.system:
            nearest_system = self.nearest.get("system")
            same_system = (
                nearest_system.upper() == entry.system.upper()
                if nearest_system
                else False
            )
            if self.system != entry.system and event in (
                "Location",
                "FSDJump",
                "StartUp",
            ):
                debug("Refreshing Patrol ({})", event)
                self.system = entry.system
                self.update()
                if self.nearest and self.CopyPatrolAdr == 1:
                    copyclip(self.nearest.get("system"))
            # If we have visted a system and
            # then jump out then lets
            # clicknext
            if (
                self.nearest
                and same_system
                and entry.data.get("event") == "StartJump"
                and entry.data.get("JumpType") == "Hyperspace"
            ):
                self.next_patrol(None)

            # After we have done everything
            # else let's see if we can
            # automatically submit and move
            # on
            if self.nearest.get("event") and same_system:
                self.trigger(entry.system, entry.data)

    def on_cmdr_data(self, data, is_beta):
        """
        We have new data on our commander

        Lets get a list of ships
        """
        cmdr = data["commander"]
        cmdr_name = cmdr.get("name")
        if cmdr_name is None:
            return
        self.cmdr = cmdr_name

        self.ships = []
        self.system = data["lastSystem"]["name"]

        current_ship = cmdr["currentShipId"]

        shipsystems = {}

        ships = data["ships"]
        for ship in ships:
            if int(ship) == int(current_ship):
                continue

            ship_system = ships[ship]["starsystem"]["name"]
            if not shipsystems.get(ship_system):
                debug("first: {}".format(ship_system))
                shipsystems[ship_system] = []

            shipsystems[ship_system].append(data.get("ships").get(ship))

        for system, ships in shipsystems.items():
            ship_pos = Systems.edsmGetSystem(system)
            ship_count = len(ships)
            if ship_count == 1:
                ship = ships[0]
                ship_type = get_ship_type(ship.get("name"))
                ship_info = "Ваш {}, {} пристыкован(а) к {}".format(
                    ship_type, ship.get("shipName"), ship["station"].get("name")
                )
            else:
                ship_info = "У вас {} кораблей в этой системе".format(ship_count)

            self.ships.append(build_patrol("SHIPS", system, ship_pos, ship_info, None))

        self.capi_update = True
        if self.system and not self.started:
            debug("Patrol download cycle commencing")
            self.started = True
            self.patrol_update()

    def close(self):
        """
        When the plugin stops we want to save the patrols where excluded = True
        We will not inclde ships or BGS in this as they can be excluded in other ways.
        """
        self.save_excluded()

    def load_excluded(self):
        debug("loading excluded")
        self.patrol_config = os.path.join(
            Release.plugin_dir, "data", "EDMC-Triumvirate.patrol"
        )
        try:
            with open(self.patrol_config) as json_file:
                self.excluded = json.load(json_file)
        except:
            pass

    def save_excluded(self):
        self.patrol_config = os.path.join(
            Release.plugin_dir, "data", "EDMC-Triumvirate.patrol"
        )
        excluded = {}
        for patrol in self.patrol_list:
            if patrol.get("excluded") and not patrol.get("type") in ("BGS", "SHIPS"):
                if not excluded.get(patrol.get("type")):
                    excluded[patrol.get("type")] = {}
                excluded[patrol.get("type")][patrol.get("system")] = True
        with open(self.patrol_config, "w+") as outfile:
            json.dump(excluded, outfile)

    def trigger(self, system, entry):
        # exit if the events dont match

        event = json.loads(self.nearest.get("event"))
        debug("event {}".format(event))
        for key in list(event.keys()):
            if event.get(key):
                debug("event key {} value {}".format(key, event.get(key)))
                if not str(entry.get(key)).upper() == str(event.get(key)).upper():
                    return False

        debug("triggered")
        # autosubmit the form --
        # allowing for google forms
        if self.nearest.get("url"):
            j = requests.get(
                self.nearest.get("url").replace("viewform", "formResponse")
            )
        self.next_patrol(None)

    def get_nearest(self, location):
        nearest = None
        for num, patrol in enumerate(self.patrol_list):
            # add the index to the
            # patrol so we can navigate
            self.patrol_list[num]["index"] = int(num)

            if not patrol.get("excluded"):
                if nearest:
                    if getDistance(location, patrol.get("coords")) < getDistance(
                        location, nearest.get("coords")
                    ):
                        nearest = patrol
                else:
                    nearest = patrol

        return nearest


def copyclip(value):
    debug("copyclip")
    window = tk.Tk()
    window.withdraw()
    window.clipboard_clear()  # clear clipboard contents
    window.clipboard_append(value)
    debug("copyclip_append")
    window.update()
    window.destroy()
    debug("copyclip done")


def getDistance(p, g):
    # gets the distance between two systems
    return math.sqrt(sum(tuple([math.pow(p[i] - g[i], 2) for i in range(3)])))
