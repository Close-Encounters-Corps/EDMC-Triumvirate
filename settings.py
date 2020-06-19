users_base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTXE8HCavThmJt1Wshy3GyF2ZJ-264SbNRVucsPUe2rbEgpm-e3tqsX-8K2mwsG4ozBj6qUyOOd4RMe/pub?gid=1832580214&single=true&output=tsv"
news_url = "https://docs.google.com/spreadsheets/d/1UnrH5ULSycKzySonUDA79aPBqxUbvNOEOSlW85NY1a0/export?&format=csv"
canonn_patrols_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSMFJL2u0TbLMAQQ5zYixzgjjsNtGunZ9-PPZFheB4xzrjwR0JPPMcdMwqLm8ioVMp3MP4-k-JsIVzO/pub?gid=282559555&single=true&output=csv"
bgs_tasks_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQQZFJ4O0nb3L1WJk5oMEPJrr1w5quBSnPRwSbz66XCYx0Lq6aAexm9s1t8N8iRxpdbUOtrhKqQMayY/pub?gid=0&single=true&output=csv"
edsm_poi_url = "https://www.edsm.net/en/galactic-mapping/json"

ships = {
    "adder": " Adder",
    "typex_3": " Alliance Challenger",
    "typex": " Alliance Chieftain",
    "typex_2": " Alliance Crusader",
    "anaconda": "а Anaconda",
    "asp explorer": " Asp Explorer",
    "asp": " Asp Explorer",
    "asp scout": " Asp Scout",
    "asp_scout": " Asp Scout",
    "beluga liner": "а Beluga Liner",
    "belugaliner": "а Beluga Liner",
    "cobra mk. iii": "а Cobra MkIII",
    "cobramkiii": "а Cobra MkIII",
    "cobra mk. iv": "а Cobra MkIV",
    "cobramkiv": "а Cobra MkIV",
    "diamondback explorer": " Diamondback Explorer",
    "diamondbackxl": " Diamondback Explorer",
    "diamondback scout": " Diamondback Scout",
    "diamondback": " Diamondback Scout",
    "dolphin": " Dolphin",
    "eagle": " Eagle",
    "federal assault ship": " Federal Assault Ship",
    "federation_dropship_mkii": " Federal Assault Ship",
    "federal corvette": " Federal Corvette",
    "federation_corvette": " Federal Corvette",
    "federal dropship": " Federal Dropship",
    "federation_dropship": " Federal Dropship",
    "federal gunship": " Federal Gunship",
    "federation_gunship": " Federal Gunship",
    "fer-de-lance": " Fer-de-Lance",
    "ferdelance": " Fer-de-Lance",
    "hauler": " Hauler",
    "imperial clipper": " Imperial Clipper",
    "empire_trader": " Imperial Clipper",
    "imperial courier": " Imperial Courier",
    "empire_courier": " Imperial Courier",
    "imperial cutter": " Imperial Cutter",
    "cutter": " Imperial Cutter",
    "empire_eagle": " Imperial Eagle",
    "keelback": " Keelback",
    "independant_trader": " Keelback",  # ???
    "krait_mkii": " Krait MkII",
    "krait_light": " Krait Phantom",
    "mamba": "а Mamba",
    "orca": "а Orca",
    "python": " Python",
    "sidewinder": " Sidewinder",
    "type 6 transporter": " Type-6 Transporter",
    "type6": " Type-6 Transporter",
    "type 7 transporter": " Type-7 Transporter",
    "type7": " Type-7 Transporter",
    "type 9 heavy": " Type-9 Heavy",
    "type9": " Type-9 Heavy",
    "type 10 defender": " Type-10 Defender",
    "type9_military": " Type-10 Defender",
    "viper mk. iii": " Viper MkIII",
    "viper": " Viper MkIII",
    "viper mk. iv": " Viper MkIV",
    "viper_mkiv": " Viper MkIV",
    "vulture": "а Vulture",
}

