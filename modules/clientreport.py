# -*- coding: utf-8 -*-
import threading
import requests
import sys
import json
import modules.emitter

try:  # py3
    from urllib.parse import quote_plus
except:  # py2
    from urllib import quote_plus
from .lib.context import global_context
from .lib.module import Module
from .debug import debug, error
from .release import Release

class ClientReportModule(Module):
    def on_journal_entry(self, entry):
        if entry.data.get("event") in ("Location", "StartUp"):
            autoupdate = global_context.by_class(Release).no_auto.get() == 0
            global_context.canonn_rt_api.submit_client(dict(
                cmdr=entry.cmdr,
                beta=entry.is_beta,
                client=entry.client,
                autoupdate=autoupdate
            ))

        if entry.data.get("event") in ("Fileheader"):
            global_context.canonn_rt_api.sumbit_game_version(entry.data)

