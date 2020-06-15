# -*- coding: utf-8 -*-
"""
Модуль, отвечающий за отображение новостей.

Как работает:
1. Класс CECNews при инициализации проверяет настройки,
    и если новости там отключены, то плагин убирает
    свои поля и ставит isvisible = True.
2. В конце инициализации ставит коллбэк на `news_update()`.
3. Тот, в свою очередь, каждые 60 секунд проверяет isvisible,
    и если плагин включен и таймер дошёл до нуля,
    то вызывает в фоновом потоке `download()`...
4. ...который выкачивает новости и обновляет таймер.

"""
import tkinter as tk
from tkinter import Frame
import json
import re
import threading
import uuid

import requests

import myNotebook as nb
from config import config
from ttkHyperlinkLabel import HyperlinkLabel
import settings

from .debug import debug, error

REFRESH_CYCLES = 60  ## how many cycles before we refresh
NEWS_CYCLE = 60 * 1000  # 60 секунд
DEFAULT_NEWS_URL = "https://vk.com/close_encounters_corps"
WRAP_LENGTH = 200


class UpdateThread(threading.Thread):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def run(self):
        debug("News: UpdateThread")
        # download cannot contain any
        # tkinter changes
        self.widget.download()


class NewsLink(HyperlinkLabel):
    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Получение новостей...",
            url=DEFAULT_NEWS_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW,
        )
        self.resized = False
        self.bind("<Configure>", self.__configure_event)

    def __reset(self):
        self.resized = False

    def __configure_event(self, event):
        "Handle resizing."

        if not self.resized:
            self.resized = True
            self.configure(wraplength=event.width)
            self.after(500, self.__reset)


class CECNews(Frame):
    def __init__(self, parent, gridrow):
        "Initialise the ``News``."

        sticky = tk.EW + tk.N  # full width, stuck to the top

        super().__init__(parent)

        self.hidden = tk.IntVar(value=config.getint("HideNews"))

        self.news_data = []
        self.columnconfigure(1, weight=1)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        self.label = tk.Label(self, text="Новости:")
        self.label.grid(row=0, column=0, sticky=sticky)
        self.label.bind("<Button-1>", self.click_news)

        self.hyperlink = NewsLink(self)
        self.hyperlink.grid(row=0, column=1, sticky="NSEW")

        self.news_count = 0
        self.news_pos = 1
        self.minutes = 0
        self.update_visible()
        self.after(250, self.news_update)

    def news_update(self):
        if self.isvisible:
            if self.news_count == self.news_pos:
                self.news_pos = 1
            else:
                self.news_pos += 1

            if self.minutes == 0:
                # вызывает в фоне download()
                UpdateThread(self).start()
            else:
                self.minutes -= 1

            self.update()
        # refesh every 60 seconds
        self.after(NEWS_CYCLE, self.news_update)

    def update(self):
        if self.isvisible:
            if self.news_data:
                feed = self.news_data.content.decode("utf-8").split("\r\n")
                lines = feed[self.news_pos]
                news = lines.split("\t")
                self.hyperlink["url"] = news[1]
                self.hyperlink["text"] = news[2]
                debug("News debug: {}", news)
            else:
                # keep trying until we
                # have some data
                # elf.hyperlink['text']
                # = 'Fetching News...'
                self.after(1000, self.update)

    def click_news(self, event):
        if self.news_count == self.news_pos:
            self.news_pos = 1
        else:
            self.news_pos += 1

        self.update()

    def download(self):
        "Update the news."

        if self.isvisible:

            debug("Fetching News")
            resp = requests.get(settings.news_url)
            debug("Response: {}", resp)
            if not resp.ok:
                raise AssertionError(
                    "Response from Google Spreadsheets is not OK"
                )
            self.news_data = resp
            self.news_count = 5
            self.news_pos = 1
            self.minutes = REFRESH_CYCLES

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidden.set(config.getint("HideNews"))
        # self.hidden = tk.IntVar(value=config.getint("HideNews"))
        return nb.Checkbutton(
            parent, text="Скрыть новости СЕС", variable=self.hidden
        ).grid(row=gridrow, column=0, sticky="NSEW")

    def update_visible(self):
        if self.hidden.get() == 1:
            self.grid_remove()
            self.isvisible = False
        else:
            self.grid()
            self.isvisible = True


    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set("HideNews", self.hidden.get())
        self.update_visible()
        if self.isvisible:
            self.news_update()