states = {
    "civilliberty": "Гражданские свободы",
    "none": "",
    "boom": "Бум",
    "bust": "Спад",
    "civilunrest": "Гражданские беспорядки",
    "civilwar": "Гражданская война",
    "election": "Выборы",
    "expansion": "Экспансия",
    "famine": "Голод",
    "investment": "Инвестиции",
    "lockdown": "Изоляция",
    "outbreak": "Эпдемия",
    "retreat": "Отступление",
    "war": "Война",
}
####################
### SOS settings ###
####################
life_supports_sizes = {
    "class1": "5:00",
    "class2": "7:30",
    "class3": "10:00",
    "class4": "15:00",
    "class5": "25:00",
}
fuel_icon_url = "https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png"
fuel_reservoirs = {
    "sidewinder": 0.3,
    "eagle": 0.34,
    "hauler": 0.25,
    "adder": 0.36,
    "empire_eagle": 0.37,
    "viper": 0.41,
    "cobramkiii": 0.49,
    "viper_mkiv": 0.46,
    "diamondback": 0.49,
    "cobramkiv": 0.51,
    "type6": 0.39,
    "dolphin": 0.5,
    "diamondbackxl": 0.52,
    "empire_courier": 0.41,
    "independant_trader": 0.39,
    "asp_scout": 0.47,
    "vulture": 0.57,
    "asp": 0.63,
    "federation_dropship": 0.83,
    "type7": 0.52,
    "typex": 0.77,
    "federation_dropship_mkii": 0.72,
    "empire_trader": 0.74,
    "typex_2": 0.77,
    "typex_3": 0.77,
    "federation_gunship": 0.82,
    "krait_light": 0.63,
    "krait_mkii": 0.63,
    "orca": 0.79,
    "ferdelance": 0.67,
    "mamba": 0.5,
    "python": 0.83,
    "type9": 0.77,
    "belugaliner": 0.81,
    "type9_military": 0.77,
    "anaconda": 1.07,
    "federation_corvette": 1.13,
    "cutter": 1.16,
}


##########################
### whitelist settings ###
##########################
whitelist_list_url = "https://us-central1-canonn-api-236217.cloudfunctions.net/whitelist"
whitelist_submit_url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitRaw"


