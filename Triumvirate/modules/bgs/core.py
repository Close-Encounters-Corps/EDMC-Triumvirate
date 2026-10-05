import requests
import sqlite3
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import Any

from Triumvirate.core.context import PluginContext
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.module import Module
from Triumvirate.lib.thread import Thread
from Triumvirate.modules.legacy import GoogleReporter

from .submodules import BGSSubmodule, CZTracker, ExpDataTracker, MissionTracker, VoucherTracker


@dataclass
class BGSReport:
    submodule_src: str
    url: str
    params: dict
    affected_systems: list[str]


class BgsUiFrame(tk.Frame):
    """
    `tk.Frame`, но скрывает себя, если всего его наследники окажутся скрыты (`<manager>_remove/forget()`).
    Обычный `Frame` в таком случае остаётся пустым местом на экране и не обновляет свой размер.

    Наследники **обязаны** вызывать `BgsUiFrame.show`, когда они помещаются на экран.
    В противном случае, если сам `BgsUiFrame` будет в этот момент скрыт, tkinter не сгенерирует
    ивент `<Map>`, и фрейм не узнает, что ему надо замаппить себя.
    """
    def __init__(self, parent: tk.Misc, row: int, column: int):
        super().__init__(parent)
        self._children_mapped = 0
        self._grid_row = row
        self._grid_column = column
        self.bind_all("<Map>", self.__on_event_map, add="+")
        self.bind_all("<Unmap>", self.__on_event_unmap, add="+")

    def show(self):
        self.grid(row=self._grid_row, column=self._grid_column)

    def __on_event_map(self, event: tk.Event):
        # микрооптимизация - так быстрее, чем через winfo_children
        if getattr(event.widget, "master", None) is self:
            self._children_mapped += 1
            self.grid(row=self._grid_row, column=self._grid_column)

    def __on_event_unmap(self, event: tk.Event):
        # при закрытии EDMC виджет получает unmap-ивент в том числе на самого себя и бросает эксепшен
        if not self.winfo_exists():
            return
        # микрооптимизация - так быстрее, чем через winfo_children
        if getattr(event.widget, "master", None) is not self:
            return
        self._children_mapped -= 1
        if self._children_mapped == 0:
            self.grid_remove()


class FilterUpdater(Thread):
    REFRESH_TIME = 30 * 60  # 30 min
    RETRY_TIME = 30  # sec
    TIMEOUT = 10  # sec

    def __init__(self, callback: Callable[[list[str]], Any]):
        self._callback = callback
        super().__init__(name="Triumvirate.BGSFilterUpdater")

    def do_run(self):
        while True:
            self.fetch()
            self.sleep(self.REFRESH_TIME)

    def fetch(self):
        attempts = 0
        systems = []
        while True:
            attempts += 1
            PluginContext.logger.debug(f"Trying to retrieve the list of tracked systems, attempt {attempts}")
            url = "https://api.github.com/gists/7455b2855e44131cb3cd2def9e30a140"
            try:
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
            except requests.RequestException as e:
                PluginContext.logger.error("Couldnt't get the list of tracked systems from GitHub, exception info:", exc_info=e)
            else:
                systems = str(response.json()["files"]["systems"]["content"]).splitlines()
                if not systems:
                    PluginContext.logger.error("Received list of tracked systems from GitHub was empty.")
                else:
                    PluginContext.logger.info(f"Got the list of tracked systems ({len(systems)} items) from GitHub.")
                    break
            # вторая попытка аналогично из другого источника
            url = "https://gitlab.com/api/v4/snippets/4888705/raw"
            try:
                response = requests.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
            except requests.RequestException as e:
                PluginContext.logger.error(
                    "Couldn't get the list of tracked systems from GitLab either, expection info:", exc_info=e
                )
            else:
                systems = response.text.splitlines()
                if not systems:
                    PluginContext.logger.error("Received list of tracked systems from GitLab was empty.")
                else:
                    PluginContext.logger.info(f"Got the list of tracked systems ({len(systems)} items) from GitLab.")
                    break
            # если не получилось, ждём и пробуем снова
            PluginContext.logger.warning(f"All sources for BGS systems list failed, next attempt in {self.RETRY_TIME} seconds.")
            self.sleep(self.RETRY_TIME)
        # список получен
        self._callback(systems)


class Filter:
    def __init__(self):
        self.__threadlock = Lock()
        self.bgs_reports_queue: Queue[BGSReport] = Queue()
        self._tracked_systems: set[str] = set()
        self.updater = FilterUpdater(self.on_data_update)
        self.updater.start()

    def process_bgs_report(self, report: BGSReport):
        if not self._tracked_systems:
            PluginContext.logger.debug(
                f"[{report.submodule_src}] BGS report check cannot be done: no tracked systems data yet. "
                "Saving the report for a delayed check."
            )
            self.bgs_reports_queue.put(report)
        else:
            with self.__threadlock:
                if not any(s in self._tracked_systems for s in report.affected_systems):
                    PluginContext.logger.debug(
                        f"[{report.submodule_src}] None of the provided affected systems "
                        f"({', '.join(report.affected_systems)}) "
                        "are tracked, ignoring this BGS report."
                    )
                    return
                PluginContext.logger.debug(f"[{report.submodule_src}] Sending a BGS report.")
                GoogleReporter(report.url, report.params).start()

    def on_data_update(self, systems: list[str]):
        with self.__threadlock:
            self._tracked_systems = set(systems)
        if not self.bgs_reports_queue.empty():
            PluginContext.logger.debug("Processing delayed BGS report checks:")
            while not self.bgs_reports_queue.empty():
                self.process_bgs_report(self.bgs_reports_queue.get_nowait())


class BGSCore(Module):
    DB_PATH = PluginContext.paths.userdata_dir / "BGSdata.db"

    @property
    def localized_name(self) -> str:
        return _translate("BGS module")

    def __init__(self, parent: tk.Misc, row: int):
        self.filter = Filter()
        self.database = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        self.ui_frame = BgsUiFrame(parent, row, 0)
        BGSSubmodule.core = self
        self.submodules = [
            CZTracker(ui_row=0),
            ExpDataTracker(),
            MissionTracker(),
            VoucherTracker(),
        ]

    def on_close(self):
        for mod in self.submodules:
            mod.on_close()
        self.database.close()

    def _send_data(self, url: str, params: dict, affected_systems: str | list[str], submodule_src: str):
        """
        Метод для субмодулей для отправки данных через фильтр. См. `BGSSubmodule.send_bgs_report`
        """
        if isinstance(affected_systems, str):
            affected_systems = [affected_systems]
        report = BGSReport(submodule_src, url, params, affected_systems)
        self.filter.process_bgs_report(report)
