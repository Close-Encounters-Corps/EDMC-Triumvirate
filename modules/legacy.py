# -*- coding: utf-8 -*-
import threading, requests, traceback, json, os, sys, sqlite3
import tkinter as tk

from math import sqrt, pow
from datetime import datetime
from collections import deque
from tkinter import font, ttk
from .debug import debug, error, info
from .lib.conf import config
from .lib.thread import Thread, BasicThread
from .player import Player

try:#py3
    from urllib.parse import quote_plus
except:#py2
    from urllib import quote_plus

if sys.maxsize >= 2**31:        # maxsize на 32 битах = 2**31-1
    from thirdparty.PIL64 import Image, ImageTk
else:
    from thirdparty.PIL import Image, ImageTk


URL_GOOGLE = 'https://docs.google.com/forms/d/e'


class Reporter(threading.Thread):
    def __init__(self, payload):
        threading.Thread.__init__(self)
        self.payload = payload

    def run(self):
        try:
            requests.get(self.payload)
        except:
            print(('Issue posting message ' + str(sys.exc_info()[0])))
            


def getDistance(x1,y1,z1,x2,y2,z2):
    return round(sqrt(pow(float(x2) - float(x1),2) + pow(float(y2) - float(y1),2) + pow(float(z2) - float(z1),2)),2)

def getDistanceMerope(x1,y1,z1):
    return round(sqrt(pow(float(-78.59375) - float(x1),2) + pow(float(-149.625) - float(y1),2) + pow(float(-340.53125) - float(z1),2)),2)        
    
def getDistanceSol(x1,y1,z1):
    return round(sqrt(pow(float(0) - float(x1),2) + pow(float(0) - float(y1),2) + pow(float(0) - float(z1),2)),2)         
        
        
def matches(d, field, value):
    return field in d and value == d[field]     
        
def faction_kill(cmdr, is_beta, system, station, entry, state):#Сделано
    if entry['event'] == 'FactionKillBond':
        factionMatch = (matches(entry, 'VictimFaction', '$faction_Thargoid;') or matches(entry, 'VictimFaction', '$faction_Guardian;'))
        if factionMatch and 'Reward' in entry:
            url = 'https://docs.google.com/forms/d/e/1FAIpQLSdA-iypOHxi5L4iaINr57hVJYWaZj9d-rmx_rpLJ8mwPrlccQ/formResponse?usp=pp_url'
            url+='&entry.1574172588=' + quote_plus(cmdr)
            if is_beta:
                beta = 'Y'
            else: 
                beta = 'N'
            url+='&entry.1534486210=' + quote_plus(beta)
            url+='&entry.451904934=' + quote_plus(system)
            if station is not None:
                url+='&entry.666865209=' + quote_plus(station)
            
            url+='&entry.310344870=' + str(entry['Reward'])
            url+='&entry.706329985=' + quote_plus(entry['AwardingFaction'])
            url+='&entry.78713015=' + quote_plus(entry['VictimFaction'])
            Reporter(url).start()



def CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):#сделано
    #{
                                                                             #'timestamp':'2018-12-30T00:48:12Z',
                                                                             #'event':'CodexEntry',
                                                                             #'EntryID':2100301,
                                                                             #'Name':'$Codex_Ent_Cone_Name;',
                                                                             #'Name_Localised':'Bark Mounds',
                                                                             #'SubCategory':'$Codex_SubCategory_Organic_Structures;',
                                                                             #'SubCategory_Localised':'Organic
                                                                             #structures',
                                                                             #'Category':'$Codex_Category_Biology;',
                                                                             #'Category_Localised':'Biological
                                                                             #and Geological',
                                                                             #'Region':'$Codex_RegionName_18;',
                                                                             #'Region_Localised':'Inner Orion
                                                                             #Spur', 'System':'HIP 16378',
                                                                             #'SystemAddress':1,
                                                                             #'VoucherAmount':2500 }
    if entry['event'] == 'CodexEntry':
        url = 'https://docs.google.com/forms/d/e/1FAIpQLSfw5LtkhGRqQIXA9wG_-ByfAJ7R1DUrs7rGJ15CMr7mSP0VFQ/formResponse?usp=pp_url'

        url+='&entry.225040908=' + quote_plus(cmdr)
        url+='&entry.1726574817=' + quote_plus(system)
        url+='&entry.763596647=' + str(x)
        url+='&entry.1058472073=' + str(y)
        url+='&entry.2082187150=' + str(z)
        if body:
            url+='&entry.1996921251=' + quote_plus(body)
        if lat:
            url+='&entry.1610549351=' + str(lat)
            url+='&entry.594657555=' + str(lon)
        url+='&entry.684427446=' + quote_plus(str(entry['EntryID']))
        url+='&entry.1284748079=' + quote_plus(entry['Name'])
        url+='&entry.763283762=' + quote_plus(entry['Name_Localised'])
        url+='&entry.1357457545=' + quote_plus(entry['SubCategory'])
        url+='&entry.1137878415=' + quote_plus(entry['SubCategory_Localised'])
        url+='&entry.145132650=' + quote_plus(entry['Category'])
        url+='&entry.1517395872=' + quote_plus(entry['Category_Localised'])
        url+='&entry.744185618=' + quote_plus(entry['Region'])
        url+='&entry.873911354=' + quote_plus(entry.get('Region_Localised').encode('utf8'))
        url+='&entry.263943315=' + quote_plus(str(entry['SystemAddress']))
        if('VoucherAmount' in entry):
            url+='&entry.246809407=' + quote_plus(str(entry['VoucherAmount']))
                
        
        Reporter(url).start()


