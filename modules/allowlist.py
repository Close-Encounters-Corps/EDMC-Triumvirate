import json
import logging
import sys
import threading
import tkinter as tk
from tkinter import Frame
from urllib.parse import quote_plus

import requests

import settings

from .debug import debug, error
from .lib.http import WebClient
from .lib.module import Module
from .lib.thread import Thread


def matchkeys(event, entry):
    for key in event:
        if key not in entry:
            return False
    return True


class AllowlistModule(Frame, Module):
    def __init__(self, parent):
        super().__init__(parent)
        self.list = None
        self.downloader = None
        self.publisher = None
        self.fetch_data()

    def on_journal_entry(self, entry):
        if not self.list:
            return # список ещё скачивается, nothing to do here
        for event in self.list:
            if matchkeys(event, entry.data) and entry.data["event"] == event["event"]:
                debug("Allowlist match {}", entry.data["event"])
                self.publish_data(entry)

    def publish_data(self, entry):
        self.publisher = PublisherThread(entry)
        self.publisher.start()

    def fetch_data(self):
        self.downloader = WebCallbackThread(
            callback=self.fetch_callback, url=settings.whitelist_list_url
        )
        self.downloader.start()

    def fetch_callback(self, data):
        self.list = [json.loads(x["definition"]) for x in data]


class WebCallbackThread(Thread):
    """
    Поток, который в цикле делает GET-запрос на url
    и вызывает коллбэк, передавая ему HTTP-ответ.
    """

    def __init__(self, callback, url, interval=3600):
        super().__init__()
        self.callback = callback
        self.url = url
        self.interval = interval

    def do_run(self):
        while 1:
            client = WebClient()
            response = client.get(self.url)
            results = response.json()
            self.callback(results)
            self.sleep(self.interval)


class PublisherThread(Thread):
    def __init__(self, entry):
        super().__init__()
        self.entry = entry

    def do_run(self):
        params = {
            "cmdrName": self.entry.cmdr,
            "systemName": self.entry.system,
            "station": self.entry.station,
            "event": self.entry.data.get("event"),
            "x": self.entry.coords.x,
            "y": self.entry.coords.y,
            "z": self.entry.coords.z,
            "lat": self.entry.lat,
            "lon": self.entry.lon,
            "is_beta": self.entry.is_beta,
            "raw_event": json.dumps(self.entry.data, ensure_ascii=False),
        }
        for key, val in params.items():
            if not isinstance(val, str):
                params[key] = str(val)
        client = WebClient()
        client.get(settings.whitelist_submit_url, params=params)

