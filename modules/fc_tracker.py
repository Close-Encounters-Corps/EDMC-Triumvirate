import json
import requests
import tkinter as tk
import traceback
from dataclasses import dataclass, fields, asdict
from datetime import datetime, UTC
from enum import Enum
from tkinter import ttk
from typing import Callable

from context import GameState
from modules.debug import debug, error, warning
from modules.legacy import GoogleReporter
from modules.lib.conf import config as plugin_config
from modules.lib.journal import JournalEntry
from modules.lib.module import Module
from modules.lib.thread import BasicThread

import myNotebook as nb

# Подключение функции перевода
import functools
from context import PluginContext
_translate = functools.partial(PluginContext._tr_template, filepath=__file__)


# Эксперимент: декоратор для UI методов, чтобы везде tk.after не пихать
def mainthread(func):
    @functools.wraps(func)
    def wrapper(*args):
        from tkinter import _default_root
        _default_root.after(0, func, *args)
    return wrapper


#################
# КЛАССЫ ДАННЫХ #
#################

class FCStatus(str, Enum):
    UNKNOWN                 = "unknown"
    NOT_BOUGHT              = "not_bought"
    ACTIVE                  = "active"
    PENDING_DECOMMISSION    = "pending_decommission"
    DECOMMISSIONED          = "decommissioned"


class FCDockingAccess(str, Enum):
    ALL                     = "all"
    SQUADRON                = "squadron"
    FRIENDS                 = "friends"
    SQUADRON_AND_FRIENDS    = "squadronfriends"
    NONE                    = "none"


class FCVariant(str, Enum):
    DRAKE                   = "Drake"
    FORTUNE                 = "Fortune"
    VICTORY                 = "Victory"
    NAUTILUS                = "Nautilus"


@dataclass
class FCData:
    cmdr:                   str | None              = None
    status:                 FCStatus                = FCStatus.UNKNOWN
    callsign:               str | None              = None
    name:                   str | None              = None
    variant:                FCVariant | None        = None
    docking_access:         FCDockingAccess | None  = None
    notorious_access:       bool | None             = None
    decommission_timestamp: datetime | None         = None
    role:                   str                     = ""
    comment:                str                     = ""
    _fcspace_link:          str                     = ""

    def asjson(self) -> dict:
        result = asdict(self)
        if isinstance(result["decommission_timestamp"], datetime):
            result["decommission_timestamp"] = datetime.isoformat(result["decommission_timestamp"])
        return result

    def reset(self):
        map(lambda f: setattr(self, f.name, f.default), fields(self))


##############
# КЛАССЫ GUI #
##############

