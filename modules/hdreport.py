﻿import glob
import json
import math
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import Button, Frame
from urllib.parse import quote_plus

import requests

import modules.emitter
from .lib.conf import config
#from config import config
from modules.emitter import Emitter

from .debug import Debug, debug, error
from .lib.context import global_context


'''

We want to record the system where the user was last hyperdicted
Ths is in the statistics event which appears every time the user
returns from the main menu.    

'''


class gSubmitHD(threading.Thread):
    def __init__(self, cmdr, x, y, z, entry):
        threading.Thread.__init__(self)
        self.cmdr = quote_plus(cmdr.encode('utf8'))
        self.system = quote_plus(entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM").encode('utf8'))
        self.x = x
        self.y = y
        self.z = z
        ts = entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP")
        year = int(ts[0:4]) - 1286
        self.eddatetime = "{}-{}:00".format(year, ts[4:])
        debug(self.eddatetime)

        self.entry = entry

    def run(self):
        debug("sending gSubmitCodex")
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitHD?cmdrName={}".format(self.cmdr)
        url = url + "&systemName={}".format(self.system)
        url = url + "&x={}".format(self.x)
        url = url + "&y={}".format(self.y)
        url = url + "&z={}".format(self.z)
        url = url + "&z={}".format(self.eddatetime)

        r = requests.get(url)

        if not r.status_code == requests.codes.ok:
            error("gSubmitHD {} ".format(url))
            error(r.status_code)
            error(r.json())


class HDReport(Emitter):
    hdsystems = {}

    def __init__(self, cmdr, is_beta, system, entry, client):
        Emitter.__init__(self, cmdr, is_beta, system, None, None, None, entry, None, None, None, client)
        self.system = system
        self.cmdr = cmdr
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client = client
        self.modelreport = "hdreports"

    def setPayload(self):
        payload = {}
        payload["fromSystemName"] = self.entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
        payload["cmdrName"] = self.cmdr
        payload["isbeta"] = self.is_beta
        payload["clientVersion"] = self.client
        payload["reportStatus"] = "accepted"
        payload["reportComment"] = "Hyperdiction from TG_ENCOUNTERS"
        payload["hdRawJson"] = self.entry.get("TG_ENCOUNTERS")

        return payload

    def excludesystems(self):
        url = self.getUrl()
        if not HDReport.hdsystems:
            debug("getting old hdsystems")
            r = requests.get(
                "{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=100".format(url, self.modelreport, self.cmdr))
            for hd in r.json():
                debug("excluding: {}".format(hd.get("fromSystemName")))
                HDReport.hdsystems[hd.get("fromSystemName")] = hd.get("fromSystemName")

    # going to overload run so that we can check for the last hdsystem
    def run(self):
        url = self.getUrl()

        self.excludesystems()
        # if not HDReport.hdsystems:
        # debug("getting old hdsystems")
        # r = requests.get("{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=2000".format(url,self.modelreport,self.cmdr))
        # for hd in r.json():
        # debug("excluding: {}".format(hd.get("fromSystemName")))
        # HDReport.hdsystems[hd.get("fromSystemName")]=hd.get("fromSystemName")

        lasthd = self.entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
        if lasthd:
            if HDReport.hdsystems.get(lasthd):
                debug("Hyperdiction already recorded here - server")
            else:
                HDReport.hdsystems[lasthd] = lasthd
                payload = self.setPayload()
                self.send(payload, url)


class HDScanner(threading.Thread):

    def __init__(self, process):
        threading.Thread.__init__(self)
        self.process = process

    def run(self):
        self.process()


class HDInspector(Frame):

    def __init__(self, parent, cmdr, is_beta, client, gridrow):
        "Initialise the ``Patrol``."
        Frame.__init__(
            self,
            parent
        )
        self.client = client
        self.commander = cmdr
        self.is_beta = is_beta
        self.grid(row=gridrow, column=0)
        self.button = Button(self, text="Нажмите, чтобы просканировать журнал на предмет гиперперехватов")
        self.button.bind('<Button-1>', self.run)
        self.button.grid(row=0, column=0)
        Emitter.setRoute(is_beta, client)

    def getUrl(self):
        if self.is_beta:
            url = Emitter.urls.get("staging")
        else:
            url = Emitter.route
        return url

    def excludesystems(self):
        url = self.getUrl()
        if not HDReport.hdsystems:
            debug("getting old hdsystems")
            r = requests.get(
                "{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=100".format(url, "hdreports", self.commander))
            for hd in r.json():
                debug("excluding: {}".format(hd.get("fromSystemName")))
                HDReport.hdsystems[hd.get("fromSystemName")] = hd.get("fromSystemName")

    def run(self, event):
        self.button.grid_remove()
        HDScanner(self.scan_journals).start()

    def set_beta(self, entry):
        if entry.get("event") == "Fileheader":
            if "beta" in entry.get("gameversion").lower():
                self.is_beta = True
            else:
                self.is_beta = False

    def set_commander(self, entry):
        if entry.get("event") == "Commander":
            self.commander = entry.get("Name")

    def detect_hyperdiction(self, entry):
        if entry.get("event") == "Statistics":
            debug("Detected Statistick evevnt")
            submit(self.commander, self.is_beta, None, None, entry, self.client)
            time.sleep(0.1)
        # else:
        # debug(entry.get("event"))

    def scan_file(self, filename):
        debug("Scaning file {} for HDs".format(filename))
        with open(filename) as f:
            for line in f:
                entry = json.loads(line)
                self.set_beta(entry)
                self.set_commander(entry)
                self.detect_hyperdiction(entry)

    def scan_journals(self):
        self.excludesystems()
        config.default_journal_dir
        for filename in glob.glob(os.path.join(config.default_journal_dir, 'journal*.log')):
            self.scan_file(filename)


class hyperdictionDetector():
    state = 0
    target_system = ""



    @classmethod
    def show(cls):
        cls.frame.grid()
        cls.frame.after(120000, cls.hide)

    @classmethod
    def setup(cls, parent, gridrow):
        cls.frame = tk.Frame(parent)
        cls.frame.grid(row=gridrow)
        cls.container = tk.Frame(cls.frame)
        cls.container.columnconfigure(1, weight=1)
        cls.container.grid(row=1)
        cls.banner = tk.Label(cls.container, text="ГИПЕРПЕРЕХВАТ", fg="red")
        cls.banner.grid(row=0, column=0, columnspan=1, sticky="NSEW")
        cls.banner.config(font=("Arial Black", 22))
        cls.instructions = tk.Label(cls.container, text="Пожалуйста, выйдите в главное меню и зайдите для подтверждения", fg="red")
        cls.instructions.grid(row=1, column=0, columnspan=1, sticky="NSEW")
        cls.instructions.config(font=("Arial Black", 8))
        cls.hide()
        return cls.frame

    @classmethod
    def startJump(cls, target_system):
        debug("startJump setting state 1 {}".format(target_system))
        cls.hide()
        cls.state = 1
        cls.target_system = target_system
    
    @classmethod
    def hide(cls):
        cls.frame.grid_remove()

    @classmethod
    def FSDJump(cls, system):
        if cls.state == 1 and not system == cls.target_system:
            debug("FSDJump setting state 2 {} {}".format(system, cls.target_system))
            cls.state = 2;
        else:
            debug("FSDJUMP resetting state back {} {}".format(system, cls.target_system))
            cls.state = 0

    @classmethod
    def Music(cls, system, cmdr, timestamp):
        if cls.state == 2:
            debug("Hyperdiction Detected")
            cls.show()
            # TODO check for None
            x, y, z = global_context.systems_module.get_system(system)
            modules.emitter.post("https://europe-west1-canonn-api-236217.cloudfunctions.net/postHDDetected",
                                {"cmdr": cmdr, "system": system, "timestamp": timestamp, "x": x, "y": y, "z": z})
            plug.show_error("Hyperdiction: Exit to main menu")
        else:
            debug("FSDJUMP resetting state back")
            cls.hide()
            cls.state == 0

    @classmethod
    def SupercruiseExit(cls):
        cls.hide()
        state = 0

    @classmethod
    def submit(cls, cmdr, is_beta, system, station, entry, client):
        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            cls.startJump(entry.get("StarSystem"))

        if entry.get("event") == "FSDJump":
            cls.FSDJump(entry.get("StarSystem"))

        if entry.get("event") == "Music" and entry.get("MusicTrack") in ("Unknown_Encounter"):
            cls.Music(system, cmdr, entry.get("timestamp"))

        if entry.get("event") == "SupercruiseExit":
            cls.SupercruiseExit()


def post_traffic(system, entry):
    debug("posting traffic {} ".format(system))
    try:
        modules.emitter.post("https://europe-west1-canonn-api-236217.cloudfunctions.net/postTraffic",
                            {"system": system, "timestamp": entry.get("timestamp")})
    except:
        plug.show_error("Failed to post traffic")
        debug("Failed to post traffic for {}".format(system))


def get_distance(a, b):
    x, y, z = global_context.systems_module.get_system_coords(a)
    a, b, c = global_context.systems_module.get_system_coords(b)
    return math.sqrt(math.pow(x - a, 2) + math.pow(y - b, 2) + math.pow(z - c, 2))


def post_distance(system, centre, entry):
    d = int(get_distance(system, centre) / 10) * 10
    debug("distance {}".format(d))
    if d <= 250:
        tag = "{} ({})".format(centre, int(d))
        post_traffic(tag, entry)


def submit(cmdr, is_beta, system, station, entry, client):
    hyperdictionDetector.submit(cmdr, is_beta, system, station, entry, client)

    hdsystems = (
    "Electra", "Asterope", "Delphi", "Merope", "Celaeno", "Maia", "HR 1185", "HIP 23759", "Witch Head Sector DL-Y d17",
    "Pleiades Sector HR-W d1-79", "Pleione", "Witch Head Sector GW-W c1-4")

    if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
        # post traffic from reference systems
        if system in hdsystems:
            post_traffic(system, entry)

        post_distance(system, 'Merope', entry)
        post_distance(system, 'Witch Head Sector IR-W c1-9', entry)

    if entry["event"] == "Statistics" and entry.get("TG_ENCOUNTERS"):
        # there is no guarentee TG_ENCOUNTER_TOTAL_LAST_SYSTEM will have a value
        if entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):

            lastsystem = entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
            gametime = entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP")
            year, remainder = gametime.split("-", 1)
            tgtime = "{}-{}".format(str(int(year) - 1286), remainder)

            if lastsystem == "Pleiades Sector IR-W d1-55":
                lastsystem = "Delphi"

            debug({"cmdr": cmdr, "system": lastsystem, "timestamp": tgtime})
            x, y, z = global_context.systems_module.get_system_coords(lastsystem)
            # we are going to submit the hyperdiction here.
            modules.emitter.post("https://europe-west1-canonn-api-236217.cloudfunctions.net/postHD",
                                {"cmdr": cmdr, "system": lastsystem, "timestamp": tgtime, "x": x, "y": y, "z": z})

            if lastsystem:
                if HDReport.hdsystems.get(lastsystem) == lastsystem:
                    debug("Hyperdiction already recorded here - session ")
                else:
                    HDReport(cmdr, is_beta, lastsystem, entry, client).start()
                    gSubmitHD(cmdr, x, y, z, entry).start()
