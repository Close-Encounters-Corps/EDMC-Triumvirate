"""
ПРЕДУПРЕЖДЕНИЕ ПОТОМКАМ И БУДУЩЕМУ СЕБЕ
Текущий механизм автообновлений плагина подразумевает, что импорты из других файлов здесь НЕ РАЗРЕШЕНЫ!
Вся логика инициализации плагина, которая раньше была в load.py, должна быть перенесена в plugin_init.py.
"""

import os
import logging
import filecmp
import functools
import requests
import shutil
import tempfile
import threading
import tkinter as tk
import zipfile
from enum import Enum
from pathlib import Path
from queue import Queue
from semantic_version import Version
from time import sleep
from typing import Callable

import l10n
from config import appname, appversion
from config import config as edmc_config


# Дефолтная конфигурация логгера. Требование EDMC
# https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#logging
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()
    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)


# Функция перевода
# https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#localisation
_translate = functools.partial(l10n.translations.tl, context=__file__)


# Механизм обновления плагина

class ReleaseType(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    DEVELOPMENT = "development"


class UpdateCycle(threading.Thread):
    """
    Поток, крутящийся в фоне и время от времени проверяющий наличие обновлений.
    """
    UPDATE_CYCLE = 30*60
    STEP = 3

    def __init__(self, updater_fn: Callable, check_now: bool):
        super().__init__()
        self._stop = False      # флаг остановки потока
        self._updater_fn = updater_fn
        self._check_now = check_now

    def stop(self):
        self._stop = True

    def run(self):
        if self._check_now:
            self._updater_fn()
        
        timer = self.UPDATE_CYCLE
        while not (self._stop or edmc_config.shutting_down()):
            if timer <= 0:
                self._updater_fn()
                timer = self.UPDATE_CYCLE
            timer -= self.STEP
            sleep(self.STEP)
        logger.debug("UpdateCycle stopped.")


class Updater:
    """
    Класс, отвечающий за загрузку, распаковку, проверку и установку обновлений плагина.
    """
    RELEASE_TYPE_KEY = "Triumvirate.Updater.ReleaseType"
    LOCAL_VERSION_KEY = "Triumvirate.Updater.LocalVersion"
    REPOSITORY_URL = "https://api.github.com/repos/Close-Encounters-Corps/EDMC-Triumvirate"

    def __init__(self, plugin_dir: str):
        self.updater_thread: UpdateCycle = None
        self.plugin_dir = Path(plugin_dir)

        self.release_type = edmc_config.get_str(self.RELEASE_TYPE_KEY)
        if self.release_type is None:
            # первый запуск после обновления 1.12.0
            self.release_type = ReleaseType.BETA             # TODO: изменить на stable после выпуска 1.12.0
            edmc_config.set(self.RELEASE_TYPE_KEY, self.release_type)

        saved_version: str | None = edmc_config.get_str(self.LOCAL_VERSION_KEY)
        self.local_version = Version(saved_version or "0.0.0")

    
    def start_update_cycle(self, _check_now: bool = False):
        if self.updater_thread:
            return
        self.updater_thread = UpdateCycle(self.check_for_updates, _check_now)
        self.updater_thread.start()
        logger.debug("UpdateCycle started.")


    def stop_update_cycle(self):
        if not self.updater_thread:
            return
        self.updater_thread.stop()
        self.updater_thread = None
        logger.debug("UpdateCycle was asked to stop.")


    def check_for_updates(self):
        if self.release_type == ReleaseType.DEVELOPMENT:
            logger.info("Release type is Development, stopping the updating process.")
            self.stop_update_cycle()
            self.load_local_version()
            return
        
        # получаем список релизов
        try:
            res = requests.get(self.REPOSITORY_URL + "/releases")
            res.raise_for_status()
        except requests.RequestException as e:
            logger.error("Couldn't get the list of versions from GitHub.", exc_info=e)
            self.load_local_version()
            return
        
        # получаем последний релиз
        releases = res.json()
        try:
            # либо stable, либо beta при соответствующей настройке
            latest = next(
                r for r in releases
                if not r["prerelease"]
                or r["prerelease"] and self.release_type == ReleaseType.BETA
            )
        except StopIteration:
            # никогда не должно произойти, если только кто-то не удалит все релизы с гитхаба
            logger.error("No suitable release found on GitHub. Something's wrong with the repository?")
            self.load_local_version()
            return

        # сверяем с имеющейся версией
        latest_version = Version(latest["tag_name"])
        if latest_version < self.local_version:
            if self.release_type == ReleaseType.STABLE:
                logger.info(
                    "Remote stable version ({}) is lower than the local one ({}). Downgrading.".format(
                        latest_version, self.local_version
                    )
                )
                self.download_update(latest_version)
            
            elif self.release_type == ReleaseType.BETA:
                logger.info("Local version is higher than the latest release. Setting release type to Development.")
                self.release_type = ReleaseType.DEVELOPMENT
                edmc_config.set(self.RELEASE_TYPE_KEY, ReleaseType.DEVELOPMENT)
                self.load_local_version()

            else:
                # Не должно произойти, если только пользователь не сменит тип релиза
                # за то время, пока мы грузим релизы. Но перестрахуемся.
                logger.info("Release type seems to be changed to Development. Skipping the updating process.")
                self.stop_update_cycle()
                self.load_local_version()
            return
            
        elif latest_version == self.local_version:
            logger.info("Local version matches the latest release. No updates required.")
            self.load_local_version()
            return
        
        # latest_version > self.local_version
        logger.info(f"Found an update: {self.local_version} -> {latest_version}.")
        self.download_update(latest_version)


    def download_update(self, tag: Version):
        url = self.REPOSITORY_URL + f"/zipball/{tag}"
        
        tempdir = Path(tempfile.gettempdir()) / "EDMC-Triumvirate"
        if tempdir.exists():
            shutil.rmtree(tempdir)
        tempdir.mkdir()

        version_zip = tempdir / f"{tag}.zip"

        # загружаем
        logger.info("Downloading the new version archive...")
        try:
            # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(version_zip, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
        except requests.RequestException as e:
            logger.error("Couldn't download the version archive from GitHub.", exc_info=e)
            self.load_local_version()
            return
        
        # распаковываем
        logger.info("Extracting the new version archive to the temporary directory...")
        with zipfile.ZipFile(version_zip, 'r') as zipf:
            zipf.extractall(tempdir)
        version_zip.unlink()

        # сверяем текущий load.py с новым - это нам понадобится в будущем
        new_ver_path = next(tempdir.iterdir())      # гитхаб оборачивает файлы в отдельную директорию
        loadpy_was_edited = not filecmp.cmp(Path(new_ver_path, "load.py"), Path(self.plugin_dir, "load.py"), False)
        
        # копируем userdata, чтобы человеки не ругались, что у них миссии между перезапусками трутся
        logger.info("Copying userdata...")
        shutil.copytree(Path(self.plugin_dir, "userdata"), Path(new_ver_path, "userdata"))

        # сносим старую версию и копируем на её место новую, удаляем временные файлы
        logger.info("Replacing plugin files...")
        shutil.rmtree(self.plugin_dir)
        shutil.copytree(new_ver_path, self.plugin_dir)
        shutil.rmtree(tempdir)

        # обновляем запись о локальной версии
        edmc_config.set(self.LOCAL_VERSION_KEY, tag)
        self.local_version = tag
        logger.info(f"Done. Local version set to {tag}.")

        # определяем, что нам делать дальше: грузиться или просить перезапустить EDMC
        if not loadpy_was_edited:
            self.load_local_version()
        else:
            logger.info("load.py was modified. EDMC restart is required.")
            self.updater_thread.stop()
            # TODO: блокировка, UI

    
    def load_local_version(self):
        logger.info("Loading the local version...")
        if not Path(self.plugin_dir, "plugin_init.py").exists():
            logger.error("`plugin_init` module not found. Aborting.")
            return
        
        import plugin_init
        global PLUGIN_VERSION
        PLUGIN_VERSION = plugin_init.get_version()
        if self.local_version != PLUGIN_VERSION:
            logger.warning("Saved local version doesn't match the loaded one. This could be due to a manual update.")
            edmc_config.set(self.LOCAL_VERSION_KEY, PLUGIN_VERSION)
            self.local_version = PLUGIN_VERSION
            logger.warning(f"Local version set to {PLUGIN_VERSION}.")
        
        global PLUGIN_STOP_HOOK, PLUGIN_PREFS_HOOK, PREFS_CHANGED_HOOK
        PLUGIN_STOP_HOOK, PLUGIN_PREFS_HOOK, PREFS_CHANGED_HOOK = plugin_init.get_hooks()

        global EDMC_VERSION, PLUGIN_DIR, EVENT_QUEUE
        plugin_init.configure(
            edmc_version=EDMC_VERSION,
            plugin_dir=PLUGIN_DIR,
            event_queue=EVENT_QUEUE
        )

        global PLUGIN_FRAME
        plugin_ui = plugin_init.plugin_app(PLUGIN_FRAME)
        plugin_ui.pack(fill="both")
        
        logger.info("Local version configured, running.")



# Базовые параметры и объекты, независимые от версии
# После загрузки версии переносятся в её Context
EDMC_VERSION: Version = appversion() if callable(appversion) else Version(appversion)
PLUGIN_DIR: str = None
PLUGIN_VERSION: Version = None
PLUGIN_STOP_HOOK: Callable = None
PLUGIN_PREFS_HOOK: Callable = None
PREFS_CHANGED_HOOK: Callable = None

EVENT_QUEUE = Queue()
PLUGIN_FRAME: tk.Frame = None
UPDATER: Updater = None


# Функции управления поведением плагина, вызываемые EDMC

def plugin_start(plugin_dir):
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 2.
    """
    raise EnvironmentError(_translate("At least EDMC 5.11.0 is required to use this plugin."))


def plugin_start3(plugin_dir: str):
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 3.
    """
    if EDMC_VERSION < Version("5.11.0"):
        raise EnvironmentError(_translate("At least EDMC 5.11.0 is required to use this plugin."))
    
    global PLUGIN_DIR, UPDATER
    PLUGIN_DIR = plugin_dir
    UPDATER = Updater(plugin_dir)
    UPDATER.start_update_cycle(_check_now=True)


def plugin_stop():
    """
    EDMC вызывает эту функцию при закрытии.
    """
    global PLUGIN_VERSION, UPDATER
    UPDATER.stop_update_cycle()
    if PLUGIN_STOP_HOOK is not None:
        PLUGIN_STOP_HOOK()


def plugin_app(parent: tk.Misc) -> tk.Frame:
    """
    EDMC вызывает эту функцию при запуске плагина для получения элемента UI плагина,
    отображаемого в окне программы.
    """
    global PLUGIN_FRAME
    return PLUGIN_FRAME


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool) -> tk.Frame:
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    if PLUGIN_PREFS_HOOK is not None:
        return PLUGIN_PREFS_HOOK()
    #TODO: заглушка