class FCInfoFrame(tk.Frame):
    """
    Фрейм, отображающий информацию по флитаку и дающий возможность настройки необязательных полей (класс, роль, описание).
    """
    def __init__(self, parent, fc_data: FCData):
        super().__init__(parent, bg="white")

        name = "[{}] {}".format(fc_data.callsign, fc_data.name or "???") if fc_data.callsign else _translate("unknown")
        self.name_label = nb.Label(self, text=_translate("Carrier name:"))
        self.name_field = nb.Label(self, text=name)
        self.name_label.grid(row=0, column=0, sticky="W")
        self.name_field.grid(row=0, column=1, padx=3, sticky="W")

        self.variant_var = tk.StringVar(value=(fc_data.variant or "Drake"))
        self.variant_label = nb.Label(self, text=_translate("Carrier class:"))
        self.variant_field = ttk.Combobox(
            self,
            values=[e.value for e in FCVariant],
            textvariable=self.variant_var,
            state="readonly"
        )
        self.variant_label.grid(row=1, column=0, sticky="W")
        self.variant_field.grid(row=1, column=1, padx=3, sticky="W")

        self.access_localized = {
            FCDockingAccess.ALL: _translate("<DOCKING_ACCESS_ALL>"),
            FCDockingAccess.FRIENDS: _translate("<DOCKING_ACCESS_FRIENDS>"),
            FCDockingAccess.SQUADRON: _translate("<DOCKING_ACCESS_SQUADRON>"),
            FCDockingAccess.SQUADRON_AND_FRIENDS: _translate("<DOCKING_ACCESS_SQUADRONFRIENDS>"),
            FCDockingAccess.NONE: _translate("<DOCKING_ACCESS_NONE>")
        }
        self.access_label = nb.Label(self, text=_translate("Docking access:"))
        self.access_field = nb.Label(self, text=self.access_localized.get(fc_data.docking_access, ""))
        self.access_label.grid(row=2, column=0, sticky="W")
        self.access_field.grid(row=2, column=1, padx=3, sticky="W")

        self.notorious_access_localized = {
            True: _translate("<NOTORIOUS_ACCESS_ALLOWED>"),
            False: _translate("<NOTORIOUS_ACCESS_NOT_ALLOWED>")
        }
        self.notorious_access_label = nb.Label(self, text=_translate("Docking permission for notorious:"))
        self.notorious_access_field = nb.Label(self, text=self.notorious_access_localized.get(fc_data.notorious_access, ""))
        self.notorious_access_label.grid(row=3, column=0, sticky="W")
        self.notorious_access_field.grid(row=3, column=1, padx=3, sticky="W")

        self.optional_fields_label = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_OPTIONAL_FIELDS>"))
        self.optional_fields_label.grid(row=4, column=0, columnspan=2, sticky="W")

        self.role_var = tk.StringVar(value=fc_data.role)
        self.role_label = nb.Label(self, text=_translate("Role:"))
        self.role_field = nb.EntryMenu(self, textvariable=self.role_var, width=70)
        self.role_label.grid(row=5, column=0, sticky="W")
        self.role_field.grid(row=5, column=1, padx=3, sticky="W")

        self.comment_var = tk.StringVar(self, value=fc_data.comment)
        self.comment_label = nb.Label(self, text=_translate("Additional comment:"))
        self.comment_field = nb.EntryMenu(self, textvariable=self.comment_var, width=70)
        self.comment_label.grid(row=6, column=0, sticky="W")
        self.comment_field.grid(row=6, column=1, padx=3, sticky="W")

    def get_optional_fields_values(self):
        variant = FCVariant(self.variant_var.get())
        role    = self.role_var.get()
        comment = self.comment_var.get()
        return variant, role, comment


class SettingsFrame(tk.Frame):
    """
    Фрейм настроек модуля.
    Предоставляет пользователю информацию по флитаку, настройку уведомлений о небезопасном разрешении на стыковку,
    показывает пару предупреждений при необходимости.
    """
    def __init__(self, parent: tk.Misc, row: int, config: FCData, disable_access_warnings: bool):
        super().__init__(parent, bg="white")
        decom_timestamp = config.decommission_timestamp.strftime("%x %X") if config.decommission_timestamp else ""

        self.module_name_label = nb.Label(self, text=_translate("Fleet Carrier tracker settings:"))
        self.module_name_label.pack(side="top", anchor="w")

        self.disable_access_warnings_var = tk.BooleanVar(value=disable_access_warnings)
        self.disable_access_warnings_checkbox = nb.Checkbutton(
            self,
            variable=self.disable_access_warnings_var,
            text=_translate("Disable unsafe docking access configuration warnings")
        )
        self.disable_access_warnings_checkbox.pack(side="top", fill="x")

        self.no_fc_label = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_NO_FC>"))
        self.fc_info_frame = FCInfoFrame(self, config)
        self.info_missing_label = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_INFO_MISSING>"))
        self.access_warning_label = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_ACCESS_WARNING>"))
        self.decom_warning_label = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_DECOM_WARNING> {TS}").format(TS=decom_timestamp))   # noqa: E501

        if config.status in (FCStatus.NOT_BOUGHT, FCStatus.DECOMMISSIONED):
            self.no_fc_label.pack(side="top", anchor="w")

        elif config.status == FCStatus.UNKNOWN:
            self.info_missing_label.pack(side="top", anchor="w")

        else:
            self.fc_info_frame.pack(side="top", fill="x")
            if config.docking_access == FCDockingAccess.ALL:
                self.access_warning_label.pack(side="top", anchor="w")
            if config.status == FCStatus.PENDING_DECOMMISSION:
                self.decom_warning_label.pack(side="top", anchor="w")

        self.grid(column=0, row=row, sticky="NWSE")


    def get_current_config(self) -> tuple[bool, FCVariant, str, str]:
        disable_access_warnings = self.disable_access_warnings_var.get()
        variant, role, comment = self.fc_info_frame.get_optional_fields_values()
        return disable_access_warnings, variant, role, comment