last_body_with_biosignals = ""
def GusonExpeditions(cmdr, is_beta, system, entry):
    # рекоды: количество тел
    if entry.get('event') == 'FSSDiscoveryScan':
        if entry.get('BodyCount') >= 150:
            url_params = {
                "entry.1258689641": cmdr,
                "entry.1469465131": entry.get("SystemName", ""),
                "entry.1583990022": "BodyCount",
                "entry.1301773715": entry.get("BodyCount", ""),
            }
            url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
            Reporter(url).start()

    # проверка АТ на биосигналы перед отправкой в базу
    if entry["event"] == "FSSBodySignals":
        for signal in entry["Signals"]:
            if signal["Type"] == "$SAA_SignalType_Biological;":
                global last_body_with_biosignals
                last_body_with_biosignals = entry["BodyName"]

    if entry.get('event') != 'Scan':
        return
    
    if "PlanetClass" in entry:
        # рекорды: масса тела
        limits = {
            "Metal rich body":                   {"limit": 643, "planetClass": "MetalRichBody"},
            "High metal content body":           {"limit": 1258, "planetClass": "HMCBody"},
            "Rocky body":                        {"limit": 475, "planetClass": "RockyBody"},
            "Rocky ice body":                    {"limit": 268, "planetClass": "RockyIceBody"},
            "Icy body":                          {"limit": 1992, "planetClass": "IcyBody"},
            "Earthlike body":                    {"limit": 6.39, "planetClass": "EarthlikeBody"},
            "Water world":                       {"limit": 667, "planetClass": "WaterWorld"},
            "Water giant":                       {"limit": 1864, "planetClass": "WaterGiant"},
            "Ammonia world":                     {"limit": 1194, "planetClass": "AmmoniaWorld"},
            "Gas giant with water based life":   {"limit": 1231, "planetClass": "WaterLifeGG"},
            "Gas giant with ammonia based life": {"limit": 818, "planetClass": "AmmoniaLifeGG"},
            "Sudarsky class I gas giant":        {"limit": 819, "planetClass": "ClassIGG"},
            "Sudarsky class II gas giant":       {"limit": 1231, "planetClass": "ClassIIGG"},
            "Sudarsky class III gas giant":      {"limit": 3112, "planetClass": "ClassIIIGG"},
            "Sudarsky class IV gas giant":       {"limit": 4862, "planetClass": "ClassIVGG"},
            "Sudarsky class V gas giant":        {"limit": 11757, "planetClass": "ClassVGG"},
            "Helium rich gas giant":             {"limit": 4288, "planetClass": "HeliumRichGG"},
            "Helium gas giant":                  {"limit": 5202, "planetClass": "HeliumGG"},
        }
        planet = entry.get("PlanetClass")
        limit = limits[planet]["limit"]
        planetClass = limits[planet]["planetClass"]
        
        mass = entry.get("MassEM")
        if mass > limit:
            url_params = {
                "entry.1258689641": cmdr,
                "entry.1469465131": entry.get("BodyName", ""),
                "entry.1583990022": f'HighMass{planetClass}',
                "entry.1301773715": str(mass).replace('.', ','),
            }
            url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
            Reporter(url).start()

        # рекорды: горячие юпитеры
        if "gas giant" in entry.get("PlanetClass").lower():
            if entry.get("SurfaceTemperature") > 9352.83:
                url_params = {
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HotJupiter",
                    "entry.1301773715": str(entry.get("SurfaceTemperature")).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
                Reporter(url).start()

        # рекорды: радиус колец
        if "Rings" in entry:
            rings = entry.get("Rings")
            for ring in rings:
                outerRad = str(ring.get("OuterRad"))
                outerRad = outerRad[:outerRad.find('.')]
                if float(outerRad) >= 34732000000:
                    url_params = {
                        "entry.1258689641": cmdr,
                        "entry.1469465131": ring.get("Name"),
                        "entry.1583990022": "WideRing",
                        "entry.1301773715": outerRad[:-3],
                    }
                    url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
                    Reporter(url).start()
        
        if entry.get("Landable") == True:
            # рекорды: температура посадочных
            if entry.get("SurfaceTemperature") > 5115.9:
                url_params = {
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HighTemperature",
                    "entry.1301773715": entry.get("SurfaceTemperature"),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
                Reporter(url).start()

            # рекорды: радиус посадочных
            if entry.get("Radius") / 1000 > 25444:
                url_params = {
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HugeRadius",
                    "entry.1301773715": str(entry.get("Radius")).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
                Reporter(url).start()
            elif entry.get("Radius") <= 138000:
                url_params = {
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "TinyRadius",
                    "entry.1301773715": str(entry.get("Radius") / 1000).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
                Reporter(url).start()
            
            # рекорды: гравитация посадочных
            if entry.get("SurfaceGravity") / 10 > 7.51:
                url_params = {
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HighGravity",
                    "entry.1301773715": str(entry.get("SurfaceGravity") / 10).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
                Reporter(url).start()

    # рекорды: орбитальный период
    if "OrbitalPeriod" in entry:
        if entry.get("OrbitalPeriod") <= 1800:
            url_params = {
                "entry.1258689641": cmdr,
                "entry.1469465131": entry.get("BodyName"),
                "entry.1583990022": "OrbitalPeriod",
                "entry.1301773715": entry.get("OrbitalPeriod"),
            }
            url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse?usp=pp_url&{"&".join([f"{k}={v}" for k, v in url_params.items()])}'
            Reporter(url).start()

    if "PlanetClass" in entry:
        # БД атмосферных и рекорды - ГГ
        if "gas giant" in entry.get("PlanetClass").lower():
            helium_percentage = 0.0
            for comp in entry.get("AtmosphereComposition", []):
                if comp["Name"] == "Helium":
                    helium_percentage = comp["Percent"]

            # общая БД
            url_params = {
                "entry.262880086": entry.get("BodyName", ""),
                "entry.808713567": str(helium_percentage).replace('.', ','),
                "entry.549950938": entry.get("StarSystem", "")
            }
            url = f'{URL_GOOGLE}/1FAIpQLSeVvva2K9VMJZyr4mJ9yRnQPXhcDHUwO8iTxrg2z1Qi4lJk_Q/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
            Reporter(url).start()

            # БД Boepp (экспедиционная)
            if "Boepp " in entry["BodyName"]:
                url_params = {
                    "entry.207321892": entry.get("BodyName", ""),
                    "entry.318090096": str(helium_percentage).replace('.', ','),
                    "entry.1828517199": entry.get("StarSystem", "")
                }
                url = f'{URL_GOOGLE}/1FAIpQLSeCRZ9GXprtSEUFgUOMR5yBGkqYpdrKAumLkYH6KkPOUq3sIA/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
                Reporter(url).start()

            # рекорды
            url_params = {
                "entry.280367197": entry.get("BodyName", ""),
                "entry.779566159": str(helium_percentage).replace('.', ','),
                "entry.1789316283": entry.get("StarSystem", "")
            }
            url = f'{URL_GOOGLE}/1FAIpQLSc6mPwibfkLDyVklC7bEiJsNOtcE8pE9OS2b9o3FpBDNiaN4g/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
            Reporter(url).start()

        # Картография
        valuable = False
        if entry["PlanetClass"] in ("Earthlike body", "Ammonia world"):
            valuable = True
        elif entry["PlanetClass"] == "Water world" and entry["TerraformState"] == "Terraformable":
            valuable = True

        known = entry.get("WasMapped") or entry.get("WasDiscovered")

        if valuable and not known:
            url_params = {
                "entry.2022004794": cmdr,
                "entry.1225803723": entry.get("BodyName", ""),
                "entry.645216132": entry.get("PlanetClass", ""),
                "entry.512641942": str(entry.get("WasDiscovered", "")),
                "entry.1801392650": str(entry.get("WasMapped", "")),
                "entry.1992174852": entry.get("StarSystem", "")
            }
            url = f'{URL_GOOGLE}/1FAIpQLSdgwzvgxow5ATuB4Gimj6DvDRD3-ub3Yp4UD-nQK4CnZdKV9w/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
            Reporter(url).start()

        # БД атмосферных - планеты
        if entry["Landable"] == True:
            if "thin" in entry["Atmosphere"]:
                if "helium" in entry["Atmosphere"] or "oxygen" in entry["Atmosphere"]:
                    gravity_limit = 0.6
                else:
                    gravity_limit = 0.275
                if entry["SurfaceGravity"] / 10 <= gravity_limit:
                    if entry["BodyName"] == last_body_with_biosignals:
                        url_params = {
                            "entry.347011697": cmdr,
                            "entry.1687350455": entry.get("BodyName", ""),
                            "entry.1816286975": entry.get("PlanetClass", ""),
                            "entry.511521292": entry.get("Atmosphere", ""),
                            "entry.241360196": entry.get("Volcanism", "None"),
                            "entry.2023664263": str(entry.get("SurfaceGravity", 0) / 10).replace('.', ','),
                            "entry.1625198123": str(entry.get("SurfaceTemperature", 0)).replace('.', ','),
                            "entry.464017034": str(entry.get("SurfacePressure", 0)).replace('.', ','),
                            "entry.1546311301": str(entry.get("WasDiscovered", "")),
                            "entry.1533734556": str(entry.get("WasMapped", "")),
                            "entry.1572906861": entry.get("StarSystem", "")
                        }
                        # общая БД
                        url = f'{URL_GOOGLE}/1FAIpQLScWkHPhTEHcNCoAwIAbb54AQgg8A6ocX2Ulbfkr2hcubgfbRA/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
                        Reporter(url).start()
                        # БД Boepp (экспедиционная)
                        if "Boepp " in entry["BodyName"]:
                            url = f'{URL_GOOGLE}/1FAIpQLSfrZqrZHJ5T0lgpaoUOcLgM0fXmR_t5_vLKvT7J5HDA8mugeg/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
                            Reporter(url).start()

    # звёзды
    if "StarType" in entry:
        url_params = {
            "entry.422166846": entry.get("BodyName", ""),
            "entry.371313324": entry.get("StarType", "") + str(entry.get("Subclass", "")) + entry.get("Luminosity"),
            "entry.770073835": entry.get("StarSystem", ""),
            "entry.1133676298": str(entry.get("SurfaceTemperature", "")),
            "entry.786810023": str(entry.get("Age_MY"))
        }
        # общая БД
        url = f'{URL_GOOGLE}/1FAIpQLSdfXA2mLXTamWdz3mXC3Ta3UaJS6anqY4wvzkX-9XzGilZ6Tw/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
        Reporter(url).start()
        # БД Boepp (экспедиционная)
        if "Boepp " in entry["BodyName"]:
            url = f'{URL_GOOGLE}/1FAIpQLSeapH5azc-9T0kIZ4vfDBcDlcd8ZfMUBS42DMRXL8fYcBxRtQ/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
            Reporter(url).start()
        # картография
        url_params = {
            "entry.1407433679": entry.get("BodyName", ""),
            "entry.741998551": entry.get("StarType", "") + str(entry.get("Subclass", "")) + entry.get("Luminosity"),
            "entry.341231285": entry.get("StarSystem", ""),
            "entry.320405751": str(entry.get("SurfaceTemperature", "")),
            "entry.2033592775": str(entry.get("Age_MY"))
        }
        url = f'{URL_GOOGLE}/1FAIpQLSfYl0iPm-qQOCyD6iVIjK7BPIgnp6yABR2YVwfcp2GB5KWtNA/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(v)}" for k, v in url_params.items()])}'
        Reporter(url).start()


def AXZone(cmdr, is_beta, system,x,y,z,station, entry, state):#Сделано
    #{
                                                                  #'timestamp':'2019-01-19T23:22:26Z',
                                                                  #'event':'FSSSignalDiscovered',
                                                                  #'SystemAddress':250414621860,
                                                                  #'SignalName':'$Warzone_TG;',
                                                                  #'SignalName_Localised':'AX
                                                                  #Conflict Zone' }
    if entry['event'] == 'FSSSignalDiscovered' and entry['SignalName'] == '$Warzone_TG;':
        
        url = 'https://docs.google.com/forms/d/18u8QGujh9G-yBLhH8KBsBzn1gJp5j9PrS_hcIG6WWgw/formResponse?usp=pp_url'

        
        url+='&entry.736793268=' + quote_plus(cmdr)
        url+='&entry.1932953897=' + quote_plus(system)
        url+='&entry.1428557264=' + str(x)
        url+='&entry.271351956=' + str(y)
        url+='&entry.1814511958=' + str(z)
        url+='&entry.154660486=' + str(entry.get('SystemAddress'))
        
        Reporter(url).start()

## I want to avoid sending this event
## if there has not been any change
## so we will have a global dict
class Stats():#сделана
    
    tg_stats = {
        'tg_encounter_wakes': 0,
        'tg_encounter_imprint': 0,
        'tg_encounter_total': 0,
        'tg_timestamp': 'x',
        'tg_scout_count': 0,
        'tg_last_system': 'x'
    }
    
    @classmethod    
    def statistics(this,cmdr, is_beta, system, station, entry, state):
        
        if entry['event'] == 'Statistics':
            tge = entry.get('TG_ENCOUNTERS')
            new_tg_stats = {
                'tg_encounter_wakes': tge.get('TG_ENCOUNTER_WAKES'),
                'tg_encounter_imprint': tge.get('TG_ENCOUNTER_IMPRINT'),
                'tg_encounter_total': tge.get('TG_ENCOUNTER_TOTAL'),
                'tg_timestamp': tge.get('TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP'),
                'tg_scout_count': tge.get('TG_SCOUT_COUNT'),
                'tg_last_system': tge.get('TG_ENCOUNTER_TOTAL_LAST_SYSTEM')
            }
            if new_tg_stats != this.tg_stats:

                this.tg_stats = new_tg_stats
                url = 'https://docs.google.com/forms/d/e/1FAIpQLScF_URtGFf1-CyMNr4iuTHkxyxOMWcrZ2ZycrKAiej0eC-hTA/formResponse?usp=pp_url'
                url+='&entry.1391154225=' + quote_plus(cmdr)
                if 'TG_ENCOUNTER_WAKES' in entry['TG_ENCOUNTERS']:
                    url+='&entry.1976561224=' + str(entry['TG_ENCOUNTERS']['TG_ENCOUNTER_WAKES'])
                if 'TG_ENCOUNTER_IMPRINT' in entry['TG_ENCOUNTERS']:
                    url+='&entry.538722824=' + str(entry['TG_ENCOUNTERS']['TG_ENCOUNTER_IMPRINT'])
                if 'TG_ENCOUNTER_TOTAL' in entry['TG_ENCOUNTERS']:
                    url+='&entry.779348244=' + str(entry['TG_ENCOUNTERS']['TG_ENCOUNTER_TOTAL'])
                if 'TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP' in entry['TG_ENCOUNTERS']:
                    url+='&entry.1664525188=' + str(entry['TG_ENCOUNTERS']['TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP'])
                if 'TG_SCOUT_COUNT' in entry['TG_ENCOUNTERS']:
                    url+='&entry.674074529=' + str(entry['TG_ENCOUNTERS']['TG_SCOUT_COUNT'])
                if 'TG_ENCOUNTER_TOTAL_LAST_SYSTEM' in entry['TG_ENCOUNTERS']:
                    url+='&entry.2124154577=' + str(entry['TG_ENCOUNTERS']['TG_ENCOUNTER_TOTAL_LAST_SYSTEM'])
                Reporter(url).start()
                
        
        
def statistics(cmdr, is_beta, system, station, entry, state):  
    Stats.statistics(cmdr, is_beta, system, station, entry, state)

class NHSS(threading.Thread):

    fss = {}
    
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    def __init__(self,cmdr, is_beta, system, x,y,z,station, entry,client):
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client = client
        self.x = x
        self.y = y
        self.z = z

    def run(self):
        payload = {}

        if self.entry['event'] == 'FSSSignalDiscovered':
            threatLevel = self.entry.get('ThreatLevel')
            type = 'FSS'
        else:
            threatLevel = self.entry.get('USSThreat')
            type = 'Drop'

        payload['systemName'] = self.system
        payload['cmdrName'] = self.cmdr  
        payload['nhssRawJson'] = self.entry
        payload['threatLevel'] = threatLevel
        payload['isbeta'] = self.is_beta
        payload['clientVersion'] = self.client
        payload['reportStatus'] = 'accepted'
        payload['reportComment'] = type

        dsol = getDistance(0,0,0,self.x,self.y,self.z)
        dmerope = getDistance(-78.59375,149.625,-340.53125,self.x,self.y,self.z)
        
        url = 'https://docs.google.com/forms/d/e/1FAIpQLScVk2LW6EkIW3hL8EhuLVI5j7jQ1ZmsYCLRxgCZlpHiN8JdcA/formResponse?usp=pp_url'
        url+='&entry.106150081=' + quote_plus(self.cmdr)
        url+='&entry.582675236=' + quote_plus(self.system)
        url+='&entry.158339236=' + str(self.x)
        url+='&entry.608639155=' + str(self.y)
        url+='&entry.1737639503=' + str(self.z)
        url+='&entry.1398738264=' + str(dsol)
        url+='&entry.922392846=' + str(dmerope)
        url+='&entry.218543806=' + quote_plus('$USS_Type_NonHuman;')
        url+='&entry.455413428=' + quote_plus('Non-Human signal source')
        url+='&entry.790504343=' + str(threatLevel)
        r = requests.post(url)  
        
        url = 'https://docs.google.com/forms/d/e/1FAIpQLSeOBbUTiD64FyyzkIeZfO5UMfqeuU2lsRf3_Ulh7APddd91JA/formResponse?usp=pp_url'
        url+='&entry.306505776=' + quote_plus(self.system)
        url+='&entry.1559250350=Non Human Signal'
        url+='&entry.1031843658=' + str(threatLevel)
        url+='&entry.1519036101=' + quote_plus(self.cmdr)
        r = requests.post(url)  



    @classmethod
    def submit(cls,cmdr, is_beta, system,x,y,z, station, entry,client):

        #USS and FFS
        if entry['event'] in ('USSDrop','FSSSignalDiscovered') and entry.get('USSType') == '$USS_Type_NonHuman;' : 

            # The have different names
            # for teh same thing so
            # normalise
            if entry['event'] == 'FSSSignalDiscovered':
                threatLevel = entry.get('ThreatLevel')
            else:
                threatLevel = entry.get('USSThreat')

            # see if you have system
            # and threat levels store
            # Thsi will fail if it a
            # new threat level in the
            # current system
            try:
                globalfss = NHSS.fss.get(system)
                oldthreat = globalfss.get(threatLevel)
                #debug(globalfss)
            except:
                oldthreat = False

            if oldthreat:
                debug('Threat level already recorded here ' + str(threatLevel))

            else:
                #debug('Threat
                #{}'.format(threatLevel))
                try:
                    #set the
                    #threatlevel for
                    #the system
                    NHSS.fss[system][threatLevel] = True
                except:
                    #we couldnt find
                    #teh system so lets
                    #define it
                    NHSS.fss[system] = { threatLevel: True}

                NHSS(cmdr, is_beta, system,x,y,z, station, entry,client).start()
 #self.entry.get("Name_Localised").encode('utf8'))



class BGS:
    _missions_tracker = None
    _cz_tracker = None
    _threadlock = threading.Lock()
    _systems = list()
    _data_send_queue = deque()      # по логике нужна queue, но не хочу ещё один импорт тащить

    @classmethod
    def setup(cls, plugin_dir):
        cls._plugin_dir = plugin_dir
        BGS._missions_tracker = BGS.Missions_Tracker()
        BGS._cz_tracker = BGS.CZ_Tracker()
        BGS.Systems_Updater(BGS._systems).start()

    class Systems_Updater(Thread):
        def __init__(self, systems_list: list):
            super().__init__(name="BGS systems list updater")
            self.systems_list = systems_list
        def do_run(self):
            url = "https://api.github.com/gists/7455b2855e44131cb3cd2def9e30a140"
            attempts = 0
            while True:
                attempts += 1
                response = requests.get(url)
                if response.status_code == 200:
                    self.systems_list.clear()
                    self.systems_list += str(response.json()["files"]["systems"]["content"]).split('\n')
                    info("[BGS.setup] Got list of systems to track.")
                    BGS._send_all()
                    return
                error("[BGS.setup] Couldn't get list of systems to track, response code {} ({} attempts)", response.status_code, attempts)
                self.sleep(10)

    @classmethod
    def journal_entry(cls, cmdr, system, station, entry):
        with cls._threadlock:
            try:
                cls._missions_tracker.process_entry(cmdr, system, station, entry)
                cls._cz_tracker.process_entry(cmdr, system, entry)
            except:
                error(traceback.format_exc())

    @classmethod
    def stop(cls):
        with cls._threadlock:
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
                    BasicThread(target=lambda: requests.get(url, params)).start()
                    info("[BGS.send]: BGS information sent.")

    @classmethod
    def _send_all(cls):
        counter = 0
        for entry in cls._data_send_queue:
            for system in entry["systems"]:
                if system in cls._systems:
                    BasicThread(target=lambda: requests.get(entry["url"], entry["params"])).start()
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
            self._query("CREATE TABLE IF NOT EXISTS missions (id, payload)")
            self.main_faction = ""

        def stop(self):
            self._prune_expired()
            self.db.close()
        
        def _query(self, query: str, *args, fetchall: bool = False):
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
            now = datetime.utcnow()
            missions_list = self._query("SELECT id, payload FROM missions", fetchall=True)
            for id, payload in missions_list:
                mission = json.loads(payload)
                if "Megaship" not in mission["type"]:
                    expires = datetime.strptime(mission["expires"], "%Y-%m-%dT%H:%M:%SZ")
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
                self._set_faction(entry)
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
            

        def _set_faction(self, entry):
            self.main_faction = entry["StationFaction"]["Name"]
            debug("[BGS.set_faction]: detected {!r}, main_faction set to {!r}", entry["event"], self.main_faction)


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
            if (self.main_faction == "FleetCarrier"
                    or "BrokerPercentage" in entry
                    or entry["Type"] not in ("bounty", "CombatBond")):
                return
            
            url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse'
            if entry["Type"] == "bounty":
                debug("[BGS.redeem_voucher] Redeeming bounties:")
                for faction in entry["Factions"]:
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
            if self.main_faction != "FleetCarrier":
                url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse'
                url_params = {
                    "entry.503143076": cmdr,
                    "entry.1108939645": "SellExpData",
                    "entry.127349896": system,
                    "entry.442800983": station,
                    "entry.48514656": self.main_faction,
                    "entry.351553038": entry["TotalEarnings"],
                    "usp": "pp_url"
                }
                debug("[BGS.exploration_data]: Sold exploration data for {} credits, station's owner: {!r}",
                    entry["TotalEarnings"],
                    self.main_faction)
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
                    # пешие конфликты: смена режима
                    elif (event in ("DropshipDeploy", "Disembark", "LaunchSRV")
                        or event == "Location" and entry.get("InSRV") or entry.get("OnFoot")):
                        self.on_foot = True
                        debug("CZ_Tracker: on foot")
                    elif (event == "DockSRV" 
                        or event == "Embark" and entry["SRV"] == False
                        or event == "Location" and not(entry.get("InSRV") or entry.get("OnFoot"))):
                        self.on_foot = False
                        debug("CZ_Tracker: on ship")
                    # завершение конфликта: прыжок
                    elif event == "StartJump":
                        self._end_conflict()
                    # завершение конфликта: возврат на шаттле (ноги)
                    elif event == "BookDropship" and entry["Retreat"] == True:
                        self._end_conflict()
                    # досрочный выход
                    elif (event in ("Shutdown", "Died", "CancelDropship") or
                          event == "Music" and entry["MusicTrack"] == "MainMenu"):
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
                    "start_time": datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
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
                    "start_time": datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
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
                self.info["conflict_type"] == "Foot"
                and self.on_foot
                and not self.info["intensity"]
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
                timestamp = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                allegiance = entry["From"][19:1]
                debug("CZ_Tracker: detected patrol message sent from {!r} ship.", allegiance)

                if not self.end_messages.get(allegiance):
                    self.end_messages[allegiance] = deque(5*[None], 5)
                queue = self.end_messages[allegiance]               # они же по ссылке передаются?
                queue.append(timestamp)
                
                if queue[0] != None:
                    if (queue[4] - queue[0]).seconds <= 15:
                        debug("CZ_Tracker: got 5 patrol messages in 15 seconds, calling END_CONFLICT.")
                        self._end_conflict(allegiance)


        def _end_conflict(self, winners_allegiance: str | None = None):
            debug("CZ_Tracker: END_CONFLICT called, calculating the result.")
            self.info["end_time"] = datetime.utcnow()
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

            if not self.safe:
                debug("CZ_Tracker: we're (probably) in the Open, winner's prediction disabled.")
            
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
            BasicThread(target=lambda: Notification(info, presumed_winner), name="cz notification").start()

            class Notification(tk.Tk):
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
                    is_foot = (info["conflict_type"] == "Foot")
                    match info.get("intensity"):
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
                    ttk.Label(leftframe, style="msgtext.TLabel", text="Напряжённость:").grid(row=1, column=0, sticky="NW")
                    ttk.Label(leftframe, style="msgtext.TLabel", text="Поселение:").grid(row=2, column=0, sticky="NW") if is_foot else None
                    ttk.Label(leftframe, style="msgtext.TLabel", text="Участвующие фракции:\n").grid(row=2+is_foot, column=0, sticky="NW")
                    ttk.Label(leftframe, style="msgtext.TLabel", text="Предполагаемый победитель:").grid(row=3+is_foot, column=0, sticky="NW")
                    ttk.Label(leftframe, style="msgtext.TLabel", text="Вы сражались на стороне:").grid(row=4+is_foot, column=0, sticky="NW")

                    # правый столбец
                    ttk.Label(rightframe, style="msgtext.TLabel", text=info["system"]).grid(row=0, column=0, sticky="NW")
                    ttk.Label(rightframe, style="msgtext.TLabel", text=intensity).grid(row=1, column=0, sticky="NW")
                    ttk.Label(rightframe, style="msgtext.TLabel", text=info["location"]).grid(row=2, column=0, sticky="NW") if is_foot else None
                    ttk.Label(rightframe, style="msgtext.TLabel", text=str(self.factions[0]+"\n"+self.factions[1])).grid(row=2+is_foot, column=0, sticky="NW")
                    ttk.Label(rightframe, style="msgtext.TLabel", text=self.presumed).grid(row=3+is_foot, column=0, sticky="NW")
                    ttk.Label(rightframe, style="msgtext.TLabel", text=info["player_fights_for"]).grid(row=4+is_foot, column=0, sticky="NW")

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
                        BGS.CZ_Tracker._send_results(self.info, self.presumed, actual_winner)
                    else:
                        debug("CZ_Tracker: user canceled the choice.")
                    self.destroy()
        

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