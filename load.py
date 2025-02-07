"""
ПРЕДУПРЕЖДЕНИЕ ПОТОМКАМ И БУДУЩЕМУ СЕБЕ
Текущий механизм автообновлений плагина подразумевает, что импорты из других файлов плагина здесь НЕ РАЗРЕШЕНЫ!
Вся логика инициализации плагина, которая раньше была в load.py, должна быть перенесена в plugin_init.py.
"""

import os
import logging
import functools
import requests
import shutil
import tempfile
import threading
import tkinter as tk
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Queue
from semantic_version import Version
from time import sleep
from tkinter import ttk
from typing import Callable

import l10n
import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
from config import appname, appversion
from config import config as edmc_config
from theme import theme


# Дефолтная конфигурация логгера. Требование EDMC
# https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#logging
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()
    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(r'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)


# Функция перевода
# https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#localisation
_translate = functools.partial(l10n.translations.tl, context=__file__)


@dataclass
class BasicContext:
    """
    Хранилище объектов и параметров, используемых до загрузки версии.
    По сути нужно лишь для того, чтобы не засорять код global-ами.
    """
    edmc_version: Version           = appversion() if callable(appversion) else Version(appversion)
    plugin_loaded: bool             = False
    plugin_version: Version         = None
    plugin_dir: str                 = None

    updater: "Updater"              = None
    event_queue: Queue[dict]        = Queue()

    plugin_frame: tk.Frame          = None
    plugin_ui: tk.Misc              = None
    status_label: "StatusLabel"     = None
    version_frame: "VersionFrame"   = None
    settings_frame: "ReleaseTypeSettingFrame" = None

    plugin_stop_hook: Callable      = None
    plugin_prefs_hook: Callable     = None
    prefs_changed_hook: Callable    = None

context = BasicContext()        # noqa: E305


# Механизм обновления плагина

class ReleaseType(str, Enum):
    STABLE = "Stable"
    BETA = "Beta"
    _DEVELOPMENT = "Development"        # не должен быть публичным, тк, по сути, отключает автообновление


class UpdateCycle(threading.Thread):
    """
    Поток, крутящийся в фоне и время от времени проверяющий наличие обновлений.
    """
    UPDATE_CYCLE = 30 * 60
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
        while not (self._stop or edmc_config.shutting_down):
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
    REPOSITORY_PATH = "Close-Encounters-Corps/EDMC-Triumvirate"

    def __init__(self):
        self.updater_thread: UpdateCycle = None

        self.release_type = edmc_config.get_str(self.RELEASE_TYPE_KEY)
        if self.release_type is None:
            self.release_type = ReleaseType.BETA             # TODO: изменить на stable после выпуска 1.12.0
            edmc_config.set(self.RELEASE_TYPE_KEY, self.release_type)

        saved_version: str | None = edmc_config.get_str(self.LOCAL_VERSION_KEY)
        self.local_version = Version(saved_version or "0.0.0")


    def start_update_cycle(self, _check_now: bool = False):
        if self.updater_thread:
            return
        self.updater_thread = UpdateCycle(self.__check_for_updates, _check_now)
        self.updater_thread.start()
        logger.debug("UpdateCycle started.")


    def stop_update_cycle(self):
        if not self.updater_thread:
            return
        self.updater_thread.stop()
        self.updater_thread = None
        logger.debug("UpdateCycle was asked to stop.")


    def restart_update_cycle(self):
        self.stop_update_cycle()
        self.start_update_cycle(_check_now=True)


    def __check_for_updates(self):
        logger.info("Checking for updates started.")
        if self.release_type == ReleaseType._DEVELOPMENT:
            logger.info("Release type is Development, stopping the updating process.")
            self.stop_update_cycle()
            self.__use_local_version()
            return

        # получаем список релизов
        try:
            res = requests.get("https://api.github.com/repos/" + self.REPOSITORY_PATH + "/releases")
            res.raise_for_status()
        except requests.RequestException as e:
            logger.error("Couldn't get the list of versions from GitHub.", exc_info=e)
            context.status_label.set_text(_translate("Error: couldn't check for updates."))
            self.__use_local_version()
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
            context.status_label.set_text(_translate("Error: couldn't check for updates."))
            self.__use_local_version()
            return

        # сверяем с имеющейся версией
        latest_version = Version(latest["tag_name"])
        if latest_version == self.local_version:
            logger.info("Local version matches the latest release. No updates required.")
            context.status_label.clear()
            self.__use_local_version()
        else:
            if latest_version < self.local_version:
                logger.info((f"Remote version ({latest_version}) is lower than the local one ({self.local_version}). ",
                             "A downgrade is required."))
            else:
                logger.info(f"Found an update: {self.local_version} -> {latest_version}.")

            if not context.plugin_loaded:
                self.__download_update(latest_version)
            else:
                logger.info("Notifying user.")
                context.status_label.set_text(
                    _translate("An update is available ({v}). Please restart EDMC.").format(v=str(latest_version))
                )


    def __download_update(self, tag: Version):
        context.status_label.set_text(_translate("Downloading an update..."))
        url = f"https://api.github.com/repos/{self.REPOSITORY_PATH}/zipball/{tag}"
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
            context.status_label.set_text(_translate("Error: couldn't download an update."))
            self.__use_local_version()
            return

        # распаковываем
        context.status_label.set_text(_translate("Installing an update..."))
        logger.info("Extracting the new version archive to the temporary directory...")
        with zipfile.ZipFile(version_zip, 'r') as zipf:
            zipf.extractall(tempdir)
        version_zip.unlink()

        # сверяем текущий load.py с новым - это нам понадобится в будущем
        new_ver_path = next(tempdir.iterdir())      # гитхаб оборачивает файлы в отдельную директорию
        loadpy_was_edited = self.__files_differ(Path(new_ver_path, "load.py"), Path(context.plugin_dir, "load.py"))

        # копируем userdata, чтобы человеки не ругались, что у них миссии между перезапусками трутся
        logger.info("Copying `userdata`...")
        try:
            shutil.copytree(Path(context.plugin_dir, "userdata"), Path(new_ver_path, "userdata"))
        except FileNotFoundError:
            logger.warning("Directory `userdata` not found, skipping.")

        # сносим старую версию и копируем на её место новую, удаляем временные файлы
        logger.info("Replacing plugin files...")
        shutil.rmtree(context.plugin_dir)
        shutil.copytree(new_ver_path, context.plugin_dir)
        shutil.rmtree(tempdir)

        # обновляем запись о локальной версии
        edmc_config.set(self.LOCAL_VERSION_KEY, str(tag))
        self.local_version = tag
        logger.info(f"Done. Local version set to {tag}.")

        # определяем, что нам делать дальше: грузиться или просить перезапустить EDMC
        if not loadpy_was_edited:
            context.status_label.clear()
            self.__use_local_version()
        else:
            logger.info("load.py was modified. EDMC restart is required.")
            self.updater_thread.stop()
            context.status_label.set_text(_translate("The update is installed. Please restart EMDC."))


    def __use_local_version(self):
        if context.plugin_loaded:
            return

        def __inner(self):
            logger.info("Loading local version the in main thread...")
            if not Path(context.plugin_dir, "plugin_init.py").exists():
                logger.error("`plugin_init` module not found. Aborting.")
                return

            import plugin_init
            context.plugin_version = plugin_init.get_version()
            if self.local_version != context.plugin_version:
                logger.warning("Saved local version doesn't match the loaded one. This could be due to a manual update.")
                edmc_config.set(self.LOCAL_VERSION_KEY, str(context.plugin_version))
                self.local_version = context.plugin_version
                logger.warning(f"Local version set to {context.plugin_version}.")

            context.plugin_stop_hook = plugin_init.plugin_stop
            context.plugin_prefs_hook = plugin_init.plugin_prefs
            context.prefs_changed_hook = plugin_init.prefs_changed

            plugin_init.init_context(
                edmc_version=context.edmc_version,
                plugin_dir=context.plugin_dir,
                event_queue=context.event_queue,
                logger=logger
            )

            context.status_label.clear()
            context.version_frame = VersionFrame(context.plugin_frame, context.plugin_version)
            context.plugin_ui = plugin_init.plugin_app(context.plugin_frame)
            theme.update(context.version_frame)
            theme.update(context.plugin_ui)
            context.version_frame.grid(row=0, column=0, sticky="NWS")
            context.plugin_ui.grid(row=2, column=0, sticky="NWSE")

            context.plugin_loaded = True
            logger.info("Local version configured, running.")


        # фикс для development-версий: удостоверимся, что userdata всегда существует
        Path(context.plugin_dir, "userdata").mkdir(exist_ok=True)

        # Если у нас стоит актуальная версия, мы можем дойти до этого участка кода быстрее,
        # чем EDMC успеет создать своё окно, и мы словим runtime error.
        # winfo_ismapped до создания окна тоже бросает эксепшн, поэтому придётся делать по-уродски.
        while True:
            try:
                tk._default_root.after(0, __inner, self)
                logger.info("IGNORE THE SURROUNDING LOGGING ALERTS. They appear because of tkinter and EMDC logging implementations.")
            except RuntimeError:
                sleep(1)
            else:
                break


    def __files_differ(self, file1: Path, file2: Path):
        """
        Этой функции могло бы не быть, если бы EDMC предоставлял filecmp. Но там как всегда.
        """
        if not (file1.exists() and file2.exists()):
            return True
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            # файлы не такие большие, можем позволить себе считать их полностью
            return f1.read() != f2.read()


# Базовые элементы GUI

class StatusLabel(tk.Label):
    """Отображается в главном окне EDMC. Предназначена для отображения статуса обновлений."""

    def __init__(self, parent: tk.Misc, row: int):
        self.textvar = tk.StringVar()
        self.row = row
        super().__init__(parent, textvariable=self.textvar)

    def set_text(self, val: str):
        self.show()
        self.textvar.set(val)

    def clear(self):
        self.textvar.set("")
        self.hide()

    def show(self):
        self.grid(row=self.row, column=0, sticky="NWS")

    def hide(self):
        self.grid_forget()


class VersionFrame(tk.Frame):
    """Отображается в главном окне EDMC. Отображает версию плагина со ссылкой на страницу релиза."""

    def __init__(self, parent: tk.Misc, version: Version):
        super().__init__(parent)
        self.text_label = tk.Label(self, text=(_translate("Version:") + ' '))
        self.text_label.pack(side="left")

        release_url = f"https://github.com/{Updater.REPOSITORY_PATH}/releases/{version}"
        try:
            res = requests.get(release_url)
            res.raise_for_status()
        except requests.RequestException:
            release_url = None

        if release_url is not None:
            self.version_label = HyperlinkLabel(
                master=self,
                text=str(context.plugin_version),
                url=release_url,
            )
        else:
            self.version_label = tk.Label(
                master=self,
                text=str(context.plugin_version),
            )

        self.version_label.pack(side="left")


class ReleaseTypeSettingFrame(nb.Frame):
    """Фрейм с настройкой типа релиза."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        reltypes_list = [ReleaseType.STABLE.value, ReleaseType.BETA.value]
        if context.updater.release_type == ReleaseType._DEVELOPMENT:
            reltypes_list.append(ReleaseType._DEVELOPMENT.value)

        self.reltype_label = nb.Label(self, text=_translate("Release channel:"))
        self.reltype_label.grid(row=0, column=0, sticky="NW")

        self.reltype_var = tk.StringVar(value=context.updater.release_type)
        self.reltype_var.trace_add('write', self._update_description)
        self.reltype_field = ttk.Combobox(self, values=reltypes_list, textvariable=self.reltype_var, state="readonly")
        self.reltype_field.grid(row=0, column=1, sticky="NW", padx=5)

        self.description_var = tk.StringVar(value=_translate(f"<RELEASE_TYPE_DESCRIPTION_{self.reltype_var.get()}>"))
        self.description_label = nb.Label(self, textvariable=self.description_var)
        self.description_label.grid(row=1, columnspan=2, sticky="NWS")

    def _update_description(self, varname, index, mode):
        self.description_var.set(_translate(f"<RELEASE_TYPE_DESCRIPTION_{self.reltype_var.get()}>"))

    def get_selected_reltype(self):
        return ReleaseType(self.reltype_var.get())


# Функции управления поведением плагина, вызываемые EDMC

def plugin_start(plugin_dir):
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 2.
    """
    raise EnvironmentError(_translate("At least EDMC 5.11.0 is required to use this plugin."))


def plugin_start3(plugin_dir: str) -> str:
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 3.
    Возвращаемое значение - строка, которой будет озаглавлена вкладка плагина в настройках.
    """
    if context.edmc_version < Version("5.11.0"):
        raise EnvironmentError(_translate("At least EDMC 5.11.0 is required to use this plugin."))

    context.plugin_dir = plugin_dir
    context.updater = Updater()
    context.updater.start_update_cycle(_check_now=True)

    return "Triumvirate"


def plugin_stop():
    """
    EDMC вызывает эту функцию при закрытии.
    """
    context.updater.stop_update_cycle()
    if context.plugin_loaded:
        context.plugin_stop_hook()


def plugin_app(parent: tk.Misc) -> tk.Frame:
    """
    EDMC вызывает эту функцию при запуске плагина для получения элемента UI плагина,
    отображаемого в окне программы.
    """
    context.plugin_frame = tk.Frame(parent)
    context.status_label = StatusLabel(context.plugin_frame, 0)
    context.status_label.show()
    return context.plugin_frame


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool) -> nb.Frame:
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    # EDMC позволяет вернуть только их nb.Frame, иначе AssertionError.
    # При этом эта хрень где-то у себя в кишочках что-то маппит grid-ом,
    # поэтому использовать удобный нам pack здесь не выйдет.
    frame = nb.Frame(parent)
    context.settings_frame = ReleaseTypeSettingFrame(frame)
    context.settings_frame.grid(row=0, column=0, sticky="NSWE")
    if context.plugin_loaded:
        context.plugin_prefs_hook(frame, cmdr, is_beta).grid(row=1, column=0, sticky="NWSE")
    return frame


def prefs_changed(cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию при сохранении настроек пользователем.
    """
    new_reltype = context.settings_frame.get_selected_reltype()
    context.settings_frame = None
    if new_reltype != context.updater.release_type:
        edmc_config.set(context.updater.RELEASE_TYPE_KEY, new_reltype)
        context.updater.release_type = new_reltype
        context.updater.restart_update_cycle()
    if context.plugin_loaded:
        context.prefs_changed_hook(cmdr, is_beta)


# Эти функции относятся к внутреигровым событиям.
# Здесь мы будем лишь сохранять все входящие данные в общую очередь.
# После загрузки версии её обработчик ивентов подключится к этой очереди и начнёт её обрабатывать.

def journal_entry(
    cmdr: str | None,
    is_beta: bool,
    system: str | None,
    station: str | None,
    entry: dict,
    state: dict
):
    """
    EDMC вызывает эту функцию при появлении новой записи в логах игры.
    """
    context.event_queue.put({"type": "journal_entry", "data": (cmdr, is_beta, system, station, entry, state)})


def dashboard_entry(cmdr: str | None, is_beta: bool, entry: dict):
    """
    EDMC вызывает эту функцию при обновлении игрой status.json.
    """
    context.event_queue.put({"type": "dashboard_entry", "data": (cmdr, is_beta, entry)})


def cmdr_data(data: dict, is_beta: bool):
    """
    EDMC вызывает эту функцию при получении данных о командире с серверов Frontier.
    """
    context.event_queue.put({"type": "cmdr_data", "data": (data, is_beta)})
