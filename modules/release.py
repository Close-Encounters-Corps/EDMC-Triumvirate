"""
Модуль, который отвечает за проверку обновлений плагина и их автоматическую установку.

Как примерно работает:
1. при запуске класса поднимается фоновый поток, который периодически
    проверяет GitHub на новые релизы.
2. Появился релиз с новой версией -- сообщеаем об этом в окне EDMC.
3. Если включено автообновление -- скачиваем и распаковываем архив с ним.
"""

from enum import Enum
import io
import json
import os
import random
import re
import shutil
import sys
import tkinter as tk
import uuid
import zipfile
from io import BytesIO, StringIO
from tkinter import Frame

import requests

import myNotebook as nb
import plug
import settings
from ttkHyperlinkLabel import HyperlinkLabel

from .debug import debug
from .lib.conf import config
from .lib.context import global_context
from .lib.http import WebClient, HttpError
from .lib.module import Module
from .lib.thread import Thread, BasicThread
from .lib.version import Version
from .player import Player

RELEASE_CYCLE = 60 * 1000 * 60  # 1 Hour
WRAP_LENGTH = 200


class Environment(Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    LIVE = "LIVE"


class ReleaseLink(HyperlinkLabel):
    def __init__(self, parent):

        super().__init__(
            parent,
            text="Поиск",
            url=settings.release_gh_url,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW,
        )
        self.bind("<Configure>", self.__configure_event)

    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)


class ReleaseThread(Thread):
    def __init__(self, release):
        super().__init__()
        self.release = release

    def do_run(self):
        while 1:
            self.release.check_updates()
            if self.release.installed:
                return
            self.sleep(RELEASE_CYCLE)


class SimpleThread(Thread):
    def __init__(self, target):
        super().__init__()
        self.target = target

    def do_run(self):
        self.target()


class Release(Frame, Module):
    def __init__(self, plugin_dir, parent, version, gridrow):

        sticky = tk.EW + tk.N  # full width, stuck to the top

        super().__init__(parent)

        self.plugin_dir = plugin_dir

        self.installed = False

        self.no_auto = tk.IntVar(value=config.get_int("DisableAutoUpdate"))
        remove_backup = None
        try:
            remove_backup = config.get_int("RemoveBackup")
        except ValueError:
            try:
                remove_backup = int(config.get_str("RemoveBackup"))
            except:
                remove_backup = 0
        self.rmbackup = tk.IntVar(value=remove_backup)
        self.no_auto_val = self.no_auto.get()
        self.rmbackup_val = self.rmbackup.get()

        self.columnconfigure(1, weight=1)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        self.label = tk.Label(self, text="Версия:")
        self.label.grid(row=0, column=0, sticky=sticky)

        self.hyperlink = ReleaseLink(self)
        self.hyperlink.grid(row=0, column=1, sticky="NSEW")

        self.button = tk.Button(
            self, text="Нажмите чтобы обновить", command=self.download
        )
        self.button.grid(row=1, column=0, columnspan=2, sticky="NSEW")
        self.button.grid_remove()
        
        self.version = Version(version)
        self.env = None
        self.release_thread = None
        self.latest = {}
        if config.getint("DisableAutoUpdate") == 0:
            self.launch()
        BasicThread(target=self.update_release_env).start()

    def launch(self):
        self.release_thread = ReleaseThread(self)
        self.release_thread.start()
        debug(f"RemoveBackup: {self.rmbackup_val}")
        if self.no_auto_val == 0:
            delete_dir = config.get_str("BackupName")
            debug(f"BackupName {delete_dir}")
            if not delete_dir or not os.path.exists(delete_dir):
                global_context.log.info("no backups to remove")
                return
            shutil.rmtree(delete_dir)
            # lets not keep trying
            config.set("RemoveBackup", 0)

    def draw_settings(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.no_auto = tk.IntVar(value=config.get_int("DisableAutoUpdate"))
        remove_backup = None
        try:
            remove_backup = config.get_int("RemoveBackup")
        except ValueError:
            try:
                remove_backup = int(config.get_str("RemoveBackup"))
            except:
                remove_backup = 0
        self.rmbackup = tk.IntVar(value=remove_backup)

        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")
        global_context.log.info(f"{self.no_auto_val=}")
        nb.Checkbutton(
            frame, text="Отключить автообновление", variable=self.no_auto
        ).grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(
            frame, text="Хранить бекапы версий", variable=self.rmbackup
        ).grid(row=0, column=1, sticky="NW")

        return frame

    def on_settings_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set("DisableAutoUpdate", self.no_auto.get())
        config.set("RemoveBackup", self.rmbackup.get())
        # остановка и запуск потока обновления (при необходимости)
        BasicThread(target=self.restart_thread).start()

    def restart_thread(self):
        self.release_thread.STOP = True
        self.release_thread.join()
        if config.getint("DisableAutoUpdate") == 0:
            self.grid()
            self.release_thread = ReleaseThread(self)
            self.release_thread.start()
        else:
            self.grid_remove()

    def update_release_env(self) -> Environment:
        try:
            resp = WebClient().get(settings.release_gh_ver_info.format(self.version))
        except HttpError as e:
            resp = e.response
            if resp.status_code == 404:
                debug("Release not in GitHub")
                self.env = Environment.DEVELOPMENT
                return
            else:
                raise
        data = resp.json()
        if data.get("prerelease", False):
            self.env = Environment.STAGING
        else:
            self.env = Environment.LIVE

    def check_updates(self):
        if self.installed:
            return
        url = settings.release_gh_latest
        client = WebClient()
        data = client.get(url).json()
        latest_tag = data["tag_name"]
        latest_version = Version(latest_tag)
        self.hyperlink["url"] = data["html_url"]
        self.hyperlink["text"] = f"EDMC-Triumvirate: {latest_tag}"
        if latest_version == self.version:
            self.grid_remove()
            return
        elif latest_version < self.version:
            self.hyperlink["text"] = f"Тестовая версия {self.version.raw_value} beta-2"
            debug(f"PLUGIN VERSION: {self.version.raw_value} beta-2")
            return
        if self.no_auto_val == 1:
            debug("Automatic update disabled.")
            # self.notify()
            return
        self.download(latest_tag)

    def download(self, tag):
        debug("Downloading version {}", tag)
        url = settings.release_zip_template.format(tag)
        new_plugin_dir = f"EDMC-Triumvirate-{tag}"
        client = WebClient()
        response = client.get(url, stream=True)
        try:
            zf = zipfile.ZipFile(response.raw)
            zf.extractall(os.path.dirname(self.plugin_dir))
        finally:
            response.close()
        renamed = f"{self.plugin_dir}.disabled"
        os.rename(self.plugin_dir, renamed)
        debug("Upgrade completed.")
        self.plugin_dir = new_plugin_dir
        self.installed = True
        config.set("BackupName", renamed)


    @classmethod
    def get_auto(cls):
        return tk.IntVar(value=config.get_int("DisableAutoUpdate")).get()


    def notify(self):
        sound = random.choice(["sounds/nag1.wav", "sounds/nag2.wav"])
        Player(self.plugin_dir, [sound]).start()
