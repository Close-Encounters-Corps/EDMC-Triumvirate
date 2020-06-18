# -*- coding: utf-8 -*-
from . import Discord

import datetime
from .debug import debug
from .lib.module import Module
from .lib.context import global_context

import settings

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





class SosModule(Module):
    def on_chat_message(self, entry) -> str:
        message = entry.data["Message"]
        if not message or message.isspace():
            return
        command, *args = message.split()
        command = command.lower()
        # запускаем SOS-сигнал только если сообщение отправил сам командир
        if entry.data["event"] == "SendText" and command == "/sos":
            return self.dispatch_sos(entry, args)

    def dispatch_sos(self, entry, args):
        debug("Sos Initiated")

        if entry.state["Role"]:
            # Эта команда прервет выполнение, если
            # игрок находится в мульткрю
            return "Вы находитесь в экипаже, SOS отключено"
        if global_context.SRVmode:
            # эта команда прервет выполнение, если
            # игрок находится в СРВ (Если ЕДМС
            # передаст эту инфу)
            return "SOS отключен, пока вы в СРВ"
        if global_context.Fightermode:
            return "SOS отключен, пока вы в Истребителе"
        if entry.dist_from_star is not None:
            Distance = str(",\n" + str(entry.dist_from_star) + " Св.Сек.")
        else:
            Distance = str("")

        debug(entry.body)
        if entry.body is not None:
            Body = str(",\nу " + entry.body)
        else:
            Body = ""

        LifeSupport = entry.state["Modules"]["LifeSupport"]["Item"]
        fuel = global_context.fuel
        debug("Fuel: {}", fuel)
        current_fuel = fuel["FuelMain"] + fuel["FuelReservoir"]
        reservoir_capacity = settings.fuel_reservoirs[entry.state["ShipType"]]
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
        for range_, val in share_colors.items():
            if current_fuel_share in range_:
                color = val
                break

        debug("Color: {}", hex(color))

        system = entry.system
        fuel_cons = global_context.fuel_cons
        location = system + Distance + Body
        debug("Fuel consumption: {}", fuel_cons)
        debug("Location: {}", location)

        params = {
            "ETitle": "SOS",
            "EDesc": "Требуется заправка",
            "EColor": color,
            "Avatar": settings.fuel_icon_url,
            "Embed?": True,
            "Fields": {
                "Местоположение": location,
            },
        }
        if args:
            params["Fields"]["Сообщение"] = " ".join(args)

        if current_fuel != 0:
            params["Fields"]["Топлива осталось"] = f"{round(current_fuel, 2)} тонн"
            if fuel_cons != 0:
                sec_to_go = round(current_fuel / fuel_cons, 3)

                time_to_go = datetime.timedelta(seconds=sec_to_go)
                params["Foouter"] = "Расчётное время отключения:"
                params["Timestamp"] = time_to_go
                params["Fields"]["Времени до отключения"] = str(time_to_go)
            else:
                # TODO а оно вообще надо?..
                params["Fields"]["Времени до отключения"] = "Нет: топливо не кончится"
        else:
            params["EDesc"] = "Срочно требуется топливо, произведено отключение всех систем!!!" # noqa E501
            life_support_class = LifeSupport.split("_")[-1]
            life_support_duration = settings.life_supports_sizes[life_support_class]
            params["Кислород кончется через (прим.): "] = life_support_duration
        debug("Параметры SOS-запроса: {}", params)
        if not args or args[0].lower() != "test":
            Discord.Sender(entry.cmdr, "FuelAlarm", params)
        return "Сигнал о помощи послан, ожидайте помощь"

