import logging
import tkinter as tk
from queue import Queue
from semantic_version import Version

import settings
from modules.lib import thread
from context import PluginContext
from modules.bgs import BGS
from modules.canonn_api import CanonnRealtimeAPI
from modules.debug import Debug
from modules.fc_tracker import FC_Tracker
from modules.notifier import Notifier
from modules.patrol import PatrolModule
from modules.systems import SystemsModule
from modules.squadron import Squadron_Tracker
from modules.visualizer import Visualizer

import myNotebook as nb


def get_version() -> Version:
    """Возвращает номер установленной версии плагина."""
    return Version(settings.version)


def init_context(edmc_version: Version, plugin_dir: str, event_queue: Queue, logger: logging.Logger):
    """Инициализирует плагин с параметрами, предоставленными EDMC."""
    PluginContext.logger = logger
    Debug.setup(logger)
    PluginContext.edmc_version = edmc_version
    PluginContext.plugin_dir = plugin_dir
    PluginContext._event_queue = event_queue


def plugin_app(parent: tk.Misc) -> tk.Frame:
    """
    Updater вызывает эту функцию для получения UI плагина,
    который затем будет размещён в главном окне EDMC.
    """
    frame = tk.Frame(parent)
    PluginContext.notifier = Notifier(frame, 3)    # его надо инициализировать первым, но маппить в самый низ
    PluginContext.visualizer = Visualizer(frame, 0)
    PluginContext.patrol_module = PatrolModule(frame, 1)
    PluginContext.fc_tracker = FC_Tracker(frame, 2)

    # эти модули не имеют UI, но стартуем их здесь же
    PluginContext.bgs_module = BGS()
    PluginContext.canonn_api = CanonnRealtimeAPI()
    PluginContext.systems_module = SystemsModule()
    PluginContext.sq_tracker = Squadron_Tracker()

    #TODO: on_start вообще не нужен с новой системой обновлений, отредактировать модули
    for mod in PluginContext.active_modules:
        mod.on_start(PluginContext.plugin_dir)

    # в последнюю очередь запускаем обработчик событий
    #TODO

    return frame


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool) -> nb.Frame:
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    frame = nb.Frame(parent)
    Debug.plugin_prefs(frame)       # всегда занимает 0-ой ряд
    for row, mod in enumerate(PluginContext.active_modules):
        mod.draw_settings(frame, cmdr, is_beta, row+1)
    nb.Label(frame, text=settings.support_message).grid(row=row+2, column=0, sticky="NW")
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