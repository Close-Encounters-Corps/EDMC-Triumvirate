# -*- coding: utf-8 -*-
import threading
import requests
import traceback
try:#py3
    from urllib.parse import quote_plus
except:#py2
    from urllib import quote_plus

import json
import os
import sys
from  math import sqrt,pow,trunc
from .debug import debug, error
from datetime import datetime, timezone
from tkinter.messagebox import askyesnocancel
from collections import deque

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

        # Картография - только из Boepp
        if "Boepp " in entry["BodyName"]:
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

    # БД атмосферных - звёзды
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



class BGS():
    def __init__(self):
        self.CURRENT_MISSIONS_FILE = f"{os.path.expanduser('~')}\\AppData\\Local\\EDMarketConnector\\currentmissions.trmv"
        self.mainfaction = ""
        self.threadlock = threading.Lock()

    def TaskCheck(self, cmdr, is_beta, system, station, entry, client):
        self.threadlock.acquire()
        try:
            event = entry["event"]
            # стыковка/вход в игру на станции
            if event == "Docked" or (event == "Location" and entry["Docked"] == True):
                self.__setFaction(entry)
            # принятие миссии
            elif event == "MissionAccepted":
                self.__missionAccepted(entry, system)
            # сдача миссии
            elif event == "MissionCompleted":
                self.__missionCompleted(entry, cmdr)
            # провал миссии
            elif event == "MissionFailed":
                self.__missionFailed(entry, cmdr)
            # отказ от миссии
            elif event == "MissionAbandoned":
                self.__missionAbandoned(entry)
            # ваучеры
            elif event == "RedeemVoucher":
                self.__redeemVoucher(entry, cmdr, system)
            # картография
            elif "SellExplorationData" in event:
                self.__explorationData(entry, cmdr, system, station)
        
        except:
            error(traceback.format_exc())
        self.threadlock.release()

    def __setFaction(self, entry):
        debug(f"MAIN_FACTION: detected \"{entry['event']}\"")
        self.mainfaction = entry["StationFaction"]["Name"]
        debug(f"MAIN_FACTION: main_faction set to \"{self.mainfaction}\"")


    def __missionAccepted(self, entry, system):
        debug("MISSION_ACCEPTED: detected MissionAccepted")
        mission = {
            "timestamp": entry["timestamp"],
            "ID": entry["MissionID"],
            "expires": entry.get("Expiry", ""),
            "type": entry["Name"],
            "system": system,
            "faction": entry["Faction"],
            "system2": entry.get("DestinationSystem", "") if entry.get("TargetFaction", "") != "" else "",
            "faction2": entry.get("TargetFaction", ""),
        }
        debug("MISSION_ACCEPTED: saved data: " + str(mission))
        with open(self.CURRENT_MISSIONS_FILE, "a", encoding="utf8") as missions_file:
            missions_file.write(json.dumps(mission) + '\n')
            debug("MISSION_ACCEPTED: saved to currentmissions")


    def __missionCompleted(self, entry, cmdr):
        debug("MISSION_COMPLETE: detected MissionCompleted")
        with open(self.CURRENT_MISSIONS_FILE, "r", encoding="utf8") as missions_file:
            missions_list = missions_file.readlines()
            debug("MISSION_COMPLETE: read currentmissions")
        completed_mission = dict()
        debug("MISSION_COMPLETE: created empty dict 'completed_mission'")
        with open(self.CURRENT_MISSIONS_FILE, "w", encoding="utf8") as missions_file:
            debug("MISSION_COMPLETE: opened currentmissions for editing")
            for line in missions_list:
                mission = json.loads(line)
                debug("MISSION_COMPLETE: mission: " + str(mission))
                if mission["ID"] != entry["MissionID"]:
                    debug("MISSION_COMPLETE: not what we're looking for, saving to currentmissions")
                    missions_file.write(line)
                else:
                    debug("MISSION_COMPLETE: found what we're looking for, completed_mission = mission")
                    completed_mission = mission
        if completed_mission == {}:
            debug("MISSION_COMPLETE: WARNING: mission not found, exiting")
            self.threadlock.release()
            return
        
        factions_inf = dict()
        debug("MISSION_COMPLETE: created empty dict for influence")
        for faction in entry["FactionEffects"]:
            debug("MISSION_COMPLETE: current faction: " + str(faction))
            # на случай, если вторая фракция не прописана в ивенте
            if faction["Faction"] == "":
                debug("MISSION_COMPLETE: WARNING: second faction is empty")
                if completed_mission["faction2"] == "":     # её нет и в MissionAccepted: игнорируем
                    debug("MISSION_COMPLETE: second faction not found in MissionAccepted, ignoring")
                    continue
                else:                                       # она есть в MissionAccepted: копируем оттуда
                    debug("MISSION_COMPLETE: second faction found in MissionAccepted, copying")
                    faction["Faction"] = completed_mission["faction2"]
            factions_inf[faction["Faction"]] = len(faction["Influence"][0]["Influence"])
            debug("MISSION_COMPLETE: influence written: " + str(factions_inf[faction["Faction"]]))
            if faction["Influence"][0]["Trend"] == "DownBad":
                debug("MISSION_COMPLETE: trend 'downbad', changing sign to minus")
                factions_inf[faction["Faction"]] *= -1
        
        url_params = {
                "entry.1839270329": cmdr,
                "entry.1889332006": completed_mission["type"],
                "entry.350771392": "COMPLETED",
                "entry.592164382": completed_mission["system"],
                "entry.1812690212": completed_mission["faction"],
                "entry.179254259": factions_inf[completed_mission["faction"]],
                "entry.739461351": completed_mission["system2"],
                "entry.887402348": completed_mission["faction2"],
                "entry.1755429366": factions_inf.get(completed_mission["faction2"], ""),
            }
        url = f'{URL_GOOGLE}/1FAIpQLSdlMUq4bcb4Pb0bUTx9C6eaZL6MZ7Ncq3LgRCTGrJv5yNO2Lw/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(str(v), safe=str())}" for k, v in url_params.items()])}'
        debug("MISSION_COMPLETE: link: " + url)
        Reporter(url).start()
        debug("MISSION_COMPLETE: successfully sent to google sheet")


    def __missionFailed(self, entry, cmdr):
        debug("MISSION_FAILED: detected MissionFailed")
        with open(self.CURRENT_MISSIONS_FILE, "r", encoding="utf8") as missions_file:
            missions_list = missions_file.readlines()
            debug("MISSION_FAILED: read currentmissions")
        failed_mission = dict()
        debug("MISSION_FAILED: created emtpy dict 'failed_mission'")
        with open(self.CURRENT_MISSIONS_FILE, "w", encoding="utf8") as missions_file:
            debug("MISSION_FAILED: opened currentmissions for editing")
            for line in missions_list:
                mission = json.loads(line)
                debug("MISSION_FAILED: mission: " + str(mission))
                if mission["ID"] != entry["MissionID"]:
                    debug("MISSION_FAILED: not what we're looking for, saving to currentmissions")
                    missions_file.write(line)
                else:
                    debug("MISSION_FAILED: found what we're looking for, completed_mission = mission")
                    failed_mission = mission
        if failed_mission == {}:
            debug("MISSION_FAILED: WARNING: mission not found, exiting")
            self.threadlock.release()
            return

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
            }
        url = f'{URL_GOOGLE}/1FAIpQLSdlMUq4bcb4Pb0bUTx9C6eaZL6MZ7Ncq3LgRCTGrJv5yNO2Lw/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(str(v), safe=str())}" for k, v in url_params.items()])}'
        debug("MISSION_FAILED: link: " + url)
        Reporter(url).start()
        debug("MISSION_FAILED: successfully sent to google sheet")


    def __missionAbandoned(self, entry):
        debug("MISSION_ABANDONED: detected MissionAbandoned")
        with open(self.CURRENT_MISSIONS_FILE, "r", encoding="utf8") as missions_file:
            missions_list = missions_file.readlines()
            debug("MISSION_ABANDONED: read currentmissions")
        with open(self.CURRENT_MISSIONS_FILE, "w", encoding="utf8") as missions_file:
            debug("MISSION_ABANDONED: opened currentmissions for editing")
            for line in missions_list:
                mission = json.loads(line)
                debug("MISSION_ABANDONED: mission: " + str(mission))
                if mission["ID"] != entry["MissionID"]:
                    debug("MISSION_ABANDONED: not id we're searching for. writing to file")
                    missions_file.write(line)
                elif mission["type"] == "Mission_HackMegaship" or mission["type"] == "MISSION_DisableMegaship":
                    debug("MISSION_ABANDONED: id found, but it's related to megaships - writing to file")
                    missions_file.write(line)
                else:
                    debug("MISSION_ABANDONED: found id, skipping")


    def __redeemVoucher(self, entry, cmdr, system):
        if self.mainfaction != "FleetCarrier":
            if "BrokerPercentage" not in entry:                 # игнорируем юристов
                debug("REDEEM_VOUCHER: detected RedeemVoucher")
                if entry["Type"] != "bounty":
                    debug(f"REDEEM_VOUCHER: type \"{entry['Type']}\", skipping")
                else:
                    debug("REDEEM_VOUCHER: type \"Bounty\"")
                    for faction in entry["Factions"]:
                        debug("REDEEM_VOUCHER: current faction: " + str(faction))
                        url_params = {
                            "entry.503143076": cmdr,
                            "entry.1108939645": "bounty",
                            "entry.127349896": system,
                            "entry.442800983": "",
                            "entry.48514656": faction["Faction"],
                            "entry.351553038": faction["Amount"],
                        }
                        url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(str(v), safe=str())}" for k, v in url_params.items()])}'
                        debug("REDEEM_VOUCHER: link: " + url)
                        Reporter(url).start()
                        debug("REDEEM_VOUCHER: successfully sent to google sheet")


    def __explorationData(self, entry, cmdr, system, station):
        if self.mainfaction != "FleetCarrier":
            debug(f"SELL_EXP_DATA: detected \"{entry['event']}\"")
            url_params = {
                "entry.503143076": cmdr,
                "entry.1108939645": "SellExpData",
                "entry.127349896": system,
                "entry.442800983": station,
                "entry.48514656": self.mainfaction,
                "entry.351553038": entry["TotalEarnings"],
            }
            url = f'{URL_GOOGLE}/1FAIpQLSenjHASj0A0ransbhwVD0WACeedXOruF1C4ffJa_t5X9KhswQ/formResponse?usp=pp_url&{"&".join([f"{k}={quote_plus(str(v), safe=str())}" for k, v in url_params.items()])}'
            debug("SELL_EXP_DATA: link: " + url)
            Reporter(url).start()
            debug("SELL_EXP_DATA: successfully sent to google sheet")


    def __del__(self):
        self.threadlock.acquire()
        # Очистка файла миссий от устаревших, чей результат выполнения не был "пойман"
        debug("Clearing missions file from old entries")
        missionslist = []
        with open(self.CURRENT_MISSIONS_FILE, 'r', encoding='utf8') as missionsfile:
            count = 0
            for line in missionsfile:
                missionslist.append(line)
                count += 1
            debug(f"Missions read: {count}")
        with open(self.CURRENT_MISSIONS_FILE, 'w', encoding='utf8') as missionsfile:
            now = datetime.now(tz=timezone.utc)
            count = 0
            for line in missionslist:
                mission = json.loads(line)
                try:
                    expires = datetime.strptime(mission["expires"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                except KeyError:
                    debug(f"Mission {mission['ID']} is written in old format and doesn't have 'expires' field, adding back to file.")
                    missionsfile.write(line)
                    count += 1
                else:
                    if expires > now:
                        missionsfile.write(line)
                        count += 1
                    else:
                        debug(f"Mission {mission['ID']} expired.")
            debug(f"Missions written: {count}")
        self.threadlock.release()



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
                    self.__end_conflict()
            except TypeError:       # если сообщений <5, [4] будет None
                pass

    
    def __end_conflict(self, entry = None):
        try:
            allegience = entry["From"][19:-1]
        except KeyError:
            allegience = None

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