canonn_patrols_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSMFJL2u0TbLMAQQ5zYixzgjjsNtGunZ9-PPZFheB4xzrjwR0JPPMcdMwqLm8ioVMp3MP4-k-JsIVzO/pub?gid=282559555&single=true&output=csv"
bgs_tasks_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQQZFJ4O0nb3L1WJk5oMEPJrr1w5quBSnPRwSbz66XCYx0Lq6aAexm9s1t8N8iRxpdbUOtrhKqQMayY/pub?gid=0&single=true&output=csv"
edsm_poi_url = "https://www.edsm.net/en/galactic-mapping/json"
edsm_url = "https://www.edsm.net"

#####################
### CEC ENDPOINTS ###
#####################
cec_url = "https://closeencounterscorps.org"
galaxy_url = "https://api-galaxy.closeencounterscorps.org"

###################
### CANONN URLS ###
###################
canonn_realtime_url = "https://us-central1-canonn-api-236217.cloudfunctions.net"

ships = {  #Некоторые корабли имеют "а" перед названием, потому что этот словарь используется  для подстановки типов в сообщение с учетом женского рода
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
    "none": "Нет данных",
    "boom": "Бум",
    "bust": "Спад",
    "civilunrest": "Гражданские беспорядки",
    "civilwar": "Гражданская война",
    "election": "Выборы",
    "expansion": "Экспансия",
    "famine": "Голод",
    "investment": "Инвестиции",
    "lockdown": "Изоляция",
    "outbreak": "Эпидемия",
    "retreat": "Отступление",
    "war": "Война",
}

odyssey_events = [
    "BookDropship",
    "BookTaxi",
    "BuyMicroResources",
    "BuySuit",
    "BuyWeapon",
    "CollectItems",
    "CreateSuitLoadout",
    "DeleteSuitLoadout",
    "DeleteSuitLoadout",
    "DropShipDeploy",
    "Disembark",
    "Embark",
    "FCMaterials",
    "LoadoutEquipModule",
    "LoadoutRemoveModule",
    "RenameSuitLoadout",
    "ScanOrganic",
    "SellMicroResources",
    "SellOrganicData",
    "SellSuit",
    "SellWeapon",
    "SwitchSuitLoadout",
    "TransferMicroResources",
    "TradeMicroResources",
    "TradeMicroResources",
    "UpgradeWeapon",
    "UpgradeWeapon"
]


########################
### release settings ###
########################
release_gh_url = "https://github.com/Close-Encounters-Corps/EDMC-Triumvirate/releases"
release_gh_latest = "https://api.github.com/repos/Close-Encounters-Corps/EDMC-Triumvirate/releases/latest"
release_zip_template = "https://github.com/Close-Encounters-Corps/EDMC-Triumvirate/archive/{}.zip"
release_gh_ver_info = "https://api.github.com/repos/Close-Encounters-Corps/EDMC-Triumvirate/releases/tags/{}"

#####################
### NHSS settings ###
#####################
nhss_canonn_url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitNHSS"

#############
### other ###
#############
support_message = """В случае возникновения проблем с плагином обращайтесь в дискорд Close Encounters Corps, канал #triumvirate_tech_support, в личные сообщения Казаков#4700 или на почтовый адрес help@cec.org"""

"""
Используется семантическое версионирование.
Для себя для процесса разработки выбрал следующий алгоритм именования:
0) Предположим, последняя публичная тестовая версия - 1.11.0-beta.1
1) При дальнейшей разработке версию меняем на 1.11.0-beta.1.indev
2) В последнем коммите после завершения работы над следующей бетой и перед её выпуском меняем версию на 1.11.0-beta.2
Таким образом соблюдается корректность алгоритма сравнения номеров версий, указанного в спецификации semantic versioning 2.0.0.
"""
version = "1.11.1-beta.1.indev"

try:
    from settings_local import *
except ImportError:
    pass