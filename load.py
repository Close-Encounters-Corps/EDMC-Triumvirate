"""
ПРЕДУПРЕЖДЕНИЕ ПОТОМКАМ И БУДУЩЕМУ СЕБЕ
Текущий механизм автообновлений плагина подразумевает, что импорты из других файлов плагина здесь НЕ РАЗРЕШЕНЫ!
Вся логика инициализации плагина, которая раньше была в load.py, должна быть перенесена в plugin_init.py.
"""

import json
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

from l10n import Locale
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


# Функция перевода
# Из-за ограничений механизма локализации EDMC будем использовать свой
class _Translation:
    fallback_language = "en"
    system_language: str = None
    selected_language: str = None
    available_languages: list[str] = []
    _strings: dict[str, dict[str, dict[str, str]]] = {}

    @classmethod
    def setup(cls):
        sys_lang: str = Locale.preferred_languages()[0]
        if sys_lang.startswith("en-"):
            cls.system_language = "en"
            logger.debug("System language: en.")
        elif sys_lang.startswith("ru-"):
            cls.system_language = "ru"
            logger.debug("System language: en.")
        else:
            logger.debug(f"Unsupported system language ({sys_lang}).")

        translations_dir = Path(context.plugin_dir) / "translations"
        if not translations_dir.exists():
            logger.error("Couldn't locate the directory with translations files.")
            return
        cls.available_languages = [
            f.name.removesuffix(".json")
            for f in translations_dir.iterdir()
            if f.is_file() and f.name.endswith(".json")
        ]
        for lang in cls.available_languages:
            try:
                with open(translations_dir / f"{lang}.json", 'r', encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Couldn't parse language file '{lang}.json'.", exc_info=e)
                cls.available_languages.remove(lang)
            except Exception as e:
                logger.error(f"Error while reading language file '{lang}.json'.", exc_info=e)
                cls.available_languages.remove(lang)
            else:
                cls._strings[lang] = data
        logger.info(f"{len(cls.available_languages)} available translation languages loaded.")

    @classmethod
    def update_active_language(cls, new_lang: str | None):
        if not new_lang:
            new_lang = cls.system_language
        if new_lang not in cls.available_languages:
            new_lang = cls.fallback_language
        cls.selected_language = new_lang
        logger.info(f"Selected language set to {cls.selected_language}.")

    @classmethod
    def translate(cls, x: str, filepath: str, lang: str = None):
        if lang not in cls.available_languages:
            lang = cls.selected_language

        relative = str(Path(filepath).relative_to(context.plugin_dir))
        translation = cls._strings.get(lang, {}).get(relative, {}).get(x)

        if not translation:
            logger.error(f"Missing translation: language '{lang}', file '{relative}', key \"{x}\".")
            return x
        return translation.replace(r"\\", "\\").replace(r"\n", "\n")


_translate = functools.partial(_Translation.translate, filepath=__file__)


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
        # прежде чем запускать процесс обновления, подождём, пока EDMC создаст своё окно
        # увы, winfo_ismapped до этого момента работать тоже не будет, поэтому придётся поколхозничать
        while True:
            try:
                tk._default_root.after(0, lambda: None)
            except RuntimeError:
                logger.debug("Tk isn't ready yet, waiting...")
                sleep(1)
            else:
                break

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

        self.release_type: str = edmc_config.get_str(self.RELEASE_TYPE_KEY)
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

        if self.local_version == Version("0.0.0"):
            # первый запуск плагина после обновления до 1.12.0
            logger.info((
                "No saved local version info found."
                "Assuming 1.12.0 or higher is installed for the first time, stopping the updating process."
            ))
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
            logger.info(f"Local version ({self.local_version}) matches the latest release. No updates required.")
            context.status_label.clear()
            self.__use_local_version()
        else:
            if latest_version < self.local_version:
                logger.info((f"Remote version ({latest_version}) is lower than the local one ({self.local_version}). "
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
            shutil.copytree(Path(context.plugin_dir, "userdata"), Path(new_ver_path, "userdata"), dirs_exist_ok=True)
        except FileNotFoundError:
            logger.warning("Directory `userdata` not found, skipping.")

        # сносим старую версию и копируем на её место новую, удаляем временные файлы
        logger.info("Replacing plugin files...")
        shutil.rmtree(context.plugin_dir, ignore_errors=True)
        shutil.copytree(new_ver_path, context.plugin_dir, dirs_exist_ok=True)
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
            context.status_label.set_text(_translate("The update is installed. Please restart EDMC."))


    def __use_local_version(self):
        if context.plugin_loaded:
            return

        def __inner(self):
            logger.info("Loading local version the in main thread...")
            if not Path(context.plugin_dir, "context.py").exists():
                logger.error("`context` module not found. Aborting.")
                context.status_label.set_text(_translate("Error: plugin files are corrupted. Unable to start the plugin."))
                return
            if not Path(context.plugin_dir, "plugin_init.py").exists():
                logger.error("`plugin_init` module not found. Aborting.")
                context.status_label.set_text(_translate("Error: plugin files are corrupted. Unable to start the plugin."))
                return

            # сначала инициализируем контекст версии уже созданными объектами
            from context import PluginContext as VersionContext
            VersionContext.logger = logger
            VersionContext.plugin_dir = context.plugin_dir
            VersionContext.edmc_version = context.edmc_version
            VersionContext._tr_template = _Translation.translate
            VersionContext._event_queue = context.event_queue

            version_mismatch = False
            context.plugin_version = VersionContext.plugin_version
            if self.local_version != context.plugin_version:
                logger.warning("Saved local version doesn't match the loaded one. This could be due to a manual update.")
                edmc_config.set(self.LOCAL_VERSION_KEY, str(context.plugin_version))
                self.local_version = context.plugin_version
                logger.warning(f"Local version set to {context.plugin_version}.")
                version_mismatch = True
                if "dev" in context.plugin_version.prerelease:
                    logger.info("Local version is of development release type, changing Updater settings.")
                    edmc_config.set(context.updater.RELEASE_TYPE_KEY, ReleaseType._DEVELOPMENT)
                    context.updater.release_type = ReleaseType._DEVELOPMENT

            # и лишь теперь мы можем стартовать саму версию
            import plugin_init
            context.plugin_stop_hook = plugin_init.plugin_stop
            context.plugin_prefs_hook = plugin_init.plugin_prefs
            context.prefs_changed_hook = plugin_init.prefs_changed

            plugin_init.init_version()

            context.status_label.clear()
            context.version_frame = VersionFrame(context.plugin_frame, context.plugin_version)
            context.plugin_ui = plugin_init.plugin_app(context.plugin_frame)
            theme.update(context.version_frame)
            theme.update(context.plugin_ui)
            context.version_frame.grid(row=0, column=0, sticky="NWS")
            context.plugin_ui.grid(row=2, column=0, sticky="NWSE")

            context.plugin_loaded = True
            logger.info("Local version configured, running.")
            if version_mismatch:
                context.updater.restart_update_cycle()


        # фикс для development-версий: удостоверимся, что userdata всегда существует
        Path(context.plugin_dir, "userdata").mkdir(exist_ok=True)
        # грузим версию в главном потоке
        logger.info("IGNORE THE FOLLOWING LOGGING ALERTS. They appear because of tkinter and EDMC logging implementations.")
        tk._default_root.after(0, __inner, self)


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
        def __inner(self, val):
            self.show()
            self.textvar.set(val)
        self.after(0, __inner, self, val)

    def clear(self):
        def __inner(self):
            self.textvar.set("")
            self.hide()
        self.after(0, __inner, self)

    def show(self):
        def __inner(self):
            self.grid(row=self.row, column=0, sticky="NWS")
        self.after(0, __inner, self)

    def hide(self):
        def __inner(self):
            self.grid_forget()
        self.after(0, __inner, self)


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


class ReleaseTypeSettingFrame(tk.Frame):
    """Фрейм с настройкой типа релиза."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent, bg="white")
        reltypes_list = [ReleaseType.STABLE.value, ReleaseType.BETA.value]
        if (
            context.updater.release_type == ReleaseType._DEVELOPMENT
            or context.plugin_version is not None and "dev" in context.plugin_version.prerelease
        ):
            reltypes_list.append(ReleaseType._DEVELOPMENT.value)

        self.topframe = tk.Frame(self, bg="white")
        self.reltype_label = tk.Label(self.topframe, bg="white", text=_translate("Release channel:"))
        self.reltype_label.pack(side="left")

        self.reltype_var = tk.StringVar(value=context.updater.release_type)
        self.reltype_var.trace_add('write', self._update_description)
        self.reltype_field = ttk.Combobox(self.topframe, values=reltypes_list, textvariable=self.reltype_var, state="readonly")
        self.reltype_field.pack(side="left", padx=5)

        self.topframe.pack(side="top", anchor="w")

        self.rt_descriptions = {
            "Stable": _translate("<RELEASE_TYPE_DESCRIPTION_STABLE>"),
            "Beta": _translate("<RELEASE_TYPE_DESCRIPTION_BETA>"),
            "Development": _translate("<RELEASE_TYPE_DESCRIPTION_DEVELOPMENT>")
        }
        self.description_var = tk.StringVar(value=self.rt_descriptions.get(self.reltype_var.get(), ""))
        self.description_label = tk.Label(self, textvariable=self.description_var, justify="left", bg="white")
        self.description_label.pack(side="top", anchor="w")

    def _update_description(self, varname, index, mode):
        self.description_var.set(self.rt_descriptions[self.reltype_var.get()])

    def get_selected_reltype(self):
        return ReleaseType(self.reltype_var.get())


# Функции управления поведением плагина, вызываемые EDMC

def plugin_start(plugin_dir):
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 2.
    """
    raise EnvironmentError(_translate("This plugin requires EDMC version 5.11.0 or later."))


def plugin_start3(plugin_dir: str) -> str:
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 3.
    Возвращаемое значение - строка, которой будет озаглавлена вкладка плагина в настройках.
    """
    context.plugin_dir = plugin_dir
    _Translation.setup()
    _Translation.update_active_language(edmc_config.get_str("language"))

    if context.edmc_version < Version("5.11.0"):
        raise EnvironmentError(_translate("This plugin requires EDMC version 5.11.0 or later."))

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
    context.status_label = StatusLabel(context.plugin_frame, 1)
    context.status_label.show()
    context.updater = Updater()
    context.updater.start_update_cycle(_check_now=True)
    return context.plugin_frame


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool) -> nb.Frame:
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    # EDMC позволяет вернуть только их nb.Frame, иначе AssertionError.
    # При этом эта хрень где-то у себя в кишочках что-то маппит grid-ом,
    # поэтому использовать удобный нам pack здесь не выйдет.
    frame = nb.Frame(parent)
    frame.grid_columnconfigure(0, weight=1)
    context.settings_frame = ReleaseTypeSettingFrame(frame)
    context.settings_frame.grid(row=0, column=0, sticky="NSWE")
    if context.plugin_loaded:
        context.plugin_prefs_hook(frame, cmdr, is_beta).grid(row=1, column=0, sticky="NWSE")
    return frame


def prefs_changed(cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию при сохранении настроек пользователем.
    """
    _Translation.update_active_language(edmc_config.get_str("language"))
    new_reltype = context.settings_frame.get_selected_reltype()
    context.settings_frame = None
    if new_reltype == ReleaseType._DEVELOPMENT:
        context.status_label.clear()
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