class FCModuleFrame(tk.Frame):
    """
    Фрейм модуля, отображаемый при необходимости в главном окне EDMC.
    """
    def __init__(self, parent: tk.Misc, row: int, no_carrier_callback: Callable):
        super().__init__(parent)
        self.row = row
        self.no_carrier_callback = no_carrier_callback

        # варианты отображения
        # 1: у нас нет информации по флитаку
        self.no_fc_info_label = tk.Label(
            self, wraplength=400, justify="left",
            text=_translate("<FC_TRACKER_NO_INFO_TEXT>")
        )
        self.no_fc_info_cancel_button = nb.Button(
            self, command=self.no_carrier_callback,
            text=_translate("I don't have a fleet carrier")
        )

        # 2: игрок купил флитак, и мы просим его зайти в панель флитака
        self.carrier_bought_label = tk.Label(
            self, wraplength=400, justify="left",
            text=_translate("<FC_TRACKER_BOUGHT_TEXT>")
        )

        # 3: мы обнаружили аномалию в логах и просим игрока зайти в панель флитака
        self.unexpected_event_label = tk.Label(
            self, wraplength=400, justify="left",
            text=_translate("<FC_TRACKER_UNEXPECTED_EVENT_TEXT>")
        )

        # 4: после 2 и 3 - мы получили инфу и предлагаем пользователю её проверить в настройках
        self.finish_configuring_fc_label = tk.Label(
            self, wraplength=400, justify="left",
            text=_translate("<FC_TRACKER_FINISH_CONFIGURING_TEXT>")
        )
        self.finish_configuring_close_button = nb.Button(
            self, command=self.__clear,
            text=_translate("Close")
        )

        # 5: предупреждение о небезопасном допуске к стыковке
        self.unsafe_docking_access_label = tk.Label(
            self, wraplength=400, justify="left",
            text=_translate("<FC_TRACKER_UNSAFE_DOCKING_ACCESS_TEXT>")
        )

    @mainthread
    def show_no_fc_info_screen(self):
        debug("[FCModuleFrame] Showing 'No info' screen.")
        self.__clear()
        self.no_fc_info_label.pack(side="top", fill="both")
        self.no_fc_info_cancel_button.pack(side="top", fill="x")
        self.show()

    @mainthread
    def show_carrier_bought_screen(self):
        debug("[FCModuleFrame] Showing 'Carrier bought' screen.")
        self.__clear()
        self.carrier_bought_label.pack(side="top", fill="both")
        self.show()

    @mainthread
    def show_unexpected_event_screen(self):
        debug("[FCModuleFrame] Showing 'Unexpected event' screen.")
        self.__clear()
        self.unexpected_event_label.pack(side="top", fill="both")
        self.show()

    @mainthread
    def show_finish_configuring_screen(self):
        debug("[FCModuleFrame] Showing 'Finish configuring' screen.")
        self.__clear()
        self.finish_configuring_fc_label.pack(side="top", fill="x")
        self.finish_configuring_close_button.pack(side="top", fill="x")
        self.show()

    @mainthread
    def show_unsafe_docking_access_warning(self):
        debug("[FCModuleFrame] Showing unsafe docking access warning.")
        self.__clear()
        self.unsafe_docking_access_label.pack(side="top", fill="both")
        self.show()

    def __clear(self):
        # декоратор не используется, чтобы при отображении экрана очистка не происходила после замаппивания новых виджетов
        for widget in self.winfo_children():
            widget.pack_forget()

    @mainthread
    def show(self):
        debug("[FCModuleFrame] Mapped.")
        self.grid(column=0, row=self.row, sticky="NWSE")

    @mainthread
    def hide(self):
        if not self.is_shown:
            return
        debug("[FCModuleFrame] Hidden.")
        self.__clear()
        self.grid_forget()
        self.master.update()

    @property
    def is_shown(self):
        return self.winfo_ismapped()


################
# КЛАСС МОДУЛЯ #
################

