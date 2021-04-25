# -*- coding: utf-8 -*-
from . import Discord

import datetime
from .debug import debug
from .lib.module import Module
from .lib.context import global_context

import settings


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
        payload = entry.as_dict()
        fuel = global_context.fuel
        payload["fuel"] = {
            "main": fuel["FuelMain"],
            "reservoir": float(fuel["FuelReservoir"]),
            "consumption": global_context.fuel_cons
        }
        payload["flags"] = global_context.latest_dashboard_entry["Flags"]
        global_context.cec_api.submit("/v1/sos", payload)
        return "Сигнал о помощи послан, ожидайте помощь"

