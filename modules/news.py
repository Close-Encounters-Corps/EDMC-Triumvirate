# -*- coding: utf-8 -*-
"""
Module responsible for showing news.

How it works:
1. Class CECNews on initialization checks settings, and
    if news are disabled, then module removes its fields and
    sets `isvisible` = False.
2. In the end of initialization makes callback on `fetch_and_update()`.
3. That method, in turn, every 60 seconds checks `isvisible`,
    and if plugin is enabled and timer reached zero,
    then calls in background thread `download()`...
4. ...that downloads news and updates the timer.
5. Also, from time to time, in `fetch_and_update()` triggers `update()`,
    that updates news fields in UI.
"""
from datetime import datetime
import tkinter as tk
from tkinter import Frame
import traceback

import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
import settings

from .debug import debug, Debug, error
from .lib.conf import config
from .lib.thread import Thread, BasicThread
from .lib.module import Module
from .lib.context import global_context

# number of cycles (NEWS_CYCLE) before getting news from platform
REFRESH_CYCLES = 60
# 60 seconds
NEWS_CYCLE = 60 * 1000


class DownloadThread(Thread):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def do_run(self):
        debug("News: UpdateThread")
        while 1:
            # download cannot contain any
            # tkinter changes
            self.widget.download()
            self.sleep(REFRESH_CYCLES * NEWS_CYCLE)

class NewsLink(HyperlinkLabel):
    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Получение новостей...",
            url=settings.cec_endpoint,
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


class CECNews(Frame, Module):
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
        # TODO does not work...
        self.label.bind("<Button-1>", self.click_news)

        self.hyperlink = NewsLink(self)
        self.hyperlink.grid(row=0, column=1, sticky="NSEW")

        self.download_thread = None

        self.news_pos = 0
        self.minutes = 0
        self.update_visible()
        self.after(250, self.fetch_and_update)

    def draw_settings(self, parent_widget, cmdr, is_beta, position):
        """Attaches widgets (settings fields) to parent"""

        self.hidden.set(config.getint("HideNews"))
        return nb.Checkbutton(
            parent_widget, text="Скрыть новости СЕС", variable=self.hidden
        ).grid(row=position, column=0, sticky="NSEW")

    def on_settings_changed(self, cmdr, is_beta):
        config.set("HideNews", self.hidden.get())
        self.update_visible()
        BasicThread(target=self.restart_thread).start()

    @property
    def enabled(self):
        return self.isvisible

    def restart_thread(self):
        self.download_thread.STOP = True
        self.download_thread.join()
        if self.enabled:
            self.download_thread = DownloadThread(self)
            self.download_thread.start()

    def fetch_and_update(self):
        if self.isvisible:
            if self.download_thread is None:
                self.download_thread = DownloadThread(self)
                self.download_thread.start()

            self.update()
        self.after(NEWS_CYCLE, self.fetch_and_update)

    def update(self):
        if self.news_data:
            self.news_pos %= len(self.news_data)
            article = self.news_data[self.news_pos]
            self.hyperlink["url"] = article["link"]
            dt = datetime.fromisoformat(article["whenPublished"]).strftime("%d.%m.%Y")
            self.hyperlink["text"] = f"{article['title']} {dt}"
            debug("News debug: {!r}", dt)
            self.news_pos += 1
        elif self.isvisible:
            # keep trying until we
            # have some data
            self.after(1000, self.update)

    def click_news(self, event):
        self.update()

    def download(self):
        """Download last news and update module fields."""
        debug("Fetching News")
        try:
            data = global_context.cec_api.fetch("/v1/news")
            self.news_data = data
            self.news_pos = 0
            self.minutes = REFRESH_CYCLES
        except:
            self.hyperlink["text"] = "Ошибка при запросе новостей"
            error("Error submitting data:")
            if Debug.debugswitch == 1:
                traceback.print_exc()



    def update_visible(self):
        if self.hidden.get() == 1:
            self.grid_remove()
            self.isvisible = False
        else:
            self.grid()
            self.isvisible = True

