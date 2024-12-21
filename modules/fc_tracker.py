import json
import requests
import tkinter as tk
import traceback
from copy import deepcopy
from dataclasses import dataclass, asdict as dataclass_asdict
from datetime import datetime, UTC
from enum import Enum
from tkinter import ttk
from typing import Callable, Any

from modules.debug import debug, error
from modules.legacy import Reporter
from modules.lib.conf import config as plugin_config
from modules.lib.context import global_context
from modules.lib.journal import JournalEntry
from modules.lib.module import Module
from modules.lib.thread import BasicThread

import myNotebook as nb

# Подключение функции перевода от EDMC
import l10n, functools
_translate = functools.partial(l10n.translations.tl, context=__file__)



class _FCStatus(str, Enum):
    UNKNOWN                 = "unknown"
    NOT_BOUGHT              = "not_bought"
    ACTIVE                  = "active"
    PENDING_DECOMMISSION    = "pending_decommission"
    DECOMMISSIONED          = "decommissioned"


class _FCDockingAccess(str, Enum):
    ALL                     = "all"
    SQUADRON                = "squadron"
    FRIENDS                 = "friends"
    SQUADRON_AND_FRIENDS    = "squadronfriends"
    NONE                    = "none"


class _FCClass(str, Enum):
    DRAKE                   = "Drake"
    FORTUNE                 = "Fortune"
    VICTORY                 = "Victory"
    NAUTILUS                = "Nautilus"


@dataclass
class _FCConfig:
    cmdr:                   str | None              = None
    status:                 _FCStatus               = _FCStatus.UNKNOWN
    callsign:               str | None              = None
    name:                   str | None              = None
    variant:                _FCClass | None         = None
    docking_access:         _FCDockingAccess | None = None
    notorious_access:       bool | None             = None
    decommission_timestamp: datetime | None         = None
    role:                   str                     = ""
    comment:                str                     = ""
    
    def is_incomplete(self) -> bool:
        return (
            self.status == _FCStatus.UNKNOWN
            or (
                self.status in (_FCStatus.ACTIVE, _FCStatus.PENDING_DECOMMISSION)
                and None in (self.cmdr, self.callsign, self.name, self.variant, self.notorious_access)
            )
            or (
                self.status == _FCStatus.PENDING_DECOMMISSION
                and self.decommission_timestamp is None
            )
        )
    
    def asjson(self) -> dict:
        result = dataclass_asdict(self)
        if isinstance(result["decommission_timestamp"], datetime):
            result["decommission_timestamp"] = datetime.isoformat(result["decommission_timestamp"])
        return result


class _FCInfoFrame(tk.Frame):
    def __init__(self, parent, config: _FCConfig):
        super().__init__(parent, bg="white")

        name = "[{}] {}".format(config.callsign, config.name or "???") if config.callsign else _translate("unknown")
        self.name_label     = nb.Label(self, text=_translate("Carrier name:"))
        self.name_field     = nb.Label(self, text=name)
        self.name_label.grid(row=0, column=0, sticky="W")
        self.name_field.grid(row=0, column=1, padx=3, sticky="W")

        self.class_var      = tk.StringVar(value=(config.variant or _translate("unknown")))
        self.class_label    = nb.Label(self, text=_translate("Carrier class:"))
        self.class_field    = ttk.Combobox(
            self,
            values=[e.value for e in _FCClass],
            textvariable=self.class_var,
            state="readonly"
        )
        self.class_label.grid(row=1, column=0, sticky="W")
        self.class_field.grid(row=1, column=1, padx=3, sticky="W")

        self.access_label   = nb.Label(self, text=_translate("Docking access:"))
        self.access_field   = nb.Label(self, text=_translate(config.docking_access))
        self.access_label.grid(row=2, column=0, sticky="W")
        self.access_field.grid(row=2, column=1, padx=3, sticky="W")

        self.notorious_access_label = nb.Label(self, text=_translate("Docking allowed for notorious:"))
        self.notorious_access_field = nb.Label(self, text=_translate(config.notorious_access))
        self.notorious_access_label.grid(row=3, column=0, sticky="W")
        self.notorious_access_field.grid(row=3, column=1, padx=3, sticky="W")

        self.optional_fields_label  = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_OPTIONAL_FIELDS>"))
        self.optional_fields_label.grid(row=4, column=0, columnspan=2, sticky="W")

        self.role_var   = tk.StringVar(value=config.role)
        self.role_label = nb.Label(self, text=_translate("Role:"))
        self.role_field = nb.EntryMenu(self, textvariable=self.role_var, width=70)
        self.role_label.grid(row=5, column=0, sticky="W")
        self.role_field.grid(row=5, column=1, padx=3, sticky="W")

        self.comment_var    = tk.StringVar(self, value=config.comment)
        self.comment_label  = nb.Label(self, text=_translate("Additional comment:"))
        self.comment_field  = nb.EntryMenu(self, textvariable=self.comment_var, width=70)
        self.comment_label.grid(row=6, column=0, sticky="W")
        self.comment_field.grid(row=6, column=1, padx=3, sticky="W")


