import csv
import requests
import webbrowser
from contextlib import closing
from math import pow, sqrt
from urllib.parse import quote_plus

from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.shortcuts import debug, error
from Triumvirate.lib.thread import BasicThread


URL_GOOGLE = 'https://docs.google.com/forms/d/e'


class GoogleReporter(BasicThread):
    STANDARD_RETRY_DELAY = 10
    LONG_RETRY_DELAY = 10 * 60
    MAX_ATTEMPTS = 10

    def __init__(self, url: str, params: dict | None = None):
        super().__init__()
        self.url = url
        self.params = params

    def run(self):
        n_attempt = 1
        while n_attempt != self.MAX_ATTEMPTS + 1:
            try:
                response = requests.post(self.url, self.params)
            except Exception as e:
                error(f"Couldn't send data: url {self.url!r}, params {self.params!r}, exception info:", exc_info=e)
                return

            if response.ok:
                debug(f"Data sent successfully: url {self.url!r}, params {self.params!r} ({n_attempt} attempts).")
                return

            elif response.status_code == 408:  # таймаут, есть смысл попытаться ещё
                error(f"Couldn't send data (418 Timeout): url {self.url!r}, params {self.params!r} ({n_attempt} attempts).")
                n_attempt += 1
                self.sleep(self.STANDARD_RETRY_DELAY)

            elif response.status_code == 429:  # слишком много запросов, подождём подольше
                error(f"Couldn't send data (429 Too many requests): url {self.url!r}, params {self.params!r} ({n_attempt} attempts).")
                n_attempt += 1
                self.sleep(self.LONG_RETRY_DELAY)

            elif response.status_code < 500:  # всё остальное из 4XX пытаться повторять смысла нет
                error(f"Coundn't send data (code {response.status_code}): url {self.url!r}, params {self.params!r}. Aborting.")
                return

            else:  # 5XX можно попытаться повторить
                error(
                    f"Coundn't send data (code {response.status_code}): "
                    f"url {self.url!r}, params {self.params!r} ({n_attempt} attempts)."
                )
                n_attempt += 1
                self.sleep(self.STANDARD_RETRY_DELAY)


def getDistance(x1, y1, z1, x2, y2, z2):
    return round(sqrt(pow(float(x2) - float(x1), 2) + pow(float(y2) - float(y1), 2) + pow(float(z2) - float(z1), 2)), 2)


def getDistanceMerope(x1, y1, z1):
    x, y, z = -78.59375, -149.625, -340.53125
    return round(sqrt(pow(float(x) - float(x1), 2) + pow(float(y) - float(y1), 2) + pow(float(z) - float(z1), 2)), 2)


def getDistanceSol(x1, y1, z1):
    return round(sqrt(pow(float(0) - float(x1), 2) + pow(float(0) - float(y1), 2) + pow(float(0) - float(z1), 2)), 2)


def matches(d, field, value):
    return field in d and value == d[field]


