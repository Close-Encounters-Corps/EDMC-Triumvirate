import tkinter as tk
from tkinter import ttk

from context import PluginContext
from journal_processor import JournalProcessor
from modules.bgs import BGS
from modules.canonn_api import CanonnRealtimeAPI
from modules.colonisation import DeliveryTracker
from modules.debug import Debug
from modules.fc_tracker import FC_Tracker
from modules.notifier import Notifier
from modules.patrol import PatrolModule
from modules.systems import SystemsModule
from modules.squadron import Squadron_Tracker
from modules.exploring.canonn_codex_poi import CanonnCodexPOI
from modules.exploring.visualizer import Visualizer
from modules.lib import thread
from modules.lib.module import Module

import myNotebook as nb                         # type: ignore
from config import config as edmc_config        # type: ignore


def init_version():
    Debug.setup(PluginContext.logger)
    # очистка устаревших ключей конфигурации
    edmc_config.delete("Triumvirate.Canonn:HideCodex", suppress=True)
    edmc_config.delete("Triumvirate.Canonn", suppress=True)
    # TODO: раскомментить после релиза 1.12.0
    # edmc_config.delete("Triumvirate.CanonnDebug", suppress=True)
    # edmc_config.delete("Triumvirate.DisableAutoUpdate", suppress=True)
    # edmc_config.delete("Triumvirate.RemoveBackup", suppress=True)


def plugin_app(parent: tk.Misc) -> tk.Frame:
    """
    Updater вызывает эту функцию для получения UI плагина,
    который затем будет размещён в главном окне EDMC.
    """
    frame = tk.Frame(parent)
    PluginContext.notifier = Notifier(frame, 3)    # его надо инициализировать первым, но маппить в самый низ
    PluginContext.exp_visualizer = Visualizer(frame, 0)
    PluginContext.patrol_module = PatrolModule(frame, 1)
    PluginContext.fc_tracker = FC_Tracker(frame, 2)

    # эти модули не имеют UI, но стартуем их здесь же
    PluginContext.systems_module = SystemsModule()
    PluginContext.bgs_module = BGS()
    PluginContext.canonn_api = CanonnRealtimeAPI()
    PluginContext.colonisation_tracker = DeliveryTracker()
    PluginContext.sq_tracker = Squadron_Tracker()
    PluginContext.canonn_codex_poi = CanonnCodexPOI()

    # TODO: on_start вообще не нужен с новой системой обновлений, отредактировать модули
    for mod in PluginContext.active_modules:
        mod.on_start(PluginContext.plugin_dir)

    # в последнюю очередь запускаем обработчик событий
    PluginContext.journal_processor = JournalProcessor()
    PluginContext.journal_processor.start()

    return frame


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool) -> tk.Frame:
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    # TODO: перейти на pack

    def rowgen():
        row = 1     # Debug.plugin_prefs всегда занимает нулевой ряд
        while True:
            yield row
            row += 1
    rg = rowgen()

    frame = tk.Frame(parent, bg="white")
    frame.grid_columnconfigure(0, weight=1)
    Debug.plugin_prefs(frame)
    ttk.Separator(frame, orient="horizontal").grid(row=next(rg), column=0, pady=5, sticky="EW")

    for mod in PluginContext.active_modules:
        # некоторые модули не имеют настроек, а лишние линии нам не нужны
        if mod.__class__.draw_settings != Module.draw_settings:
            mod.draw_settings(frame, cmdr, is_beta, next(rg))
            ttk.Separator(frame, orient="horizontal").grid(row=next(rg), column=0, pady=5, sticky="EW")

    nb.Label(
        frame, text=PluginContext._tr_template("<SETTINGS_SUPPORT_MESSAGE>", filepath=__file__)
    ).grid(row=next(rg), column=0, sticky="NW")
    return frame


def prefs_changed(cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию при сохранении настроек пользователем.
    """
    Debug.prefs_changed()
    for mod in PluginContext.active_modules:
        mod.on_settings_changed(cmdr, is_beta)


def plugin_stop():
    """
    EDMC вызывает эту функцию при закрытии.
    """
    PluginContext.logger.debug("Stopping the plugin.")
    for mod in PluginContext.active_modules:
        mod.on_close()
    thread.Thread.stop_all()
