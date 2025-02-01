# -*- coding: utf-8 -*-
import myNotebook as nb
import os
import requests
import threading
import traceback
from modules.debug import debug, error
from .lib.conf import config
from math import sqrt, pow
from urllib.parse import quote_plus, unquote
from tkinter import Frame
import tkinter as tk
from settings import edsm_url, canonn_cloud_url_us_central
from context import GameState

nvl = lambda a, b: a or b


def surface_pressure(tag, value):
    if value == None:
        return 0
    if tag == "surfacePressure":
        return value * 100000
    else:
        return value


class poiTypes(threading.Thread):
    def __init__(self, system, cmdr, callback):
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.callback = callback

    def run(self):
        debug("running poitypes")
        self.callback(self.system, self.cmdr)

    # def recycle(self):
    #     print "Recycling Labels"
    #
    #     for label in self.lt:
    #         label.grid_remove()
    #     for label in self.lp:
    #         label.grid_remove()

    # Frame.destroy(self)


class CodexTypes(Frame):
    tooltips = {
        "Geology": _("Geology: Vents and fumeroles"),
        "Cloud": _("Lagrange Clouds"),
        "Anomaly": _("Anomalous stellar phenomena"),
        "Thargoid": _("Thargoid sites or barnacles"),
        "Biology": _("Biological surface signals"),
        "Guardian": _("Guardian sites"),
        "None": _("Unclassified codex entry"),
        "Human": _("Human Sites"),
        "Ring": _("Planetary Ring Resources"),
        "Other": _("Other Sites"),
        "Planets": _("Valuable Planets"),
        "Tourist": _("Tourist Informatiom")
    }

    body_types = {
        'Metal-rich body': _('Metal-Rich Body'),
        'Metal rich body': _('Metal-Rich Body'),
        'Earth-like world': _('Earthlike World'),
        'Earthlike body': _('Earthlike World'),
        'Water world': _('Water World'),
        'Ammonia world': _('Ammonia World')
    }

    bodycount = 0

    parentRadius = 0
    minPressure = 80

    close_orbit = 0.05
    eccentricity = 0.9

    waiting = True

    def __init__(self, parent, gridrow):
        "Initialise the ``Patrol``."
        Frame.__init__(
            self,
            parent
        )

        self.parent = parent
        self.bind('<<POIData>>', self.evisualise)
        self.hidecodexbtn = tk.IntVar(value=config.getint("CanonnHideCodex"))
        self.hidecodex = self.hidecodexbtn.get()

        self.container = Frame(self)
        self.container.columnconfigure(1, weight=1)
        # self.tooltip=Frame(self)
        # self.tooltip.columnconfigure(1, weight=1)
        # self.tooltip.grid(row = 1, column = 0,sticky="NSEW")

        # self.tooltiplist=tk.Frame(self.tooltip)
        self.tooltiplist = tk.Frame(self)

        self.images = {}
        self.labels = {}
        self.tooltipcol1 = []
        self.tooltipcol2 = []

        self.addimage("Geology", 0)
        self.addimage("Cloud", 1)
        self.addimage("Anomaly", 2)
        self.addimage("Thargoid", 3)
        self.addimage("Biology", 4)
        self.addimage("Guardian", 5)
        self.addimage("Human", 6)
        self.addimage("Ring", 7)
        self.addimage("None", 8)
        self.addimage("Other", 9)
        self.addimage("Planets", 10)
        self.addimage("Tourist", 11)

        # self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        self.grid(row=gridrow, column=0)
        self.container.grid(row=0, column=0, sticky="W")
        self.poidata = []
        # self.tooltip.grid_remove()
        self.tooltiplist.grid()
        self.grid()
        self.tooltiplist.grid_remove()
        self.grid_remove()

    # wrapper for visualise

    def evisualise(self, event):
        self.visualise()

    def getdata(self, system, cmdr):
        debug("Getting POI data in thread")
        CodexTypes.waiting = True

        try:
            self.poidata = []
            system_name = quote_plus(system.encode('utf8'))
            odyssey = "Y" if GameState.odyssey else "N"
            params = {
                "system":  system_name,
                "cmdr":    cmdr,
                "odyssey": odyssey
            }
            url = f"{canonn_cloud_url_us_central}/query/getSystemPoi"
            debug(params)
            r = requests.get(url, params=params)

            if r.status_code == 200:
                poidata = r.json().get("codex")
                if not poidata:
                    debug("[codex] Nothing interesting here.")
                    self.event_generate('<<POIData>>', when='tail')
                    return
            else:
                debug("[codex] Error while fetching data: response code {}.")

            for r in poidata:
                self.merge_poi(
                    r.get("hud_category"),
                    r.get("english_name"),
                    r.get("body")
                )

            usystem = unquote(system)
            params = {
                "systemName": system_name,
            }
            edsm = f"{edsm_url}/api-system-v1/bodies"
            debug(edsm)
            r = requests.get(edsm, params=params)
            if r.status_code == requests.codes.ok:
                bodies = r.json().get("bodies")
                if bodies:
                    CodexTypes.bodycount = len(bodies)
                    debug("bodycount: {}".format(CodexTypes.bodycount))
                    if bodies[0].get("solarRadius"):
                        CodexTypes.parentRadius = self.light_seconds(
                            "solarRadius", bodies[0].get("solarRadius")
                        )

                    for body in bodies:
                        debug(body.get("subType"))
                        body_code = body.get("name").replace(usystem, '')
                        body_name = body.get("name")

                        # Terraforming
                        if body.get('terraformingState') == 'Candidate for terraforming':
                            self.merge_poi(
                                "Planets", "Terraformable", body_code
                            )

                        # Landable Volcanism
                        if body.get('type') == 'Planet' and body.get('volcanismType') != 'No volcanism' and body.get('isLandable'):
                            self.merge_poi(
                                "Geology", body.get('volcanismType'), body_code
                            )

                        # water ammonia etc
                        if body.get('subType') in CodexTypes.body_types.keys():
                            self.merge_poi(
                                "Planets",
                                CodexTypes.body_types.get(body.get('subType')),
                                body_code
                            )

                        # fast orbits
                        if body.get('orbitalPeriod'):
                            if abs(float(body.get('orbitalPeriod'))) <= 0.042:
                                self.merge_poi(
                                    "Tourist", 'Fast Orbital Period', body_code
                                )

                        # Ringed ELW etc
                        if body.get('subType') in ('Earth-like world', 'Water world', 'Ammonia world'):
                            if body.get("rings"):
                                self.merge_poi(
                                    "Tourist",
                                    'Ringed {}'.format(CodexTypes.body_types.get(body.get('subType'))),
                                    body_code)
                            if body.get("parents")[0].get("Planet"):
                                self.merge_poi("Tourist",
                                               '{} Moon'.format(CodexTypes.body_types.get(body.get('subType'))),
                                               body_code)
                        if body.get('subType') in ('Earth-like world') and body.get('rotationalPeriodTidallyLocked'):
                            self.merge_poi("Tourist", 'Tidal Locked Earthlike Word',
                                           body_code)

                        #  Landable with surface pressure
                        if (body.get('type') == 'Planet'
                            and surface_pressure("surfacePressure", body.get('surfacePressure')) > CodexTypes.minPressure
                            and body.get('isLandable')
                        ):
                            self.merge_poi("Tourist", 'Landable with atmosphere', body_code)

                        #    Landable high-g (>3g)
                        if body.get('type') == 'Planet' and body.get('gravity') > 3 and body.get('isLandable'):
                            self.merge_poi("Tourist", 'High Gravity', body_code)

                        #    Landable large (>18000km radius)
                        if body.get('type') == 'Planet' and body.get('radius') > 18000 and body.get('isLandable'):
                            self.merge_poi("Tourist", 'Large Radius Landable', body_code)

                        # orbiting close to the star we need the solar radius for this...
                        if (body.get('type') == 'Planet'
                            and body.get("distanceToArrival") - CodexTypes.parentRadius < 10
                        ):
                            self.merge_poi("Tourist", 'Surface Close to parent star', body_code)

                        #    Orbiting close to parent body less than 5ls
                        if body.get('type') == 'Planet' and self.aphelion('semiMajorAxis', body.get("semiMajorAxis"),
                                                                       body.get(
                                                                           "orbitalEccentricity")) < CodexTypes.close_orbit:
                            self.merge_poi("Tourist", 'Close Orbit', body_code)

                        #   Shepherd moons (orbiting closer than a ring)
                        #    Close binary pairs
                        #   Colliding binary pairs
                        #    Moons of moons

                        #    Tiny objects (<300km radius)
                        if body.get('type') == 'Planet' and body.get('radius') < 300 and body.get('isLandable'):
                            self.merge_poi("Tourist", 'Tiny Radius Landable', body_code)

                        #    Fast and non-locked rotation
                        if body.get('type') == 'Planet' and abs(float(body.get('rotationalPeriod'))) < 1 / 24 and not body.get(
                                "rotationalPeriodTidallyLocked"):
                            self.merge_poi("Tourist", 'Fast unlocked rotation', body_code)

                        #    High eccentricity
                        if float(body.get("orbitalEccentricity") or 0) > CodexTypes.eccentricity:
                            self.merge_poi("Tourist", 'Highly Eccentric Orbit', body)
                        #    Wide rings
                        #    Good jumponium availability (5/6 materials on a single body)
                        #    Full jumponium availability within a single system
                        #    Full jumponium availability on a single body

            else:
                CodexTypes.bodycount = 0
                debug("bodycount: {}".format(CodexTypes.bodycount))
        except:
            debug("Error fetching data")
            debug(traceback.format_exc())

        CodexTypes.waiting = False
        debug("event_generate")
        self.event_generate('<<POIData>>', when='tail')
        debug("Finished getting POI data in thread")

    def enter(self, event):

        type = event.widget["text"]
        # clear it if it exists
        for col in self.tooltipcol1:
            col["text"] = ""
            try:
                col.grid()
                col.grid_remove()
            except:
                error("Col1 grid_remove error")
        for col in self.tooltipcol2:
            col["text"] = ""
            try:
                col.grid()
                col.grid_remove()
            except:
                error("Col2 grid_remove error")

        poicount = 0

        # need to initialise if not exists
        if len(self.tooltipcol1) == 0:
            self.tooltipcol1.append(tk.Label(self.tooltiplist, text=""))
            self.tooltipcol2.append(tk.Label(self.tooltiplist, text=""))

        for poi in self.poidata:
            if poi.get("hud_category") == type:
                ## add a new label if it dont exist
                if len(self.tooltipcol1) == poicount:
                    self.tooltipcol1.append(tk.Label(self.tooltiplist, text=poi.get("english_name")))
                    self.tooltipcol2.append(tk.Label(self.tooltiplist, text=poi.get("body")))
                else:  ## just set the label
                    self.tooltipcol1[poicount]["text"] = poi.get("english_name")
                    self.tooltipcol2[poicount]["text"] = poi.get("body")

                # remember to grid them
                self.tooltipcol1[poicount].grid(row=poicount, column=0, columnspan=1, sticky="NSEW")
                self.tooltipcol2[poicount].grid(row=poicount, column=1, sticky="NSEW")
                poicount = poicount + 1

        if poicount == 0:
            self.tooltipcol1[poicount]["text"] = CodexTypes.tooltips.get(type)
            self.tooltipcol1[poicount].grid(row=poicount, column=0, columnspan=2)
            self.tooltipcol2[poicount].grid_remove()

        # self.tooltip.grid(sticky="NSEW")
        self.tooltiplist.grid(sticky="NSEW")

        ##self.tooltip["text"]=CodexTypes.tooltips.get(event.widget["text"])

    def leave(self, event):
        # self.tooltip.grid_remove()

        self.tooltiplist.grid()
        self.tooltiplist.grid_remove()

    def addimage(self, name, col):

        grey = "{}_grey".format(name)
        self.images[name] = tk.PhotoImage(file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(name)))
        self.images[grey] = tk.PhotoImage(file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(grey)))
        self.labels[name] = tk.Label(self.container, image=self.images.get(grey), text=name)
        self.labels[name].grid(row=0, column=col)

        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind("<ButtonPress>", self.enter)
        self.labels[name]["image"] = self.images[name]

    def set_image(self, name, enabled):
        grey = "{}_grey".format(name)

        if enabled:
            setting = name
        else:
            setting = grey

        if enabled and self.labels.get(name):
            self.labels[name].grid()
        else:
            # ensure it is enabled before disabling
            self.labels[name].grid()
            self.labels[name].grid_remove()

    def merge_poi(self, hud_category, english_name, body):
        debug("Merge POI")
        found = False
        signals = self.poidata
        for i, v in enumerate(signals):
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category:
                if not body in signals[i].get("body").split(','):
                    self.poidata[i]["body"] = "{},{}".format(signals[i].get("body"), body)
                found = True
        if not found:
            self.poidata.append({"hud_category": hud_category, "english_name": english_name, "body": body})

    def remove_poi(self, hud_category, english_name):
        debug("Remove POI")
        signals = self.poidata
        for i, v in enumerate(signals):
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category:
                del self.poidata[i]

    def light_seconds(self, tag, value):
        debug("light seconds {} {}".format(tag, value))
        if tag in ("distanceToArrival", "DistanceFromArrivalLS"):
            return value

        # Things measured in meters
        if tag in ("Radius", "SemiMajorAxis"):
            # from journal metres
            return value / 299792000

        # Things measure in kilometres
        if tag == "radius":
            return value / 299792

        # Things measure in astronomical units
        if tag == "semiMajorAxis":
            return value * 499.005

        # Things measured in solar radii
        if tag == "solarRadius":
            return value * 2.32061

    def semi_minor_axis(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        minor = sqrt(pow(a, 2) * (1 - pow(e, 2)))

        return minor

    # The focus is the closest point of the orbit
    # return value is in light seconds
    def perihelion(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        focus = a * (1 - e)
        debug("focus  {}ls".format(a))

        return focus

    def aphelion(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        focus = a * (1 + e)
        debug("focus  {}ls".format(a))

        return focus

    def surface_distance(self, d, r1, r2):
        return d - r1 - r2

    def visualise(self):

        #debug("visualise")
        # we may want to try again if the data hasn't been fetched yet
        if CodexTypes.waiting:
            #debug("Still waiting");
            pass
        else:

            self.set_image("Geology", False)
            self.set_image("Cloud", False)
            self.set_image("Anomaly", False)
            self.set_image("Thargoid", False)
            self.set_image("Biology", False)
            self.set_image("Guardian", False)
            self.set_image("Human", False)
            self.set_image("Ring", False)
            self.set_image("None", False)
            self.set_image("Other", False)
            self.set_image("Planets", False)
            self.set_image("Tourist", False)

            if self.poidata:
                self.grid()
                self.visible()
                for r in self.poidata:
                    #debug(r)
                    self.set_image(r.get("hud_category"), True)
            else:
                self.grid()
                self.grid_remove()

    def journal_entry(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        #debug("CodeTypes journal_entry")

        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            # go fetch some data.It will 
            poiTypes(entry.get("StarSystem"), cmdr, self.getdata).start()
            self.grid()
            self.grid_remove()

        if entry.get("event") in ("Location", "StartUp"):
            debug("Looking for POI data in {}".format(system))
            poiTypes(system, cmdr, self.getdata).start()

        if entry.get("event") in ("Location", "StartUp", "FSDJump"):
            if entry.get("SystemAllegiance") in ("Thargoid", "Guardian"):
                self.merge_poi(entry.get("SystemAllegiance"), "{} Controlled".format(entry.get("SystemAllegiance")), "")

        if entry.get("event") in ("FSSDiscoveryScan"):
            CodexTypes.fsscount = entry.get("BodyCount")
            if not CodexTypes.fsscount:
                CodexTypes.fsscount = 0
            debug("body reconciliation: {} {}".format(CodexTypes.bodycount, CodexTypes.fsscount))
            if nvl(CodexTypes.fsscount,0) > nvl(CodexTypes.bodycount,0):
                self.merge_poi("Planets", "Unexplored Bodies", "")

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in (
                '$Fixed_Event_Life_Ring;', '$Fixed_Event_Life_Cloud;'):
            if entry.get("SignalName") == '$Fixed_Event_Life_Cloud;':
                self.merge_poi("Cloud", "Life Cloud", "")
            else:
                self.merge_poi("Cloud", "Life Ring", "")

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in ('Guardian Beacon'):
            self.merge_poi("Guardian", "Guardian Beacon", "")

        if entry.get("event") == "FSSSignalDiscovered":
            if "NumberStation" in entry.get("SignalName"):
                self.merge_poi("Human", "Unregistered Comms Beacon", body)
            if "Megaship" in entry.get("SignalName"):
                self.merge_poi("Human", "Megaship", body)
            if "ListeningPost" in entry.get("SignalName"):
                self.merge_poi("Human", "Listening Post", body)
            if "CAPSHIP" in entry.get("SignalName"):
                self.merge_poi("Human", "Capital Ship", body)
            if "Generation Ship" in entry.get("SignalName"):
                self.merge_poi("Human", entry.get("SignalName"), body)


        if entry.get("event") == "FSSAllBodiesFound":
            self.remove_poi("Planets", "Unexplored Bodies")

        if entry.get("event") == "Scan" and entry.get("ScanType") in ("Detailed", "AutoScan"):
            self.remove_poi("Planets", "Unexplored Bodies")
            body = entry.get("BodyName").replace(system, '')
            english_name = CodexTypes.body_types.get(entry.get("PlanetClass"))
            if entry.get("PlanetClass") in CodexTypes.body_types.keys():
                debug("PlanetClass".format(entry.get("PlanetClass")))
                self.merge_poi("Planets", english_name, body)
            debug("Volcanism {} landable {}".format(entry.get("Volcanism"), entry.get("Landable")))
            if entry.get("Volcanism") != "" and entry.get("Landable"):
                self.merge_poi("Geology", entry.get("Volcanism"), body)
            if entry.get('TerraformState') == 'Terraformable':
                self.merge_poi("Planets", "Terraformable", body)

            if entry.get('OrbitalPeriod'):
                if abs(float(entry.get('OrbitalPeriod'))) < 3600:
                    self.merge_poi("Tourist", "Fast Orbit", body)

            if entry.get('PlanetClass') in ('Earthlike body', 'Water world', 'Ammonia world'):
                if entry.get("Rings"):
                    self.merge_poi("Tourist", 'Ringed {}'.format(CodexTypes.body_types.get(entry.get('PlanetClass'))),
                                   body)
                if entry.get("Parents")[0].get("Planet"):
                    self.merge_poi("Tourist", '{} Moon'.format(CodexTypes.body_types.get(entry.get('PlanetClass'))),
                                   body)

            if entry.get('PlanetClass') and entry.get('PlanetClass') in ('Earthlike body') and entry.get('TidalLock'):
                self.merge_poi("Tourist", 'Tidal Locked Earthlike Word',
                               body)

            #  Landable with surface pressure
            if entry.get('PlanetClass') and entry.get('Landable') and entry.get(
                    'SurfacePressure') and surface_pressure("SurfacePressure", entry.get(
                    'SurfacePressure')) > CodexTypes.minPressure:
                self.merge_poi("Tourist", 'Landable with atmosphere', body)

            #    Landable high-g (>3g) looks like the journal is tenths of G therefor 3.257900 = 0.33G
            if entry.get('PlanetClass') and entry.get('SurfaceGravity') and entry.get('SurfaceGravity') > 30 and entry.get('Landable'):
                self.merge_poi("Tourist", 'High Gravity', body)

            #    Landable large (>18000km radius)
            if entry.get('PlanetClass') and entry.get('Radius') > 18000000 and entry.get('Landable'):
                self.merge_poi("Tourist", 'Large Radius Landable', body)

            #    Orbiting close to parent body
            if entry.get('PlanetClass') and self.aphelion('SemiMajorAxis', entry.get("SemiMajorAxis"),
                                                          entry.get("Eccentricity")) < CodexTypes.close_orbit:
                self.merge_poi("Tourist", 'Close Orbit', body)
            #   Shepherd moons (orbiting closer than a ring)
            #    Close binary pairs
            #   Colliding binary pairs
            #    Moons of moons

            #    Tiny objects (<300km radius)
            if entry.get('Landable') and entry.get('Radius') and entry.get('Radius') < 300000 :
                self.merge_poi("Tourist", 'Tiny Radius Landable', body)

            #    Fast and non-locked rotation < 1 hour
            if entry.get('PlanetClass') and entry.get('RotationPeriod') and abs(
                    entry.get('RotationPeriod')) < 3600 and not entry.get("TidalLock"):
                self.merge_poi("Tourist", 'Fast unlocked rotation', body)

            #    High eccentricity
            if float(entry.get("Eccentricity") or 0) > CodexTypes.eccentricity:
                self.merge_poi("Tourist", 'Highly Eccentric Orbit', body)
            #    Wide rings
            #    Good jumponium availability (5/6 materials on a single body)
            #    Full jumponium availability within a single system
            #    Full jumponium availability on a single body

        if entry.get("event") == "Scan" and entry.get("AutoScan") and entry.get("BodyID") == 1:
            CodexTypes.parentRadius = self.light_seconds("Radius", entry.get("Radius"))

        if entry.get("event") == "SAASignalsFound":
            # if we arent waiting for new data
            bodyName = entry.get("BodyName")
            bodyVal = bodyName.replace(system, '')

            debug("SAASignalsFound")

            signals = entry.get("Signals")
            for i, v in enumerate(signals):
                found = False
                type = signals[i].get("Type")
                english_name = type.replace("$SAA_SignalType_", "").replace("ical;", "y").replace(";", '')
                if " Ring" in bodyName:
                    cat = "Ring"
                if "$SAA_SignalType_" in type:
                    cat = english_name
                for x, r in enumerate(self.poidata):
                    if r.get("hud_category") == cat and r.get("english_name") == english_name:
                        found = True
                        if not bodyVal in r.get("body"):
                            self.poidata[x]["body"] = "{},{}".format(self.poidata[x]["body"], bodyVal)
                if not found:
                    self.set_image(cat, True)
                    self.poidata.append({'body': bodyVal, 'hud_category': cat, 'english_name': english_name})

                debug(self.poidata)
                debug("cat {} name  {} body {}".format(cat, english_name, bodyVal))

        # we can do this on every event can't we
        self.visualise()
        #debug(json.dumps(self.poidata))

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidecodexbtn = tk.IntVar(value=config.getint("CanonnHideCodex"))

        self.hidecodex = self.hidecodexbtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text=_("Настройки Кодекса")).grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text=_("Скрыть иконки кодекса"), variable=self.hidecodexbtn).grid(row=1, column=0, sticky="NW")

        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnHideCodex', self.hidecodexbtn.get())

        self.hidecodex = self.hidecodexbtn.get()

        # dont check the retval

        self.visualise()

    def visible(self):

        noicons = (self.hidecodex == 1)

        if noicons:
            self.grid()
            self.grid_remove()
            self.isvisible = False
            return False
        else:
            self.grid()
            self.isvisible = True
            return True