last_body_with_biosignals = ""
def GusonExpeditions(cmdr, is_beta, system, entry):  # noqa: E302
    if GameState.gamemode != 'MainGame':
        return
    # рекоды: количество тел
    if entry.get('event') == 'FSSDiscoveryScan':
        if entry.get('BodyCount') >= 150:
            params = {
                "usp": "pp_url",
                "entry.1258689641": cmdr,
                "entry.1469465131": entry.get("SystemName", ""),
                "entry.1583990022": "BodyCount",
                "entry.1301773715": entry.get("BodyCount", ""),
            }
            url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
            GoogleReporter(url, params).start()

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
            params = {
                "usp": "pp_url",
                "entry.1258689641": cmdr,
                "entry.1469465131": entry.get("BodyName", ""),
                "entry.1583990022": f'HighMass{planetClass}',
                "entry.1301773715": str(mass).replace('.', ','),
            }
            url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
            GoogleReporter(url, params).start()

        # рекорды: горячие юпитеры
        if "gas giant" in entry.get("PlanetClass").lower():
            if entry.get("SurfaceTemperature") > 9352.83:
                params = {
                    "usp": "pp_url",
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HotJupiter",
                    "entry.1301773715": str(entry.get("SurfaceTemperature")).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
                GoogleReporter(url, params).start()

        # рекорды: радиус колец
        if "Rings" in entry:
            rings = entry.get("Rings")
            for ring in rings:
                outerRad = str(ring.get("OuterRad"))
                outerRad = outerRad[:outerRad.find('.')]
                if float(outerRad) >= 34732000000:
                    params = {
                        "usp": "pp_url",
                        "entry.1258689641": cmdr,
                        "entry.1469465131": ring.get("Name"),
                        "entry.1583990022": "WideRing",
                        "entry.1301773715": outerRad[:-3],
                    }
                    url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
                    GoogleReporter(url, params).start()

        if entry.get("Landable") is True:
            # рекорды: температура посадочных
            if entry.get("SurfaceTemperature") > 5115.9:
                params = {
                    "usp": "pp_url",
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HighTemperature",
                    "entry.1301773715": entry.get("SurfaceTemperature"),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
                GoogleReporter(url, params).start()

            # рекорды: радиус посадочных
            if entry.get("Radius") / 1000 > 25444:
                params = {
                    "usp": "pp_url",
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HugeRadius",
                    "entry.1301773715": str(entry.get("Radius")).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
                GoogleReporter(url, params).start()
            elif entry.get("Radius") <= 138000:
                params = {
                    "usp": "pp_url",
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "TinyRadius",
                    "entry.1301773715": str(entry.get("Radius") / 1000).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
                GoogleReporter(url, params).start()

            # рекорды: гравитация посадочных
            if entry.get("SurfaceGravity") / 10 > 7.51:
                params = {
                    "usp": "pp_url",
                    "entry.1258689641": cmdr,
                    "entry.1469465131": entry.get("BodyName", ""),
                    "entry.1583990022": "HighGravity",
                    "entry.1301773715": str(entry.get("SurfaceGravity") / 10).replace('.', ','),
                }
                url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
                GoogleReporter(url, params).start()

    # рекорды: орбитальный период
    if "OrbitalPeriod" in entry:
        if entry.get("OrbitalPeriod") <= 1800:
            params = {
                "usp": "pp_url",
                "entry.1258689641": cmdr,
                "entry.1469465131": entry.get("BodyName"),
                "entry.1583990022": "OrbitalPeriod",
                "entry.1301773715": entry.get("OrbitalPeriod"),
            }
            url = f'{URL_GOOGLE}/1FAIpQLSfFr7ezqpQ4cnw99bJ-lOIW-6QtKRArhgDNtSj8eLtPoILXUg/formResponse'
            GoogleReporter(url, params).start()

    if "PlanetClass" in entry:
        # БД атмосферных и рекорды - ГГ
        if "gas giant" in entry.get("PlanetClass").lower():
            helium_percentage = 0.0
            for comp in entry.get("AtmosphereComposition", []):
                if comp["Name"] == "Helium":
                    helium_percentage = comp["Percent"]

            # общая БД
            params = {
                "usp": "pp_url",
                "entry.262880086": entry.get("BodyName", ""),
                "entry.808713567": str(helium_percentage).replace('.', ','),
                "entry.549950938": entry.get("StarSystem", "")
            }
            url = f'{URL_GOOGLE}/1FAIpQLSeVvva2K9VMJZyr4mJ9yRnQPXhcDHUwO8iTxrg2z1Qi4lJk_Q/formResponse'
            GoogleReporter(url, params).start()

            # БД Boepp (экспедиционная)
            if "Boepp " in entry["BodyName"]:
                params = {
                    "usp": "pp_url",
                    "entry.207321892": entry.get("BodyName", ""),
                    "entry.318090096": str(helium_percentage).replace('.', ','),
                    "entry.1828517199": entry.get("StarSystem", "")
                }
                url = f'{URL_GOOGLE}/1FAIpQLSeCRZ9GXprtSEUFgUOMR5yBGkqYpdrKAumLkYH6KkPOUq3sIA/formResponse'
                GoogleReporter(url, params).start()

            # рекорды
            params = {
                "usp": "pp_url",
                "entry.280367197": entry.get("BodyName", ""),
                "entry.779566159": str(helium_percentage).replace('.', ','),
                "entry.1789316283": entry.get("StarSystem", "")
            }
            url = f'{URL_GOOGLE}/1FAIpQLSc6mPwibfkLDyVklC7bEiJsNOtcE8pE9OS2b9o3FpBDNiaN4g/formResponse'
            GoogleReporter(url, params).start()

        # Картография
        valuable = False
        if entry["PlanetClass"] in ("Earthlike body", "Ammonia world"):
            valuable = True
        elif entry["PlanetClass"] == "Water world" and entry["TerraformState"] == "Terraformable":
            valuable = True

        known = entry.get("WasMapped") or entry.get("WasDiscovered")

        if valuable and not known:
            params = {
                "usp": "pp_url",
                "entry.2022004794": cmdr,
                "entry.1225803723": entry.get("BodyName", ""),
                "entry.645216132": entry.get("PlanetClass", ""),
                "entry.512641942": str(entry.get("WasDiscovered", "")),
                "entry.1801392650": str(entry.get("WasMapped", "")),
                "entry.1992174852": entry.get("StarSystem", "")
            }
            url = f'{URL_GOOGLE}/1FAIpQLSdgwzvgxow5ATuB4Gimj6DvDRD3-ub3Yp4UD-nQK4CnZdKV9w/formResponse'
            GoogleReporter(url, params).start()

        # БД атмосферных - планеты
        if entry["Landable"] is True:
            if "thin" in entry["Atmosphere"]:
                if "helium" in entry["Atmosphere"] or "oxygen" in entry["Atmosphere"]:
                    gravity_limit = 0.6
                else:
                    gravity_limit = 0.275
                if entry["SurfaceGravity"] / 10 <= gravity_limit:
                    if entry["BodyName"] == last_body_with_biosignals:
                        params = {
                            "usp": "pp_url",
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
                        url = f'{URL_GOOGLE}/1FAIpQLScWkHPhTEHcNCoAwIAbb54AQgg8A6ocX2Ulbfkr2hcubgfbRA/formResponse'
                        GoogleReporter(url, params).start()
                        # БД Boepp (экспедиционная)
                        if "Boepp " in entry["BodyName"]:
                            url = f'{URL_GOOGLE}/1FAIpQLSfrZqrZHJ5T0lgpaoUOcLgM0fXmR_t5_vLKvT7J5HDA8mugeg/formResponse'
                            GoogleReporter(url, params).start()

    # звёзды
    if "StarType" in entry:
        params = {
            "usp": "pp_url",
            "entry.422166846": entry.get("BodyName", ""),
            "entry.371313324": entry.get("StarType", "") + str(entry.get("Subclass", "")) + entry.get("Luminosity"),
            "entry.770073835": entry.get("StarSystem", ""),
            "entry.1133676298": str(entry.get("SurfaceTemperature", "")),
            "entry.786810023": str(entry.get("Age_MY"))
        }
        # общая БД
        url = f'{URL_GOOGLE}/1FAIpQLSdfXA2mLXTamWdz3mXC3Ta3UaJS6anqY4wvzkX-9XzGilZ6Tw/formResponse'
        GoogleReporter(url, params).start()
        # БД Boepp (экспедиционная)
        if "Boepp " in entry["BodyName"]:
            url = f'{URL_GOOGLE}/1FAIpQLSeapH5azc-9T0kIZ4vfDBcDlcd8ZfMUBS42DMRXL8fYcBxRtQ/formResponse'
            GoogleReporter(url, params).start()
        # картография
        params = {
            "entry.1407433679": entry.get("BodyName", ""),
            "entry.741998551": entry.get("StarType", "") + str(entry.get("Subclass", "")) + entry.get("Luminosity"),
            "entry.341231285": entry.get("StarSystem", ""),
            "entry.320405751": str(entry.get("SurfaceTemperature", "")),
            "entry.2033592775": str(entry.get("Age_MY"))
        }
        url = f'{URL_GOOGLE}/1FAIpQLSfYl0iPm-qQOCyD6iVIjK7BPIgnp6yABR2YVwfcp2GB5KWtNA/formResponse'
        GoogleReporter(url, params).start()


def report_version():
    try:
        resp = requests.get('https://api.ipify.org', timeout=3)
        resp.raise_for_status()
        ipv4 = resp.text
    except requests.RequestException as e:
        error(f"Couldn't fetch IPv4 address: {e}")
        ipv4 = None
    try:
        resp = requests.get('https://api6.ipify.org', timeout=3)
        resp.raise_for_status()
        ipv6 = resp.text
    except requests.RequestException as e:
        debug(f"Couldn't fetch IPv6 address. Exception info: {e}")
        ipv6 = None
    if ipv4 is None and ipv6 is None:
        error("Neither IPv4 nor IPv6 are determined. Skipping sending plugin version report.")
        return
    url = "https://docs.google.com/forms/d/1h7LG5dEi07ymJCwp9Uqf_1phbRnhk1R3np7uBEllT-Y/formResponse"
    params = {
        "usp": "pp_url",
        "entry.1181808218": GameState.cmdr,
        "entry.254549730":  str(PluginContext.plugin_version),
        "entry.1622540328": ipv4 or "0",
        "entry.488844173":  ipv6 or "0",
        "entry.1210213202": 1
    }
    GoogleReporter(url, params).start()


def fetch_squadron() -> tuple[str | None, str | None]:
    """
    Возвращает название и ID сквадрона командира из имеющихся у нас данных.
    """
    if GameState.cmdr is None:
        return None, None
    debug("Community Check started")
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTXE8HCavThmJt1Wshy3GyF2ZJ-264SbNRVucsPUe2rbEgpm-e3tqsX-8K2mwsG4ozBj6qUyOOd4RMe/pub?gid=1832580214&single=true&output=tsv"  # noqa: E501
    with closing(requests.get(url, stream=True)) as r:
        reader = csv.reader(r.content.decode('utf-8').splitlines(), delimiter='\t')
        next(reader)
        for row in reader:
            cmdr, squadron, sqid = row
            if cmdr == GameState.cmdr:
                PluginContext.patrol_module.sqid = sqid
                return squadron.upper(), sqid

    debug("Community Check failed: CMDR not found, requesting to fill a form.")
    url = "https://docs.google.com/forms/d/e/1FAIpQLSeERKxF6DlrQ3bMqFdceycSlBV0kwkzziIhYD0ctDzrytm8ug/viewform?usp=pp_url"
    url += "&entry.42820869=" + quote_plus(GameState.cmdr)
    debug(f"SQID {url}")
    webbrowser.open(url)
    return None, None
