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

При вызове plugin_prefs в параметр parent добавляются настройки новостей.

"""
import tkinter as tk
from tkinter import Frame
import json
import re
import threading
import uuid

import requests

import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
import settings

from .debug import debug, error
from .lib.spreadsheet import Spreadsheet
from .lib.conf import config

REFRESH_CYCLES = 60  ## how many cycles before we refresh
NEWS_CYCLE = 60 * 1000  # 60 секунд
DEFAULT_NEWS_URL = "https://vk.com/close_encounters_corps"
WRAP_LENGTH = 200


class Downloader(threading.Thread):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def run(self):
        debug("News: UpdateThread")
        # download cannot contain any
        # tkinter changes
        self.widget.download()


class LimitedSpreadsheet(Spreadsheet):
    limit = 5
    def process(self):
        self.data = []
        for i, row in enumerate(self, start=1):
            self.data.append(row)
            if i == self.limit:
                break


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

        self.news_data = None
        self.columnconfigure(1, weight=1)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        self.label = tk.Label(self, text="Новости:")
        self.label.grid(row=0, column=0, sticky=sticky)
        self.label.bind("<Button-1>", self.click_news)

        self.hyperlink = NewsLink(self)
        self.hyperlink.grid(row=0, column=1, sticky="NSEW")

        self.news_count = 5
        self.news_pos = 0
        self.minutes = 0
        self.update_visible()
        self.after(250, self.news_update)

    def news_update(self):
        if self.isvisible:
            if self.minutes == 0:
                Downloader(self).start()
            else:
                self.minutes -= 1

            self.update()
        self.after(NEWS_CYCLE, self.news_update)

    def update(self):
        if self.news_data:
            self.news_pos %= self.news_count
            news = self.news_data[self.news_pos]
            self.hyperlink["url"] = news[1]
            self.hyperlink["text"] = news[2]
            debug("News debug: '{}'", news[2])
            self.news_pos += 1
        elif self.isvisible:
            # keep trying until we
            # have some data
            self.after(1000, self.update)

    def click_news(self, event):
        self.update()

    def download(self):
        """Выкачивает последние несколько новостей и обновляет поля модуля."""
        debug("Fetching News")
        table = LimitedSpreadsheet(settings.news_url)
        self.news_data = table
        self.news_pos = 0
        self.minutes = REFRESH_CYCLES

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        """Добавляет виджеты (поля настроек) к parent"""

        self.hidden.set(config.getint("HideNews"))
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
        """Обновляет параметры модуля новостей."""
        config.set("HideNews", self.hidden.get())
        self.update_visible()
