"""
ПРЕДУПРЕЖДЕНИЕ ПОТОМКАМ И БУДУЩЕМУ СЕБЕ
Текущий механизм автообновлений плагина подразумевает, что импорты из других файлов плагина здесь НЕ РАЗРЕШЕНЫ!
Вся логика инициализации плагина, которая раньше была в load.py, должна быть перенесена в core/plugin_init.py.
"""

import functools
import json
import logging
import os
import requests
import shutil
import tempfile
import threading
import tkinter as tk
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from queue import Queue
from semantic_version import Version
from time import sleep
from tkinter import ttk

import myNotebook as nb  # pyright: ignore[reportMissingImports]
from config import appname, appversion  # pyright: ignore[reportMissingImports]
from config import config as edmc_config  # pyright: ignore[reportMissingImports]
from l10n import Locale  # pyright: ignore[reportMissingImports]
from theme import theme  # pyright: ignore[reportMissingImports]
from ttkHyperlinkLabel import HyperlinkLabel  # pyright: ignore[reportMissingImports]


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

    ВАЖНО: часть объектов, помеченная конкретными типами, на деле инициализируется в None
    с подавлением ошибок. Эти объекты создаются в процессе запуска EDMC и плагина
    в функциях `plugin_start3` и `plugin_app`. Это сделано осознанно, т.к. предполагается,
    что любые действия обновлятор и плагин в целом должны проводить только после полной
    инициализации EDMC. Если вы попытаетесь их использовать слишком рано и логичным образом
    нарветесь на эксепшены, вина на вас.
    """
    plugin_name: str = "Triumvirate"
    edmc_version: Version = appversion() if callable(appversion) else Version(appversion)  # pyright: ignore[reportAssignmentType]
    event_queue: Queue[dict] = Queue()
    _shutdown: bool = False

    # инициализируется в plugin_start3
    plugin_dir: Path = None  # pyright: ignore[reportAssignmentType]

    # инициализируются в plugin_app
    updater: "Updater" = None  # pyright: ignore[reportAssignmentType]
    plugin_frame: tk.Frame = None  # pyright: ignore[reportAssignmentType]
    status_label: "StatusLabel" = None  # pyright: ignore[reportAssignmentType]

    # создается в plugin_prefs, сбрасывается в None в prefs_changed
    settings_frame: "ReleaseTypeSettingFrame | None" = None

    # выставляются после инициализации версии и больше не могут быть изменены без перезапуска EDMC
    plugin_loaded: bool = False
    plugin_version: Version | None = None
    version_frame: "VersionFrame | None" = None
    plugin_ui: tk.Frame | None = None
    plugin_stop_hook: Callable | None = None
    plugin_prefs_hook: Callable | None = None
    prefs_changed_hook: Callable | None = None


context = BasicContext()


# Механизм перевода
# Из-за ограничений механизма локализации EDMC будем использовать свой
class _Translation:
    fallback_language = "en"
    system_language: str
    selected_language: str
    available_languages: list[str] = []
    _strings: dict[str, dict[str, dict[str, str]]] = {}     # {"lang": {"file": {"key": "value"}}}

    @classmethod
    def read_system_language(cls):
        sys_lang: str = Locale.preferred_languages()[0]
        if sys_lang.startswith("en-"):
            cls.system_language = "en"
            logger.debug("System language: en.")
        elif sys_lang.startswith("ru-"):
            cls.system_language = "ru"
            logger.debug("System language: ru.")
        else:
            logger.debug(f"Unsupported system language ({sys_lang}).")
            cls.system_language = sys_lang

    @classmethod
    def read_translations(cls):
        translations_dir = context.plugin_dir / "translations"
        if not translations_dir.exists():
            logger.error("Couldn't find the directory with the translation files.")
            return
        lang_files = [
            f.name.removesuffix(".json")
            for f in translations_dir.iterdir()
            if f.is_file() and f.name.endswith(".json")
        ]
        cls.available_languages = [lang for lang in lang_files if cls._load_language(translations_dir, lang)]
        logger.info(f"Loaded {len(cls.available_languages)} languages: {cls.available_languages}")

    @classmethod
    def _load_language(cls, translations_dir: Path, lang: str) -> bool:
        try:
            with open(translations_dir / f"{lang}.json", 'r', encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Couldn't parse language file '{lang}.json'. Exception info:", exc_info=e)
            return False
        except Exception as e:
            logger.error(f"Error while reading language file '{lang}.json'. Exception info:", exc_info=e)
            return False
        else:
            cls._strings[lang] = data
            return True

    @classmethod
    def update_active_language(cls, new_lang: str | None):
        if not new_lang:
            new_lang = cls.system_language
        if new_lang not in cls.available_languages:
            new_lang = cls.fallback_language
        cls.selected_language = new_lang
        logger.info(f"Selected language set to {cls.selected_language}.")

    @classmethod
    def translate(cls, x: str, filepath: str, lang: str | None = None):
        if lang not in cls.available_languages:
            lang = cls.selected_language

        relative_path = str(Path(filepath).relative_to(context.plugin_dir).as_posix())
        translation = cls._strings.get(lang, {}).get(relative_path, {}).get(x)
        if not translation:
            logger.error(f"Missing translation: language '{lang}', file '{relative_path}', key \"{x}\".")
            return x
        return translation.replace(r"\\", "\\").replace(r"\n", "\n")


_translate = functools.partial(_Translation.translate, filepath=__file__)


# Механизм обновления плагина

class ReleaseType(StrEnum):
    STABLE = "Stable"
    BETA = "Beta"
    _DEVELOPMENT = "Development"  # не должен быть публичным, тк, по сути, отключает автообновление


class UpdateCycle(threading.Thread):
    """
    Поток, крутящийся в фоне и время от времени проверяющий наличие обновлений.
    """
    UPDATE_CYCLE = 30 * 60
    STEP = 1

    def __init__(self, updater_fn: Callable, check_now: bool):
        super().__init__()
        self._stop = threading.Event()  # флаг остановки потока
        self._updater_fn = updater_fn
        self._check_now = check_now

    def stop(self):
        self._stop.set()

    def run(self):
        if self._check_now:
            self._updater_fn()
        timer = self.UPDATE_CYCLE
        while not (self._stop.is_set() or edmc_config.shutting_down):
            if timer <= 0:
                self._updater_fn()
                timer = self.UPDATE_CYCLE
            timer -= self.STEP
            sleep(self.STEP)


class Updater:
    """
    Класс, отвечающий за загрузку, распаковку, проверку и установку обновлений плагина.
    """
    DEFAULT_RELEASE_TYPE = ReleaseType.BETA  # TODO: изменить на STABLE после выпуска 1.12.0
    RELEASE_TYPE_KEY = "Triumvirate.Updater.ReleaseType"
    LOCAL_VERSION_KEY = "Triumvirate.Updater.LocalVersion"
    REPOSITORY_PATH = "Close-Encounters-Corps/EDMC-Triumvirate"
    VERSION_FILE_NAME = ".version"

    def __init__(self):
        self.updater_thread: UpdateCycle | None = None
        self.version_file_path = Path(context.plugin_dir) / context.plugin_name / self.VERSION_FILE_NAME
        try:
            self.local_version = Version(self.version_file_path.read_text())
        except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
            logger.error(f"Failed to read the local .version file: {e}")
            self.local_version = None
        except ValueError as e:
            logger.error(f"Failed to parse the local .version file: {e}")
            self.local_version = None

        saved_rt = edmc_config.get_str(self.RELEASE_TYPE_KEY)
        if saved_rt not in ReleaseType:
            logger.info(f"Missing or invalid saved release type: {saved_rt!r}. Resetting to default ({self.DEFAULT_RELEASE_TYPE}).")
            edmc_config.set(self.RELEASE_TYPE_KEY, self.DEFAULT_RELEASE_TYPE)
            saved_rt = self.DEFAULT_RELEASE_TYPE
        else:
            saved_rt = ReleaseType(saved_rt)
        self.release_type = saved_rt


    def start_update_cycle(self, check_now: bool = False):
        if self.updater_thread:
            return
        self.updater_thread = UpdateCycle(self.__check_for_updates, check_now)
        self.updater_thread.start()
        logger.debug("UpdateCycle started.")


    def stop_update_cycle(self):
        if not self.updater_thread:
            return
        self.updater_thread.stop()
        if self.updater_thread is not threading.current_thread():
            self.updater_thread.join()
        self.updater_thread = None
        logger.debug("UpdateCycle stopped.")


    def restart_update_cycle(self):
        self.stop_update_cycle()
        self.start_update_cycle(check_now=True)


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
            logger.error("Couldn't get the list of versions from GitHub. Exception info:", exc_info=e)
            context.status_label.set_text(_translate("Error: couldn't check for updates."))
            self.__use_local_version()
            return

        # получаем последний релиз
        releases = res.json()
        latest_stable = Version(next((r["tag_name"] for r in releases if not r["prerelease"]), "0.0.0"))
        latest_beta = Version(next((r["tag_name"] for r in releases if r["prerelease"]), "0.0.0"))
        if latest_beta < latest_stable:
            latest_beta = latest_stable

        latest = latest_stable if self.release_type == ReleaseType.STABLE else latest_beta
        if latest == Version("0.0.0"):
            # никогда не должно произойти, если только кто-то не удалит все релизы с гитхаба
            # UPD: на практике выяснилось, что сбои у гитхаба могут также давать пустой список с кодом 200
            logger.error("No suitable release found on GitHub. Something's wrong with the repository?")
            context.status_label.set_text(_translate("Error: couldn't check for updates."))
            self.__use_local_version()
            return

        # сверяем с имеющейся версией
        if latest == self.local_version:
            logger.info(f"Local version ({self.local_version}) matches the latest release. No updates required.")
            context.status_label.clear()
            self.__use_local_version()
        else:
            logger.info(f"Remote version ({latest}) doesn't match the local one ({self.local_version}).")
            if not context.plugin_loaded:
                logger.info("Plugin not loaded yet, proceeding to downloading.")
                self.__download_update(latest)
            else:
                logger.info("Plugin already loaded - can't update without a restart. Notifying the user.")
                context.status_label.set_text(
                    _translate("An update is available ({v}). Please restart EDMC.").format(v=str(latest))
                )


    def __download_update(self, tag: Version):
        context.status_label.set_text(_translate("Downloading an update..."))
        url = f"https://api.github.com/repos/{self.REPOSITORY_PATH}/zipball/{tag}"
        tempdir = Path(tempfile.gettempdir()) / f"EDMC-{context.plugin_name}"
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
            logger.error("Couldn't download the version archive from GitHub. Exception info:", exc_info=e)
            context.status_label.set_text(_translate("Error: couldn't download an update."))
            self.__use_local_version()
            return
        except Exception as e:
            logger.error("Unexpected error while downloading the update! Exception info:", exc_info=e)
            context.status_label.set_text(_translate("Failed to update the plugin - unexpected error!"))
            self.__use_local_version()
            return

        # распаковываем
        context.status_label.set_text(_translate("Installing an update..."))
        logger.info("Extracting the new version archive to the temporary directory...")
        with zipfile.ZipFile(version_zip, 'r') as zf:
            zf.extractall(tempdir)
        version_zip.unlink()

        # сверяем текущий load.py с новым - это нам понадобится в будущем
        new_ver_path = next(tempdir.iterdir())  # гитхаб оборачивает файлы в отдельную директорию
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
        self.local_version = tag
        if not (self.version_file_path.exists() and self.version_file_path.is_file()):
            logger.warning("New installed version doesn't include the `.version` file.")
        else:
            try:
                file_version = Version(self.version_file_path.read_text())
                if file_version != tag:
                    logger.warning(f"New `.version` ({file_version}) doesn't match the tag ({tag}).")
            except PermissionError as e:
                logger.warning(f"Can't read the new `.version` file: {e}")
            except ValueError as e:
                logger.warning(f"Failed to parse the new `.version` file: {e}")
        logger.info(f"Done. Local version set to {tag}.")

        # определяем, что нам делать дальше: грузиться или просить перезапустить EDMC
        if not loadpy_was_edited:
            # после обновления могли измениться строки перевода и доступные языки
            _Translation.read_translations()
            _Translation.update_active_language(edmc_config.get_str("language"))
            context.status_label.clear()
            self.__use_local_version()
        else:
            logger.info("load.py was modified. EDMC restart is required.")
            if self.updater_thread:
                self.updater_thread.stop()
            context.status_label.set_text(_translate("The update is installed. Please restart EDMC."))


    def __use_local_version(self):
        if context.plugin_loaded:
            return

        def __inner():
            logger.info(f"Loading local version {self.local_version} the in main thread...")
            if not Path(context.plugin_dir, context.plugin_name, "plugin_init.py").exists():
                logger.error("`plugin_init` module not found. Aborting.")
                context.status_label.set_text(_translate("Error: plugin files are corrupted. Unable to start the plugin."))
                return

            import Triumvirate.plugin_init as plugin_init
            context.plugin_stop_hook = plugin_init.plugin_stop
            context.plugin_prefs_hook = plugin_init.plugin_prefs
            context.prefs_changed_hook = plugin_init.prefs_changed

            context.status_label.clear()
            context.version_frame = VersionFrame(context.plugin_frame, self.local_version)  # pyright: ignore[reportArgumentType]
            context.plugin_ui = plugin_init.initialize(
                edmc_version=context.edmc_version,
                plugin_name=context.plugin_name,
                plugin_version=self.local_version,  # pyright: ignore[reportArgumentType]
                plugin_root_dir=context.plugin_dir,
                ui_parent=context.plugin_frame,
                logger=logger,
                event_queue=context.event_queue,
                translation_fn=_Translation.translate,
            )
            theme.register(context.version_frame)
            theme.register(context.plugin_ui)
            # theme.register и theme.update не проверяют пары виджетов,
            # поэтому мы легко можем случайно замаппить, например, кнопки не для той темы.
            # Чтобы нам с этим не париться во всех модулях, вынудим EDMC заново применить тему на весь GUI.
            # NOTE: _default_root здесь нельзя заменить на нормальный виджет, потому что theme.apply()
            # пытается что-то там делать с параметром `-menu`, который есть только у tk.Tk и tk.Toplevel.
            theme.apply(tk._default_root)  # pyright: ignore[reportAttributeAccessIssue]
            context.version_frame.grid(row=0, column=0, sticky="NWS")
            context.plugin_ui.grid(row=2, column=0, sticky="NWSE")

            context.plugin_loaded = True
            context.plugin_version = self.local_version
            logger.info(f"Local version {self.local_version} configured, running.")

        # грузим версию в главном потоке
        Path(context.plugin_dir, "userdata").mkdir(exist_ok=True)
        context.plugin_frame.after_idle(__inner)


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
                text=str(version),
                url=release_url,
            )
        else:
            self.version_label = tk.Label(
                master=self,
                text=str(version),
            )

        self.version_label.pack(side="left")


class ReleaseTypeSettingFrame(tk.Frame):
    """Фрейм с настройкой типа релиза."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent, bg="white")
        reltypes_list = [ReleaseType.STABLE.value, ReleaseType.BETA.value]
        if (
            context.updater.release_type == ReleaseType._DEVELOPMENT
            or (
                context.plugin_version is not None
                and context.plugin_version.prerelease is not None
                and "dev" in context.plugin_version.prerelease
            )
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
    raise EnvironmentError("This plugin requires EDMC version 5.11.0 or later.")


def plugin_start3(plugin_dir: str) -> str:
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 3.
    Возвращаемое значение - строка, которой будет озаглавлена вкладка плагина в настройках.
    """
    if context.edmc_version < Version("5.11.0"):
        raise EnvironmentError("This plugin requires EDMC version 5.11.0 or later.")
    context.plugin_dir = Path(plugin_dir)
    _Translation.read_system_language()
    _Translation.read_translations()
    _Translation.update_active_language(edmc_config.get_str("language"))
    return context.plugin_name


def plugin_stop():
    """
    EDMC вызывает эту функцию при закрытии.
    """
    # Пользователь может накликать кнопку отключения в настройках EDMC несколько раз,
    # и мы получим несколько вызовов этой функции.
    # https://github.com/EDCD/EDMarketConnector/issues/2605
    if context._shutdown:
        return
    context._shutdown = True
    logger.info("Received plugin_stop signal, starting shutdown procedures.")
    context.updater.stop_update_cycle()
    if context.plugin_loaded:
        logger.debug("Passing the shutdown signal to the loaded version.")
        context.plugin_stop_hook()  # pyright: ignore[reportOptionalCall]
    logger.info("Done.")


def plugin_app(parent: tk.Misc) -> tk.Frame:
    """
    EDMC вызывает эту функцию при запуске плагина для получения элемента UI плагина,
    отображаемого в окне программы.
    """
    context.plugin_frame = tk.Frame(parent)
    context.plugin_frame.grid_columnconfigure(0, weight=1)
    context.status_label = StatusLabel(context.plugin_frame, 1)
    context.status_label.show()
    context.updater = Updater()
    parent.after_idle(context.updater.start_update_cycle, True)
    return context.plugin_frame


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool) -> nb.Frame:
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    if context._shutdown:   # никогда не должно произойти, но предосторожность не помешает
        return
    # EDMC позволяет вернуть только их nb.Frame, иначе AssertionError.
    # При этом эта хрень где-то у себя в кишочках что-то маппит grid-ом,
    # поэтому использовать удобный нам pack здесь не выйдет.
    frame = nb.Frame(parent)
    frame.grid_columnconfigure(0, weight=1)
    context.settings_frame = ReleaseTypeSettingFrame(frame)
    context.settings_frame.grid(row=0, column=0, sticky="NSWE")
    if context.plugin_loaded:
        context.plugin_prefs_hook(frame, cmdr, is_beta).grid(row=1, column=0, sticky="NWSE")  # pyright: ignore[reportOptionalCall]
    return frame


def prefs_changed(cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию при сохранении настроек пользователем.
    """
    if context._shutdown:   # никогда не должно произойти, но предосторожность не помешает
        return
    _Translation.update_active_language(edmc_config.get_str("language"))
    new_reltype = context.settings_frame.get_selected_reltype()  # pyright: ignore[reportOptionalMemberAccess]
    context.settings_frame = None
    if new_reltype == ReleaseType._DEVELOPMENT:
        context.status_label.clear()
    if new_reltype != context.updater.release_type:
        edmc_config.set(context.updater.RELEASE_TYPE_KEY, new_reltype.value)
        context.updater.release_type = new_reltype
        context.updater.restart_update_cycle()
    if context.plugin_loaded:
        context.prefs_changed_hook(cmdr, is_beta)  # pyright: ignore[reportOptionalCall]


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
    if context._shutdown:
        return
    context.event_queue.put({"type": "journal_entry", "data": (cmdr, is_beta, system, station, entry, state)})


def dashboard_entry(cmdr: str | None, is_beta: bool, entry: dict):
    """
    EDMC вызывает эту функцию при обновлении игрой status.json.
    """
    if context._shutdown:
        return
    context.event_queue.put({"type": "dashboard_entry", "data": (cmdr, is_beta, entry)})


def cmdr_data(data: dict, is_beta: bool):
    """
    EDMC вызывает эту функцию при получении данных о командире с серверов Frontier.
    """
    if context._shutdown:
        return
    context.event_queue.put({"type": "cmdr_data", "data": (data, is_beta)})
