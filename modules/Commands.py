# -*- coding: utf-8 -*-
from . import Discord

import datetime
from .debug import debug


class Range(object):
    """
    Класс, который проверяет на вхождение объектов в диапазон
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __contains__(self, obj):
        return self.start <= obj < self.end

    def __hash__(self):
        return hash((self.start, self.end))

    def __repr__(self):
        return "{}({}, {})".format(
            self.__class__.__name__,
            self.start,
            self.end
        )


def sos(
    cmdr,
    system,
    DistFromStarLS,
    state,
    body,
    lat,
    lon,
    fuel,
    fuel_cons,
    is_SRV,
    is_Fighter,
    args
):
    # TODO переместить в настройки
    LifeSupportList = {
        "int_lifesupport_size1_class1": "5:00",
        "int_lifesupport_size1_class2": "7:30",
        "int_lifesupport_size1_class3": "10:00",
        "int_lifesupport_size1_class4": "15:00",
        "int_lifesupport_size1_class5": "25:00",
        "int_lifesupport_size2_class1": "5:00",
        "int_lifesupport_size2_class2": "7:30",
        "int_lifesupport_size2_class3": "10:00",
        "int_lifesupport_size2_class4": "15:00",
        "int_lifesupport_size2_class5": "25:00",
        "int_lifesupport_size3_class1": "5:00",
        "int_lifesupport_size3_class2": "7:30",
        "int_lifesupport_size3_class3": "10:00",
        "int_lifesupport_size3_class4": "15:00",
        "int_lifesupport_size3_class5": "25:00",
        "int_lifesupport_size4_class1": "5:00",
        "int_lifesupport_size4_class2": "7:30",
        "int_lifesupport_size4_class3": "10:00",
        "int_lifesupport_size4_class4": "15:00",
        "int_lifesupport_size4_class5": "25:00",
        "int_lifesupport_size5_class1": "5:00",
        "int_lifesupport_size5_class2": "7:30",
        "int_lifesupport_size5_class3": "10:00",
        "int_lifesupport_size5_class4": "15:00",
        "int_lifesupport_size5_class5": "25:00",
        "int_lifesupport_size6_class1": "5:00",
        "int_lifesupport_size6_class2": "7:30",
        "int_lifesupport_size6_class3": "10:00",
        "int_lifesupport_size6_class4": "15:00",
        "int_lifesupport_size6_class5": "25:00",
        "int_lifesupport_size7_class1": "5:00",
        "int_lifesupport_size7_class2": "7:30",
        "int_lifesupport_size7_class3": "10:00",
        "int_lifesupport_size7_class4": "15:00",
        "int_lifesupport_size7_class5": "25:00",
        "int_lifesupport_size8_class1": "5:00",
        "int_lifesupport_size8_class2": "7:30",
        "int_lifesupport_size8_class3": "10:00",
        "int_lifesupport_size8_class4": "15:00",
        "int_lifesupport_size8_class5": "25:00",
    }
    FuelReserwours = {
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
    debug("Sos Initiated")
    params = {}

    if state["Role"]:
        # Эта команда прервет выполнение, если
        # игрок находится в мульткрю
        return "Вы находитесь в экипаже, SOS отключено"
    if is_SRV:
        # эта команда прервет выполнение, если
        # игрок находится в СРВ (Если ЕДМС
        # передаст эту инфу)
        return "SOS отключен, пока вы в СРВ"
    if is_Fighter:
        return "SOS отключен, пока вы в Истребителе"
    if DistFromStarLS is not None:
        Distance = str(",\n" + str(DistFromStarLS) + " Св.Сек.")
    else:
        Distance = str("")

    debug(body)
    if body is not None:
        Body = str(",\nу " + body)
    else:
        Body = ""

    LifeSupport = state["Modules"]["LifeSupport"]["Item"]
    debug("Fuel: {}", fuel)
    current_fuel = fuel["FuelMain"] + fuel["FuelReservoir"]
    reservoir_capacity = FuelReserwours[state["ShipType"]]
    debug("Reservoir capacity: {}", reservoir_capacity)
    current_fuel_share = current_fuel / reservoir_capacity
    debug("Current fuel share: {}", current_fuel_share)

    # TODO переписать на алгоритм генерации цвета вместо словаря
    share_colors = {
        Range(0.9, 1.0): 0xffe600,
        Range(0.8, 0.9): 0xffcd00,
        Range(0.7, 0.8): 0xffb400,
        Range(0.6, 0.7): 0xff9b00,
        Range(0.5, 0.6): 0xff8200,
        Range(0.4, 0.5): 0xff6900,
        Range(0.3, 0.4): 0xff5200,
        Range(0.2, 0.3): 0xff5200,
        Range(0.1, 0.2): 0xff1e00,
        Range(0.0, 0.1): 0xff0500,
    }

    # чисто жёлтый цвет в случае если в баке
    # есть какое-то количество топлива
    color = 0xffff00
    for range_, val in share_colors.iteritems():
        if current_fuel_share in range_:
            color = val
            break

    debug("Color: {}", hex(color))

    avatar_url = "https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png" # noqa E501
    if current_fuel != 0:
        debug("Fuel consumption: {}", fuel_cons)
        location = system + Distance + Body
        debug("Location: {}", location)
        debug("Location (repr): {}", repr(location))
        location = str(location)
        if fuel_cons != 0:
            sec_to_go = round(current_fuel / fuel_cons, 3)

            time_to_go = datetime.timedelta(seconds=sec_to_go)

            params.update(
                {
                    "Etitle": "SOS",
                    "EDesc": str("Требуется заправка"),
                    "EColor": color,
                    "Avatar": avatar_url,
                    "Foouter": "Расчетное время отключения:",
                    "Timestamp": (time_to_go),
                    "Embed?": True,
                    "Fields": {
                        str("Местоположение:"): str(system + Distance + Body),
                        str("Топлива осталось:"): str(
                            str(round(current_fuel, 2))
                            + " тонн"
                        ),
                        str("Времени до отключения:"): str((time_to_go)),
                    },
                }
            )
        else:
            params.update(
                {
                    "Etitle": "SOS",
                    "EDesc": str("Требуется заправка"),
                    "EColor": color,
                    "Avatar": avatar_url,
                    "Embed?": True,
                    "Fields": {
                        str("Местоположение:"): str(system + Distance + Body),
                        str("Топлива осталось:"): str(
                            str(round(current_fuel, 2))
                            + " тонн"
                        ),
                        str("Времени до отключения:"): str("Не кончится"),
                    },
                }
            )
    else:
        params.update(
            {
                "Etitle": "SOS",
                "EDesc": str(
                    "Срочно требуется топливо, произведено отключение всех систем!!!" # noqa E501
                ),
                "EColor": "16711680",
                "Avatar": avatar_url,
                "Foouter": str("Расчетное время смерти:"),
                "Timestamp": (time_to_go),
                "Embed?": True,
                "Fields": {
                    str("Местоположение:"): str(system + Distance + Body),
                    str("Топлива осталось:"): str(
                        str(round(current_fuel, 2))
                        + " тонн"
                    ),
                    str("Кислород кончится через (прим.):"): LifeSupportList[
                        LifeSupport
                    ],
                },
            }
        )
    debug("Параметры SOS-запроса: {}", params)
    if "test" not in args:
        Discord.Sender(cmdr, "FuelAlarm", params)
    return "Сигнал о помощи послан, ожидайте помощь"


def commands(
    cmdr,
    is_beta,
    system,
    SysFactionState,
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
    fuel,
    fuel_cons,
    is_SRV,
    is_Fighter,
):
    if entry["event"] == "SendText":
        args = entry["Message"].lower().split()
        command = args[0]
        args = args[1:]
        if command == "/sos":
            debug("SOS args: {}", args)
            return sos(
                cmdr,
                system,
                DistFromStarLS,
                state,
                body,
                lat,
                lon,
                fuel,
                fuel_cons,
                is_SRV,
                is_Fighter,
                args=args
            )