class _SettingsFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, row: int, config: _FCConfig, disable_access_warnings: bool):
        super().__init__(parent, bg="white")
        decom_timestamp = config.decommission_timestamp.strftime("%x %X") if config.decommission_timestamp else ""

        self.module_name_label = nb.Label(self, text=_translate("FC Tracker settings:"))
        self.module_name_label.pack(side="top", anchor="w")

        self.disable_access_warnings_frame = tk.Frame(self, bg="white")
        self.disable_access_warnings_var = tk.BooleanVar(value=disable_access_warnings)
        self.disable_access_warnings_checkbox = nb.Checkbutton(self.disable_access_warnings_frame, variable=self.disable_access_warnings_var)
        self.disable_access_warnings_label = nb.Label(
            self.disable_access_warnings_frame,
            text=_translate("Disable warnings about unsafe docking access configuration")
        )
        self.disable_access_warnings_checkbox.grid(row=0, column=0)
        self.disable_access_warnings_label.grid(row=0, column=1, sticky="W")
        self.disable_access_warnings_frame.pack(side="top", fill="x")

        self.no_fc_label            = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_NO_FC_INFO>"))
        self.fc_info_frame          = _FCInfoFrame(self, config)
        self.info_missing_label     = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_INFO_MISSING>"))
        self.access_warning_label   = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_ACCESS_WARNING>"))
        self.decom_warning_label    = nb.Label(self, text=_translate("<FC_TRACKER_SETTINGS_DECOM_WARNING> {TS}").format(TS=decom_timestamp))

        if config.status in (_FCStatus.NOT_BOUGHT, _FCStatus.UNKNOWN, _FCStatus.DECOMMISSIONED):
            self.no_fc_label.pack(side="top", anchor="w")

        elif config.is_incomplete():
            self.info_missing_label.pack(side="top", anchor="w")
        
        else:
            if config.status in (_FCStatus.ACTIVE, _FCStatus.PENDING_DECOMMISSION):
                self.fc_info_frame.pack(side="top", fill="x")

            if config.docking_access == _FCDockingAccess.ALL:
                self.access_warning_label.pack(side="top", anchor="w")

            if config.status == _FCStatus.PENDING_DECOMMISSION:
                self.decom_warning_label.pack(side="top", anchor="w")
        
        self.grid(column=0, row=row, sticky="NWSE")


    def get_current_config(self) -> tuple[bool, _FCClass, str, str]:
        disable_access_warnings = self.disable_access_warnings_var.get()
        variant                 = self.fc_info_frame.class_var.get()
        role                    = self.fc_info_frame.role_var.get()
        comment                 = self.fc_info_frame.comment_var.get()
        return disable_access_warnings, variant, role, comment