class FC_Tracker(Module):
    """Модуль для отслеживания информации по флитакам: название, код, привязка к fleetcarrier.space и др."""

    FC_DATA_KEY = "FCTracker.CarrierData"
    FC_ACCESS_WARNINGS_KEY = "FCTracker.DisableAccessWarnings"

    def __init__(self, parent: tk.Misc, row: int):
        self.load_fc_data()
        self.ui_frame = FCModuleFrame(parent, row, self.__no_carrier_callback)
        self.just_bought = False    # специально для ситуаций, когда пилот купил флитак, и мы ждём CarrierStats

        self.disable_access_warnings = plugin_config.get_bool(self.FC_ACCESS_WARNINGS_KEY)
        if self.disable_access_warnings is None:
            self.disable_access_warnings = False
            plugin_config.set(self.FC_ACCESS_WARNINGS_KEY, False)
        debug(f"[FC_Tracker] Unsafe docking access warnings are {'disabled' if self.disable_access_warnings else 'enabled'}.")

        if self.fc_data.status == FCStatus.PENDING_DECOMMISSION:
            if datetime.now(UTC) > self.fc_data.decommission_timestamp:
                debug(
                    "[FC_Tracker] Reached saved decommission timestamp ({}), clearing FC data.",
                    self.fc_data.decommission_timestamp.isoformat()
                )
                cmdr, callsign = self.fc_data.cmdr, self.fc_data.callsign
                self.fc_data.reset()
                self.fc_data.status = FCStatus.DECOMMISSIONED
                self.fc_data.cmdr = cmdr
                self.fc_data.callsign = callsign        # он привязан к командиру, а не флитаку; при покупке нового будет тем же
                self.save_fc_data()

        if self.fc_data.status in (FCStatus.ACTIVE, FCStatus.PENDING_DECOMMISSION):
            self.check_docking_access()


    # Методы модуля

    def on_journal_entry(self, journal_entry: JournalEntry):        # noqa: E301
        event = journal_entry.data["event"]
        match event:
            case "CarrierBuy":                  self.carrier_bought(journal_entry)
            case "CarrierStats":                self.carrier_stats(journal_entry)
            case "CarrierDecommission":         self.carrier_planned_decommission(journal_entry)
            case "CarrierCancelDecommission":   self.carrier_cancel_decommission(journal_entry)
            case "CarrierDockingPermission":    self.carrier_docking_access_changed(journal_entry)
            case "CarrierNameChanged":          self.carrier_name_changed(journal_entry)
            case _:
                if (
                    journal_entry.cmdr is not None
                    and self.fc_data.status == FCStatus.UNKNOWN
                    and not self.ui_frame.is_shown
                ):
                    debug("[FC_Tracker] No FC info found.")
                    self.fc_data.cmdr = journal_entry.cmdr
                    self.ui_frame.show_no_fc_info_screen()


    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        self.settings_frame = SettingsFrame(parent_widget, row, self.fc_data, self.disable_access_warnings)


    def on_settings_changed(self, cmdr: str, is_beta: bool):
        self.disable_access_warnings, variant, role, comment = self.settings_frame.get_current_config()
        plugin_config.set(self.FC_ACCESS_WARNINGS_KEY, self.disable_access_warnings)

        self.fc_data.variant = variant
        self.fc_data.role = role
        self.fc_data.comment = comment
        self.save_fc_data()
        debug(("[FC_Tracker] New config: "
               f"unsafe access warnings {'disabled' if self.disable_access_warnings else 'enabled'}, "
               f"FC optional data: variant '{variant}', role '{role}', comment '{comment}'."))

        del self.settings_frame
        self.check_docking_access()


    # Методы-обработчики ивентов флитака

    def carrier_bought(self, journal_entry: JournalEntry):      # noqa: E301
        debug("[FC_Tracker] Detected CarrierBuy.")
        self.just_bought = True
        self.fc_data.reset()
        self.fc_data.status = FCStatus.ACTIVE
        self.fc_data.cmdr = journal_entry.cmdr
        self.fc_data.callsign = journal_entry.data["Callsign"]
        self.fc_data.variant = FCVariant.DRAKE
        self.save_fc_data()
        self.ui_frame.show_carrier_bought_screen()


    def carrier_stats(self, journal_entry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierStats.")

        # для этого ивента unexpected простительно - просто дадим юзеру потом заполнить доп.инфу
        unexpected = self.fc_data.status in (FCStatus.UNKNOWN, FCStatus.NOT_BOUGHT, FCStatus.DECOMMISSIONED)

        self.fc_data.cmdr = journal_entry.cmdr
        self.fc_data.callsign = journal_entry.data["Callsign"]
        self.fc_data.name = journal_entry.data["Name"]
        self.fc_data.docking_access = journal_entry.data["DockingAccess"]
        self.fc_data.notorious_access = journal_entry.data["AllowNotorious"]

        if not self.fc_data.variant:
            self.fc_data.variant = FCVariant.DRAKE

        if not journal_entry.data["PendingDecommission"]:
            self.fc_data.status = FCStatus.ACTIVE
            self.fc_data.decommission_timestamp = None
        else:
            self.fc_data.status = FCStatus.PENDING_DECOMMISSION
            if self.fc_data.decommission_timestamp is None:
                debug("[FC_Tracker] FC is pending decommission, but no saved timestamp found.")
                # CarrierStats не даёт timestamp списания флитака - посчитаем его сами
                # предположительно это ближайший четверг, 07:00 UTC, но требуются дополнительные проверки
                # например, я не уверен, что произойдёт, если запросить списание за ~24 часа до чт7:00
                timestamp = int(datetime.fromisoformat(journal_entry.data["timestamp"]).timestamp())
                timestamp -= 25200                  # отнимаем 7 часов, выравнивая с unix epoch (полночь четверга)
                timestamp += 604800                 # добавляем неделю, чтобы найти ближайший четверг в этом промежутке
                timestamp -= timestamp % 604800     # находим его
                timestamp += 25200                  # добавляем обратно 7 часов
                self.fc_data.decommission_timestamp = datetime.fromtimestamp(timestamp, UTC)
                debug("[FC_Tracker] Calculated decommission timestamp: {}.", self.fc_data.decommission_timestamp.isoformat())

        self.save_fc_data()
        if unexpected or self.just_bought:
            self.ui_frame.show_finish_configuring_screen()
            self.just_bought = False
        else:
            self.ui_frame.hide()
            self.check_docking_access()


    def carrier_planned_decommission(self, journal_entry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierDecommission.")
        if self.fc_data.status in (FCStatus.UNKNOWN, FCStatus.NOT_BOUGHT, FCStatus.DECOMMISSIONED):
            # unexpected event
            warning("[FC_Tracker] Last event was unexpected.")
            self.fc_data.reset()
            self.ui_frame.show_unexpected_event_screen()
            return

        self.fc_data.status = FCStatus.PENDING_DECOMMISSION
        self.fc_data.decommission_timestamp = datetime.fromtimestamp(journal_entry.data["ScrapTime"], UTC)
        self.save_fc_data()


    def carrier_cancel_decommission(self, journal_entry: JournalEntry):
        if self.fc_data.status in (FCStatus.UNKNOWN, FCStatus.NOT_BOUGHT, FCStatus.DECOMMISSIONED):
            # unexpected event
            warning("[FC_Tracker] Last event was unexpected.")
            self.fc_data.reset()
            self.ui_frame.show_unexpected_event_screen()
            return

        self.fc_data.status = FCStatus.ACTIVE
        self.fc_data.decommission_timestamp = None
        self.save_fc_data()


    def carrier_docking_access_changed(self, journal_entry: JournalEntry):
        if self.fc_data.status in (FCStatus.UNKNOWN, FCStatus.NOT_BOUGHT, FCStatus.DECOMMISSIONED):
            # unexpected event
            warning("[FC_Tracker] Last event was unexpected.")
            self.fc_data.reset()
            self.ui_frame.show_unexpected_event_screen()
            return

        self.fc_data.docking_access = journal_entry.data["DockingAccess"]
        self.fc_data.notorious_access = journal_entry.data["AllowNotorious"]
        self.check_docking_access()
        self.save_fc_data()


    def carrier_name_changed(self, journal_entry: JournalEntry):
        # проверяем на unexpected-ность
        unexpected_status = self.fc_data.status in (FCStatus.UNKNOWN, FCStatus.NOT_BOUGHT, FCStatus.DECOMMISSIONED)
        callsign_mismatch = (
            self.fc_data.callsign is not None
            and self.fc_data.callsign != journal_entry.data["Callsign"]
        )
        if unexpected_status or callsign_mismatch:
            warning("[FC_Tracker] Last event was unexpected.")
            if callsign_mismatch:
                warning("[FC_Tracker] Callsign mismatch. New CMDR?")
            self.fc_data.reset()
            self.ui_frame.show_unexpected_event_screen()
            return

        self.fc_data.name = journal_entry.data["CarrierNameChanged"]
        self.save_fc_data()


    def check_docking_access(self):
        if self.fc_data.status not in (FCStatus.ACTIVE, FCStatus.PENDING_DECOMMISSION):
            return
        if self.disable_access_warnings:
            self.ui_frame.hide()
            return

        # TODO: перевести на нормальное определение "союзности", когда будет возможность
        from modules.canonn_api import is_cec_fleetcarrier
        if is_cec_fleetcarrier(self.fc_data.name) or GameState.squadron == "CLOSE ENCOUNTERS CORPS":
            if self.fc_data.docking_access == FCDockingAccess.ALL:
                self.ui_frame.show_unsafe_docking_access_warning()
            else:
                self.ui_frame.hide()


    # Методы управления конфигом модуля

    def load_fc_data(self):     # noqa: E301
        saved = plugin_config.get_str(self.FC_DATA_KEY)
        if saved:
            debug("[FC_Tracker] Loading saved FC data.")
            data = json.loads(saved)
            if isinstance(data["decommission_timestamp"], str):
                data["decommission_timestamp"] = datetime.fromisoformat(data["decommission_timestamp"])
        else:
            debug("[FC_Tracker] No saved data found, setting the default values.")
            data = {}

        self.fc_data = FCData(**data)
        debug(f"[FC_Tracker] Loaded FC data: {self.fc_data}.")
        # на случай первого запуска
        if data == {}:
            self.save_fc_data()


    def save_fc_data(self):
        str_repr = json.dumps(self.fc_data.asjson(), ensure_ascii=False)
        saved = plugin_config.get_str(self.FC_DATA_KEY)
        if str_repr != saved:
            plugin_config.set(self.FC_DATA_KEY, str_repr)
            debug(f"[FC_Tracker] Updated saved FC data: {str_repr}.")
            if self.fc_data.status not in (FCStatus.UNKNOWN, FCStatus.NOT_BOUGHT):
                self.send_fc_data()


    def send_fc_data(self):
        BasicThread(target=self.__submit_form_in_thread, name="FC_Tracker._submit_form").start()

    def __submit_form_in_thread(self):
        self.__check_fleetcarrier_space_account()
        decommission_timestamp = datetime.isoformat(self.fc_data.decommission_timestamp) if self.fc_data.decommission_timestamp else ""

        # TODO: перевести с тестовой формы на основную, когда будет готово
        url = "https://docs.google.com/forms/d/e/1FAIpQLSepZDoWnZeD77CvShDw409j7FCmftaEweAFtlkBzpR7eDNniA/formResponse?usp=pp_url"
        params = {
            "entry.1191899309": self.fc_data.cmdr,
            "entry.1759759791": self.fc_data.callsign,
            "entry.307209108":  self.fc_data.name,
            "entry.1813580887": self.fc_data.status,
            "entry.393285798":  self.fc_data.docking_access,
            "entry.1756948762": self.fc_data.notorious_access,
            "entry.982436332":  self.fc_data._fcspace_link,
            "entry.601824719":  self.fc_data.variant,
            "entry.544438189":  self.fc_data.role,
            "entry.78144414":   self.fc_data.comment,
            "entry.1361520128": decommission_timestamp
        }
        GoogleReporter(url, params).start()


    def __check_fleetcarrier_space_account(self):
        if self.fc_data._fcspace_link:
            return

        # Проверяем наличие аккаунта на fleetcarrier.space
        # Перенаправляет на /carrier/<callsign> -> найдено. Отдаёт 200 -> такого нема.
        # Если реквестить саму /carrier/<callsign> - отдаст 200 в любом случае. Такие дела.
        fc_account_link = ""
        url = f"https://fleetcarrier.space/search?term={self.fc_data.callsign}"

        try:
            res = requests.get(url, allow_redirects=False)
        except requests.RequestException:
            error("[FC_Tracker] Couldn't check for account on fleetcarrier.space:\n" + traceback.format_exc())
            fc_account_link = "[UNKNOWN]"
        else:
            if res.status_code == 200:
                debug("[FC_Tracker] Account on fleetcarrier.space wan't found.")
                fc_account_link = ""
            elif res.status_code == 302:
                debug("[FC_Tracker] Found account on fleetcarrier.space.")
                fc_account_link = f"https://fleetcarrier.space/carrier/{self.fc_data.callsign}"
            else:
                error(
                    "[FC_Tracker] Unexpected status code {} when checking for account on fleetcarrier.space:\n{}",
                    res.status_code, res.text
                )
                fc_account_link = "[UNKNOWN]"

        self.fc_data._fcspace_link = fc_account_link


    # danger zone: эти методы вызывает UI на действия пользователя

    def __no_carrier_callback(self):        # noqa: E301
        # пользователь указал, что флитака во владении не имеет
        debug("[FC_Tracker] User claims not to own a fleet carrier.")
        cmdr = self.fc_data.cmdr
        self.fc_data.reset()
        self.fc_data.status = FCStatus.NOT_BOUGHT
        self.fc_data.cmdr = cmdr
        self.save_fc_data()
        self.ui_frame.hide()