def prefs_changed(cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию при сохранении настроек пользователем.
    """
    if PREFS_CHANGED_HOOK is not None:
        PREFS_CHANGED_HOOK()
        return
    #TODO: заглушка
    

# Эти функции относятся к внутреигровым событиям.
# Здесь мы будем лишь сохранять все входящие данные в общую очередь.
# После загрузки версии её обработчик ивентов подключится к этой очереди и начнёт её обрабатывать.

def journal_entry(
    cmdr:       str | None,
    is_beta:    bool,
    system:     str | None,
    station:    str | None,
    entry:      dict,
    state:      dict
):
    """
    EDMC вызывает эту функцию при появлении новой записи в логах игры.
    """
    EVENT_QUEUE.put({"type": "journal_entry", "data": (cmdr, is_beta, system, station, entry, state)})


def dashboard_entry(cmdr: str | None, is_beta: bool, entry: dict):
    """
    EDMC вызывает эту функцию при обновлении игрой status.json.
    """
    EVENT_QUEUE.put({"type": "dashboard_entry", "data": (cmdr, is_beta, entry)})


def cmdr_data(data: dict, is_beta: bool):
    """
    EDMC вызывает эту функцию при получении данных о командире с серверов Frontier.
    """
    EVENT_QUEUE.put({"type": "cmdr_data", "data": (data, is_beta)})