class _FCModuleStatusFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, row: int,
                 missing_info_cancel_callback: Callable,
                 save_changes_callback: Callable[[_FCConfig], Any]):
        super().__init__(parent)
        self.row = row
        self.missing_info_cancel_callback = missing_info_cancel_callback
        self.save_changes_callback = save_changes_callback

        # варианты
        # 1: у нас нет информации по флитаку
        self.missing_info_label = tk.Label(self, text=_translate("<FC_TRACKER_MISSING_INFO_TEXT>"), wraplength=400, justify="left")
        self.missing_info_cancel_button = nb.Button(self, text=_translate("I don't have a fleet carrier"), command=self.missing_info_cancel_callback)

        # 2: игрок купил флитак, и мы просим зайти в его панель
        self.carrier_bought_label = tk.Label(self, text=_translate("<FC_CARRIER_BOUGHT_TEXT>"), wraplength=400, justify="left")
        
        # 3: мы обнаружили, что у нас недостаточно информации о флитаке
        self.info_incomplete_label = tk.Label(self, text=_translate("<FC_CARRIER_INFO_INCOMPLETE_TEXT>"), wraplength=400, justify="left")

        # 4: после 2 и 3 - мы получили инфу и предлагаем пользователю её проверить и дополнить
        # фрейм с инфой по флитаку замаппим в соответствующем методе (нам нужен актуальный конфиг)
        self.finish_configuring_fc_info_frame: _FCInfoFrame | None = None
        self.finish_configuring_confirm_changes_button = nb.Button(self, text=_translate("Save"), command=self.__confirm_changes)
    

    def show_missing_info_screen(self):
        self.clear()
        self.missing_info_label.pack(side="top", fill="both")
        self.missing_info_cancel_button.pack(side="top", fill="x")

    def show_carrier_bought_screen(self):
        self.clear()
        self.carrier_bought_label.pack(side="top", fill="both")

    def show_info_incomplete_screen(self):
        self.clear()
        self.info_incomplete_label.pack(side="top", fill="both")

    def show_finish_configuring_screen(self, config_copy: _FCConfig):
        self.clear()
        self.fc_config = config_copy
        self.finish_configuring_fc_info_frame = _FCInfoFrame(self, self.fc_config)
        self.finish_configuring_fc_info_frame.pack(side="top", fill="both")
        self.finish_configuring_confirm_changes_button.pack(side="top", fill="x")

    def __confirm_changes(self):
        self.fc_config.variant  = self.finish_configuring_fc_info_frame.class_var.get()
        self.fc_config.role     = self.finish_configuring_fc_info_frame.role_var.get()
        self.fc_config.comment  = self.finish_configuring_fc_info_frame.comment_var.get()
        self.after(0, self.save_changes_callback, deepcopy(self.fc_config))

        self.finish_configuring_fc_info_frame.destroy()
        self.finish_configuring_fc_info_frame = None
        self.clear()
        del self.fc_config

    def clear(self):
        for widget in self.winfo_children():
            widget.pack_forget()
        
    def show(self):
        self.grid(column=0, row=self.row, sticky="NWSE")
    
    def hide(self):
        self.clear()
        self.grid_forget()

    @property
    def is_shown(self) -> bool:
        return self.winfo_ismapped()



