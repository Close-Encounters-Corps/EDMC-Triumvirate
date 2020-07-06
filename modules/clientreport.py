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
from .debug import debug, error
from .release import Release


class clientReport(modules.emitter.Emitter):
    done = False

    def __init__(self, cmdr, is_beta, client):

        self.modelreport = "clientreports"
        modules.emitter.Emitter.__init__(
            self, cmdr, is_beta, None, None, None, None, None, None, None, None, client
        )

    def setPayload(self):
        payload = {}
        payload["cmdrName"] = self.cmdr
        payload["isBeta"] = self.is_beta
        payload["clientVersion"] = self.client
        if global_context.by_class(Release).no_auto.get() == 0:
            payload["AutoUpdateDisabled"] = False
        else:
            payload["AutoUpdateDisabled"] = True

        return payload

    def run(self):
        if not clientReport.done:
            clientReport.done = True
            debug("sending client report")
            # configure the payload
            payload = self.setPayload()
            url = self.getUrl()
            self.send(payload, url)
            debug("Google Client Report")
            modules.emitter.post(
                "https://us-central1-canonn-api-236217.cloudfunctions.net/submitCient",
                {
                    "cmdr": payload.get("cmdrName"),
                    "beta": payload.get("isBeta"),
                    "client": payload.get("clientVersion"),
                    "autoupdate": not payload.get("AutoUpdateDisabled"),
                },
            )


def submit(cmdr, is_beta, client, entry):
    if entry.get("event") in ("Location", "StartUp"):
        clientReport(cmdr, is_beta, client).start()

    if entry.get("event") in ("Fileheader"):
        modules.emitter.post(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/postGameVersion",
            entry,
        )