###############################
### systems module settings ###
###############################
systems_static_coords = {
    "HIP 18609": [-15.96875, -85.65625, -173.90625],
    "Kagutsuchi": [-11.5, -84.5625, -162.65625],
    "HIP 18843": [-9.5625, -87.40625, -173.5],
    "Arietis Sector EQ-Y c17": [-24.53125, -87.6875, -166.4375],
    "Arietis Sector DQ-Y c16": [-28.125, -79.8125, -157.03125],
    "HIP 20827": [4.96875, -65.65625, -158.5625],
    "Obamumbo": [-9.03125, -78.59375, -152.90625],
    "Gaezatorix": [-0.78125, -74.375, -149.15625],
    "Arietis Sector DQ-Y c18": [-27.28125, -71.9375, -168.9375],
    "Scythia": [6.75, -76.90625, -150.34375],
    "HIP 20419": [9.625, -73.0625, -153.375],
    "HIP 17305": [-35.25, -72.53125, -153.9375],
    "HIP 15412": [-41.0625, -100.875, -159.21875],
    "Bhillke": [-0.59375, -83.09375, -137.21875],
    "HIP 19757": [10.3125, -82.3125, -153.125],
    "Jataya": [-36.40625, -67.96875, -152.71875],
    "HIP 19796": [6.34375, -67.4375, -130.40625],
    "51 Tauri": [-16.25, -59.09375, -165.34375],
    "Arietis Sector OS-T b3-0": [-39.5625, -81.59375, -144.15625],
    "Kara": [-29.75, -58.8125, -163.15625],
    "HIP 16405": [-34.875, -78.71875, -144.71875],
    "Hreidmarda": [-38.59375, -78.28125, -140.3125],
    "Wolf 1268": [-48.40625, -65.0625, -167.25],
    "Paesan": [-47.5, -77.46875, -138.59375],
    "UX Arietis": [-53.25, -64.09375, -146.34375],
    "Arietis Sector IR-V b2-0": [-33.78125, -52.71875, -163.875],
    "Cocassetsa": [-53.96875, -84.3125, -134.625],
    "BD+20 518": [-46.28125, -88.59375, -142.84375],
    "HIP 15278": [-51.84375, -83.625, -152.90625],
    "Tujila": [-64.375, -62.875, -153.875],
    "LHS 1020": [20.78125, -77.125, 25.625],
    "Sanna": [35.96875, -83.3125, 23.125],
    "HDS 3215": [31.53125, -54.21875, 40.78125],
    "Euryale": [35.375, -68.96875, 24.8125],
    "Chup Kamui": [26.28125, -39.15625, 21.5],
    "LTT 305": [27.6875, -75.28125, 21.8125],
    "Fjorgyn": [38.375, -43.71875, 42.125],
    "Mamaragan": [33.875, -49.09375, 26.4375],
    "Gebel": [23.40625, -50.90625, 29.375],
    "Arare": [28.125, -40.5625, 30.78125],
    "Aparctias": [25.1875, -56.375, 22.90625],
    "Kerebaei": [50.96875, -67.875, 6.9375],
    "LTT 9181": [31.96875, -61.6875, 43.03125],
    "Mat Zemlya": [37.03125, -56.5, 24.71875],
    "LFT 78": [33, -58.875, 21.71875],
    "LTT 9387": [33.15625, -49.21875, 33.8125],
    "CD-61 6651": [25.53125, -55.15625, 46.4375],
    "Putamasin": [37.21875, -76.375, 21.28125],
    "Kappa Tucanae": [39.5625, -51.0625, 22.28125],
    "Chapsugaibo": [42.5625, -80.78125, 10.0625],
    "L 119-33": [25.1875, -43.375, 34.34375],
    "LHS 1379": [38.34375, -64.03125, 5.125],
    "Veroandi": [33.15625, -37.625, 32.25],
    "LTT 700": [40.78125, -52.8125, 23.03125],
    "LHS 3615": [8.65625, -37.78125, 42.09375],
    "Nanabozho": [22.9375, -35.75, 24.15625],
    "CPC 20 6743": [23.71875, -55.90625, 54.9375],
    "Lauksa": [17.8125, -33.96875, 60.6875],
    "Caelinus": [0.1875, -18.625, 52.0625],
    "LFT 1442": [8.375, -17, 41.875],
    "Tiolce": [10.5, -34.78125, 25.0625],
    "Algreit": [-8.3125, -11.78125, 53.28125],
    "Clayakarma": [-20.5, -4.96875, 60.6875],
    "Rishalu": [18.625, -32.25, 59.4375],
    "Ullese": [35.75, -73.78125, 38.96875],
    "LTT 464": [22.8125, -64.96875, 14.8125],
    "LP 91-140": [38.71875, -35.53125, 9.84375],
    "LFT 1594": [10.78125, -27.125, 29.46875],
    "Viracocha": [14, -46.4375, 9.65625],
    "LFT 141": [28.6875, -67.1875, 6.65625],
    "Nabatean": [23.125, -66.28125, 22.46875],
    "Two Ladies": [19.625, -51.8125, 37.8125],
    "Long": [31.6875, -89.5, 17.84375],
    "LTT 1044": [39.84375, -77.75, 6.96875],
    "Gami Musu": [8.3125, -82.875, 20.0625],
    "Obotrima": [24.1875, -67.53125, -0.6875],
    "Cerktondhs": [-5.0625, -23.5625, 59.25],
    "Aeternitas": [-1.5, -14.65625, 56.875],
    "Ahemez": [-103.34375, -84.6875, -75.875],
    "Krivasho": [-101.375, -84, -76.9375],
    "Arietis Sector KC-V c2-20": [-95.78125, -80.96875, -79.78125],
    "Marmatae": [-99.21875, -92.84375, -84.03125],
    "San Guojin": [-101.25, -78.34375, -88.15625],
    "HIP 2824": [-112.375, -84.78125, -63.78125],
    "Tzeltal": [-118.5, -81.125, -76.9375],
    "T'a Shakarwa": [-87.875, -67.53125, -80.59375],
    "Gucumadhyas": [-89.6875, -97.09375, -76.875],
    "78 Piscium": [-92.15625, -68.375, -71.15625],
    "Orishanann": [-88.28125, -82.28125, -63],
    "Loponnaruai": [-100.90625, -99.125, -81.84375],
    "Kpannon Di": [-97.25, -70.40625, -95.03125],
    "Aonikenk": [-88.96875, -79.5625, -62.34375],
    "HIP 6975": [-88.125, -97.0625, -87.75],
    "HR 415": [-87.875, -61.59375, -78.75],
    "Tz'utumu": [-86.21875, -99.5, -75],
    "Kutnal": [-87.4375, -63.9375, -89.78125],
    "Epsilon Andromedae": [-118.34375, -89.78125, -69.09375],
    "Arietis Sector WK-O b6-5": [-118.9375, -81.6875, -77.96875],
    "Wiyotset": [-115.65625, -80.25, -63.53125],
    "HIP 3428": [-98.6875, -92.65625, -60.34375],
    "Wayano": [-94.03125, -81.28125, -59.46875],
    "Arietis Sector VZ-P b5-5": [-100.125, -95.5625, -94.96875],
    "79 Psi-2 Piscium": [-89.71875, -102.53125, -72.46875],
    "Luchunza": [-89.46875, -103.65625, -64.46875],
    "Wandrama": [-90.25, -103.3125, -94.96875],
    "Gunab": [-100.1875, -104.4375, -83.875],
}
edsm_system_url = "https://www.edsm.net/api-v1/system"

########################
### release settings ###
########################
release_gh_url = "https://github.com/VAKazakov/EDMC-Triumvirate/releases"
release_gh_latest = "https://api.github.com/repos/VAKazakov/EDMC-Triumvirate/releases/latest"
release_zip_template = "https://github.com/VAKazakov/EDMC-Triumvirate/archive/{}.zip"
release_gh_ver_info = "https://api.github.com/repos/VAKazakov/EDMC-Triumvirate/releases/tags/{}"

#####################
### NHSS settings ###
#####################
nhss_canonn_url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitNHSS"

#############
### other ###
#############
support_message = """В случае возникновения проблем с плагином
или в случае, если Вы поставили неправильное сообщество в гугл-форме,
пишите в канал CEC #triumvirate_tech_support или в личку Казаков#4700"""
version = "1.3.0"