class FC_Tracker(Module):
    """Модуль для отслеживания информации по флитакам: название, код, привязка к fleetcarrier.space и др."""

    FC_CONFIG_KEY = "FCTracker.fc_config"
    WARNINGS_CONFIG_KEY = "FCTracker.access_warnings_disabled"

    def __init__(self, parent: tk.Misc, row: int):
        self.__ui_frame = _FCModuleStatusFrame(parent, row, self.__ui_cancel_callback, self.__ui_save_callback)

        self.access_warnings_disabled = plugin_config.get_bool(self.WARNINGS_CONFIG_KEY)
        if self.access_warnings_disabled is None:
            self.access_warnings_disabled = False
            plugin_config.set(self.WARNINGS_CONFIG_KEY, False)
        debug(f"[FC_Tracker] Docking access warnings are {'disabled' if self.access_warnings_disabled else 'enabled'}.")

        self.__saved_fc_config = self._load_fc_config()
        self.fc_config = deepcopy(self.__saved_fc_config)

        if self.fc_config.status == _FCStatus.UNKNOWN:
            self.__ui_frame.after(0, self.__ui_frame.show)
            self.__ui_frame.after(0, self.__ui_frame.show_missing_info_screen)
        
        elif (
            self.fc_config.status == _FCStatus.PENDING_DECOMMISSION
            and self.fc_config.decommission_timestamp is not None
            and datetime.now(UTC) > self.fc_config.decommission_timestamp
        ):
            debug(
                "[FC_Tracker] Fleet carrier was pending decommission (saved timestamp {}), resetting the config.",
                datetime.isoformat(self.fc_config.decommission_timestamp)
            )
            cmdr = self.fc_config.cmdr
            callsign = self.fc_config.callsign
            self.fc_config = _FCConfig(cmdr=cmdr, callsign=callsign, status=_FCStatus.DECOMMISSIONED)
            self._save_fc_config()
            debug("[FC_Tracker] Notifying the user.")
            global_context.notifier.send(_translate("Your fleet carrier configuration has been reset due to its decommissioning."))
        
        self._check_docking_access()

    
    def on_journal_entry(self, journalEntry: JournalEntry):
        event = journalEntry.data["event"]
        match event:
            case "CarrierBuy": self.carrier_bought(journalEntry)
            case "CarrierStats": self.carrier_stats(journalEntry)
            case "CarrierDecommission": self.decommission_planned(journalEntry)
            case "CarrierCancelDecommission": self.decommission_canceled(journalEntry)
            case "CarrierDockingPermission": self.docking_access_changed(journalEntry)
            case "CarrierNameChanged": self.name_changed(journalEntry)

        if journalEntry.cmdr != self.fc_config.cmdr and journalEntry.cmdr is not None:
            self.fc_config.cmdr = journalEntry.cmdr
            debug("[FC_Tracker] Saved CMDR changed to {}.", self.fc_config.cmdr)
    

    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        if cmdr is not None and cmdr != self.fc_config.cmdr:
            self.fc_config.cmdr = cmdr
            debug("[FC_Tracker] Saved CMDR changed to {}.", self.fc_config.cmdr)
        self.__settings_frame = _SettingsFrame(parent_widget, row, deepcopy(self.fc_config), self.access_warnings_disabled)
    

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        disable_warnings, variant, role, comment = self.__settings_frame.get_current_config()

        self.access_warnings_disabled = disable_warnings
        plugin_config.set(self.WARNINGS_CONFIG_KEY, self.access_warnings_disabled)

        self.fc_config.variant  = variant
        self.fc_config.role     = role
        self.fc_config.comment  = comment
        if cmdr is not None and cmdr != self.fc_config.cmdr:
            self.fc_config.cmdr = cmdr
            debug("[FC_Tracker] Saved CMDR changed to {}.", self.fc_config.cmdr)

        self._save_fc_config()
        self._check_docking_access()
    

    def carrier_bought(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierBuy.")
        self.fc_config = _FCConfig()
        self.fc_config.cmdr = journalEntry.cmdr
        self.fc_config.status = _FCStatus.ACTIVE
        self.fc_config.callsign = journalEntry.data["Callsign"]
        self.fc_config.variant = _FCClass.DRAKE
        self.__ui_frame.after(0, self.__ui_frame.show)
        self.__ui_frame.after(0, self.__ui_frame.show_carrier_bought_screen)
        self._save_fc_config()


    def carrier_stats(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierStats.")
        entry = journalEntry.data

        self.fc_config.callsign = entry["Callsign"]
        self.fc_config.name = entry["Name"]
        self.fc_config.docking_access = entry["DockingAccess"]
        self.fc_config.notorious_access = entry["AllowNotorious"]

        old_status = self.fc_config.status

        if entry["PendingDecommission"] == False:
            self.fc_config.status = _FCStatus.ACTIVE
            self.fc_config.decommission_timestamp = None
        else:
            self.fc_config.status = _FCStatus.PENDING_DECOMMISSION
            if self.fc_config.decommission_timestamp is None:
                # CarrierStats не даёт timestamp списания флитака - посчитаем его сами
                # предположительно это ближайший четверг, 07:00 UTC, но требуются дополнительные проверки
                # например, я не уверен, что произойдёт, если запросить списание за ~24 часа до чт7:00
                timestamp = int(datetime.timestamp(datetime.fromisoformat(entry["timestamp"])))
                timestamp -= 25200                  # отнимаем 7 часов, выравнивая с unix epoch (полночь четверга)
                timestamp += 604800                 # добавляем неделю, чтобы найти ближайший четверг в этом промежутке
                timestamp -= timestamp % 604800     # находим его
                timestamp += 25200                  # добавляем обратно 7 часов
                self.fc_config.decommission_timestamp = datetime.fromtimestamp(timestamp)
                debug(
                    "[FC_Tracker] The carrier was pending decommission, calculated timestamp: {}.",
                    datetime.isoformat(self.fc_config.decommission_timestamp)
                )
        
        if old_status in (_FCStatus.UNKNOWN, _FCStatus.NOT_BOUGHT, _FCStatus.DECOMMISSIONED):
            # дадим юзеру дополнить инфу
            self.__ui_frame.after(0, self.__ui_frame.show_finish_configuring_screen, deepcopy(self.fc_config))
        
        self._save_fc_config()
        self._check_docking_access()


    def decommission_planned(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierDecommission.")
        self.fc_config.status = _FCStatus.PENDING_DECOMMISSION
        self.fc_config.decommission_timestamp = datetime.fromtimestamp(journalEntry.data["ScrapTime"], UTC)
        self._save_fc_config()


    def decommission_canceled(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierCancelDecommission.")
        self.fc_config.status = _FCStatus.ACTIVE
        self.fc_config.decommission_timestamp = None
        self._save_fc_config()


    def docking_access_changed(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierDockingPermission.")
        if self.fc_config.status in (_FCStatus.NOT_BOUGHT, _FCStatus.DECOMMISSIONED):
            self.fc_config.status = _FCStatus.UNKNOWN      # may be pending decommission
        self.fc_config.docking_access = journalEntry.data["DockingAccess"]
        self.fc_config.notorious_access = journalEntry.data["AllowNotorious"]
        self._save_fc_config()
        self._check_docking_access()


    def name_changed(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierNameChanged.")
        if self.fc_config.status in (_FCStatus.NOT_BOUGHT, _FCStatus.DECOMMISSIONED):
            self.fc_config.status = _FCStatus.UNKNOWN      # may be pending decommission
        self.fc_config.callsign = journalEntry.data["Callsign"]
        self.fc_config.name = journalEntry.data["Name"]
        self._save_fc_config()


    def _load_fc_config(self) -> _FCConfig:
        saved_config = plugin_config.get_str(self.FC_CONFIG_KEY)
        if saved_config:
            debug("[FC_Tracker] Loading saved config.")
            config = json.loads(saved_config)
            if isinstance(config["decommission_timestamp"], str):
                config["decommission_timestamp"] = datetime.fromisoformat(config["decommission_timestamp"])
        else:
            debug("[FC_Tracker] No saved config found, setting the default values.")
            config = {}

        config_instance = _FCConfig(**config)
        debug(f"[FC_Tracker] Loaded config: {config_instance}.")
        return config_instance
    

    def _save_fc_config(self):
        if self.fc_config.is_incomplete():
            self.__ui_frame.after(0, self.__ui_frame.show)
            if self.fc_config.status == _FCStatus.UNKNOWN:
                self.__ui_frame.after(0, self.__ui_frame.show_missing_info_screen)
            else:
                self.__ui_frame.after(0, self.__ui_frame.show_info_incomplete_screen)
        else:
            self.__ui_frame.after(0, self.__ui_frame.hide)

        if self.fc_config != self.__saved_fc_config:
            plugin_config.set(self.FC_CONFIG_KEY, json.dumps(self.fc_config.asjson()))
            self.__saved_fc_config = deepcopy(self.fc_config)
            if (
                not self.fc_config.is_incomplete()
                and not self.fc_config.status == _FCStatus.NOT_BOUGHT
            ):
                self._submit_form()
            debug(f"[FC_Tracker] Saving updated config: {self.fc_config}")

    
    def _check_docking_access(self):
        debug(
            "[FC_Tracker] Docking access: {}, CQID: {}, warning disabled: {}.",
            self.fc_config.docking_access,
            global_context.cmdr_SQID,
            self.access_warnings_disabled
        )
        if (
            self.fc_config.docking_access == _FCDockingAccess.ALL
            # TODO: заменить на нормальную проверку "союзности" по готовности БД
            and global_context.cmdr_SQID == "SCEC"
            and not self.access_warnings_disabled
        ):
            debug("[FC_Tracker] Sending an unsafe docking access warning.")
            global_context.notifier.send(_translate("<FC_TRACKER_UNSAFE_DOCKING_ACCESS_WARNING>"))
    

    def _submit_form(self):
        BasicThread(target=self.__submit_form_in_thread, name="FC_Tracker._submit_form").start()

    def __submit_form_in_thread(self):
        # Проверяем наличие аккаунта на fleetcarrier.space
        # Перенаправляет на /carrier/<callsign> -> найдено. Отдаёт 200 -> такого нема.
        # Если реквестить саму /carrier/<callsign> - отдаст 200 в любом случае. Такие дела.
        url = f"https://fleetcarrier.space/search?term={self.fc_config.callsign}"
        try:
            res = requests.get(url, allow_redirects=False)
        except:
            error("[FC_Tracker] Couldn't check for account on fleetcarrier.space:\n" + traceback.format_exc())
            fc_account_link = "[UNKNOWN]"
        else:
            if res.status_code == 200:
                debug("[FC_Tracker] Account on fleetcarrier.space wan't found.")
                fc_account_link = ""
            elif res.status_code == 302:
                debug("[FC_Tracker] Found account on fleetcarrier.space.")
                fc_account_link = f"https://fleetcarrier.space/carrier/{self.fc_config.callsign}"
            else:
                error(f"[FC_Tracker] Unexpected status code {res.status_code} when checking for account on fleetcarrier.space:\n" + res.text)
                fc_account_link = "[UNKNOWN]"

        decomission_timestamp = datetime.isoformat(self.fc_config.decommission_timestamp) if self.fc_config.decommission_timestamp else ""

        # TODO: перевести с тестовой формы на основную, когда будет готово
        url = "https://docs.google.com/forms/d/e/1FAIpQLSepZDoWnZeD77CvShDw409j7FCmftaEweAFtlkBzpR7eDNniA/formResponse?usp=pp_url"
        params = {
            "entry.1191899309": self.fc_config.cmdr,
            "entry.1759759791": self.fc_config.callsign,
            "entry.307209108":  self.fc_config.name,
            "entry.1813580887": self.fc_config.status,
            "entry.393285798":  self.fc_config.docking_access,
            "entry.1756948762": self.fc_config.notorious_access,
            "entry.982436332":  fc_account_link,
            "entry.601824719":  self.fc_config.variant,
            "entry.544438189":  self.fc_config.role,
            "entry.78144414":   self.fc_config.comment,
            "entry.1361520128": decomission_timestamp
        }
        Reporter(url, params).start()

    
    def __ui_cancel_callback(self):
        # нам сказали, что флитаком не владеют
        cmdr = self.fc_config.cmdr
        self.fc_config = _FCConfig(cmdr=cmdr, status=_FCStatus.NOT_BOUGHT)
        self._save_fc_config()


    def __ui_save_callback(self, new_config: _FCConfig):
        self.fc_config.variant  = new_config.variant
        self.fc_config.role     = new_config.role
        self.fc_config.comment  = new_config.comment
        self._save_fc_config()