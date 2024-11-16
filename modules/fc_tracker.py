import json
import requests
import tkinter as tk
import traceback
from copy import deepcopy
from enum import Enum
from dataclasses import dataclass, asdict as dataclass_asdict
from datetime import datetime, UTC
from tkinter import ttk

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
plugin_tr = functools.partial(l10n.translations.tl, context=__file__)



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
class _FCModuleConfig:
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


class _SettingsFCInfoFrame(tk.Frame):
    def __init__(self, parent, config: _FCModuleConfig):
        super().__init__(parent, bg="white")

        name = "[{}] {}".format(config.callsign, config.name or "???") if config.callsign else plugin_tr("unknown")
        self.name_label     = nb.Label(self, text=plugin_tr("Carrier name:"))
        self.name_field     = nb.Label(self, text=name)
        self.name_label.grid(row=0, column=0, sticky="W")
        self.name_field.grid(row=0, column=1, padx=3, sticky="W")

        self.class_var      = tk.StringVar(value=(config.variant or plugin_tr("unknown")))
        self.class_label    = nb.Label(self, text=plugin_tr("Carrier class:"))
        self.class_field    = ttk.Combobox(
            self,
            values=[e.value for e in _FCClass],
            textvariable=self.class_var,
            state="readonly"
        )
        self.class_label.grid(row=1, column=0, sticky="W")
        self.class_field.grid(row=1, column=1, padx=3, sticky="W")

        self.access_label   = nb.Label(self, text=plugin_tr("Docking access:"))
        self.access_field   = nb.Label(self, text=plugin_tr(config.docking_access))
        self.access_label.grid(row=2, column=0, sticky="W")
        self.access_field.grid(row=2, column=1, padx=3, sticky="W")

        self.notorious_access_label = nb.Label(self, text=plugin_tr("Docking allowed for notorious:"))
        self.notorious_access_field = nb.Label(self, text=plugin_tr(config.notorious_access))
        self.notorious_access_label.grid(row=3, column=0, sticky="W")
        self.notorious_access_field.grid(row=3, column=1, padx=3, sticky="W")

        self.optional_fields_label  = nb.Label(self, text=plugin_tr("<FC_TRACKER_SETTINGS_OPTIONAL_FIELDS>"))
        self.optional_fields_label.grid(row=4, column=0, columnspan=2, sticky="W")

        self.role_var   = tk.StringVar(value=config.role)
        self.role_label = nb.Label(self, text=plugin_tr("Role:"))
        self.role_field = nb.EntryMenu(self, textvariable=self.role_var, width=70)
        self.role_label.grid(row=5, column=0, sticky="W")
        self.role_field.grid(row=5, column=1, padx=3, sticky="W")

        self.comment_var    = tk.StringVar(self, value=config.comment)
        self.comment_label  = nb.Label(self, text=plugin_tr("Additional comment:"))
        self.comment_field  = nb.EntryMenu(self, textvariable=self.comment_var, width=70)
        self.comment_label.grid(row=6, column=0, sticky="W")
        self.comment_field.grid(row=6, column=1, padx=3, sticky="W")


class _SettingsFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, row: int, config: _FCModuleConfig, disable_access_warnings: bool):
        super().__init__(parent, bg="white")
        decom_timestamp = config.decommission_timestamp.strftime("%x %X") if config.decommission_timestamp else ""

        self.module_name_label = nb.Label(self, text=plugin_tr("FC Tracker settings:"))
        self.module_name_label.pack(side="top", anchor="w")

        self.disable_access_warnings_frame = tk.Frame(self, bg="white")
        self.disable_access_warnings_var = tk.BooleanVar(value=disable_access_warnings)
        self.disable_access_warnings_checkbox = nb.Checkbutton(self.disable_access_warnings_frame, variable=self.disable_access_warnings_var)
        self.disable_access_warnings_label = nb.Label(
            self.disable_access_warnings_frame,
            text=plugin_tr("Disable warnings about unsafe docking access configuration")
        )
        self.disable_access_warnings_checkbox.grid(row=0, column=0)
        self.disable_access_warnings_label.grid(row=0, column=1, sticky="W")
        self.disable_access_warnings_frame.pack(side="top", fill="x")

        self.no_fc_label            = nb.Label(self, text=plugin_tr("<FC_TRACKER_SETTINGS_NO_FC_INFO>"))
        self.fc_info_frame          = _SettingsFCInfoFrame(self, config)
        self.info_missing_label     = nb.Label(self, text=plugin_tr("<FC_TRACKER_SETTINGS_INFO_MISSING>"))
        self.access_warning_label   = nb.Label(self, text=plugin_tr("<FC_TRACKER_SETTINGS_ACCESS_WARNING>"))
        self.decom_warning_label    = nb.Label(self, text=plugin_tr("<FC_TRACKER_SETTINGS_DECOM_WARNING> {TS}").format(TS=decom_timestamp))

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


class _Notification(tk.Toplevel):
    def __init__(self, callback):
        super().__init__(tk._default_root)
        self.title(plugin_tr("Fleetcarrier info update"))
        self.protocol("WM_DELETE_WINDOW", self.__nothing)       # запрещаем закрывать окно
        self.callback = callback
        self.missing_info_label = tk.Label(self, text=plugin_tr("<FC_TRACKER_NOTIFICATION_TEXT>"), wraplength=500, justify="left")
        self.missing_info_label.pack(side="top", fill="both")
        self.cancel_button = nb.Button(self, text=plugin_tr("I don't have a fleet carrier"), command=self.callback)
        self.cancel_button.pack(side="bottom", fill="x")
    
    def __nothing(self):
        pass



class FC_Tracker(Module):
    """Модуль для отслеживания информации по флитакам: название, код, привязка к fleetcarrier.space и др."""

    FC_CONFIG_KEY = "FCTracker.fc_config"
    WARNINGS_CONFIG_KEY = "FCTracker.access_warnings_disabled"

    def __init__(self):
        self.__notification: _Notification | None = None

        self.access_warnings_disabled = plugin_config.get_bool(self.WARNINGS_CONFIG_KEY)
        if self.access_warnings_disabled is None:
            self.access_warnings_disabled = False
            plugin_config.set(self.WARNINGS_CONFIG_KEY, False)
        debug(f"[FC_Tracker] Docking access warning disabled: {self.access_warnings_disabled}.")

        self.__saved_fc_config = self._load_fc_config()
        self.fc_config = deepcopy(self.__saved_fc_config)

        if self.fc_config.status == _FCStatus.UNKNOWN:
            tk._default_root.after(0, self.__create_notification)

        if (
            self.fc_config.status == _FCStatus.PENDING_DECOMMISSION
            and self.fc_config.decommission_timestamp is not None
            and datetime.now(UTC) > self.fc_config.decommission_timestamp
        ):
            debug(
                "[FC_Tracker] Fleet carrier was pending decommission (saved timestamp {}), resetting the config.",
                datetime.isoformat(self.fc_config.decommission_timestamp)
            )
            self.fc_config.status                   = _FCStatus.DECOMMISSIONED
            self.fc_config.name                     = None
            self.fc_config.variant                  = None
            self.fc_config.docking_access           = None
            self.fc_config.notorious_access         = None
            self.fc_config.decommission_timestamp   = None
            self.fc_config.role                     = None
            self.fc_config.comment                  = None
            self._save_fc_config()
            debug("[FC_Tracker] Notifying the user.")
            global_context.notifier.send(plugin_tr("Your fleet carrier configuration has been reset due to its decommissioning."))
        
        self._check_docking_access()

    
    def on_journal_entry(self, journalEntry: JournalEntry):
        entry = journalEntry.data
        event = entry["event"]

        match event:
            case "CarrierBuy": self.carrier_bought(journalEntry)
            case "CarrierStats": self.carrier_stats(journalEntry)
            case "CarrierDecommission": self.decommission_planned(journalEntry)
            case "CarrierCancelDecommission": self.decommission_canceled(journalEntry)
            case "CarrierDockingPermission": self.docking_access_changed(journalEntry)
            case "CarrierNameChanged": self.name_changed(journalEntry)

        if not journalEntry.cmdr is None:
            self.fc_config.cmdr = journalEntry.cmdr
    

    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        if cmdr is not None:
            self.fc_config.cmdr = cmdr
        self.__settings_frame = _SettingsFrame(parent_widget, row, deepcopy(self.fc_config), self.access_warnings_disabled)
    

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        disable_warnings, variant, role, comment = self.__settings_frame.get_current_config()

        self.access_warnings_disabled = disable_warnings
        plugin_config.set(self.WARNINGS_CONFIG_KEY, self.access_warnings_disabled)

        self.fc_config.variant  = variant
        self.fc_config.role     = role
        self.fc_config.comment  = comment
        if cmdr is not None:
            self.fc_config.cmdr = cmdr

        self._save_fc_config()
        self._check_docking_access()
    

    def carrier_bought(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierBuy.")
        self.fc_config = _FCModuleConfig()
        self.fc_config.cmdr = journalEntry.cmdr
        self.fc_config.status = _FCStatus.ACTIVE
        self.fc_config.callsign = journalEntry.data["Callsign"]
        self.fc_config.variant = _FCClass.DRAKE
        self._save_fc_config()


    def carrier_stats(self, journalEntry: JournalEntry):
        debug("[FC_Tracker] Detected CarrierStats.")
        entry = journalEntry.data

        self.fc_config.callsign = entry["Callsign"]
        self.fc_config.name = entry["Name"]
        self.fc_config.docking_access = entry["DockingAccess"]
        self.fc_config.notorious_access = entry["AllowNotorious"]

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
        
        if self.fc_config.variant is None:
            self.fc_config.variant = _FCClass.DRAKE
            debug("[FC_Tracker] Assigning the default carrier class (Drake).")
        
        if self.__notification is not None:
            debug("[FC_Tracker] Closing the notification.")
            self.__notification.destroy()
            self.__notification = None
        
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


    def _load_fc_config(self) -> _FCModuleConfig:
        saved_config = plugin_config.get_str(self.FC_CONFIG_KEY)
        if saved_config:
            debug("[FC_Tracker] Loading saved config.")
            config = json.loads(saved_config)
            if isinstance(config["decommission_timestamp"], str):
                config["decommission_timestamp"] = datetime.fromisoformat(config["decommission_timestamp"])
        else:
            debug("[FC_Tracker] No saved config found, setting the default values.")
            config = {}

        config_instance = _FCModuleConfig(**config)
        debug(f"[FC_Tracker] Loaded config: {config_instance}.")
        return config_instance
    

    def _save_fc_config(self):
        if self.fc_config.is_incomplete():
            tk._default_root.after(0, self.__create_notification)

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
            global_context.notifier.send(plugin_tr("<FC_TRACKER_UNSAFE_DOCKING_ACCESS_WARNING>"))
    

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


    def __create_notification(self):
        debug("[FC_Tracker] Creating the notification window.")
        self.__notification = _Notification(self.__notif_cancel_callback)


    def __notif_cancel_callback(self):
        self.__notification.destroy()
        self.__notification = None

        self.fc_config.status                   = _FCStatus.NOT_BOUGHT
        self.fc_config.name                     = None
        self.fc_config.variant                  = None
        self.fc_config.docking_access           = None
        self.fc_config.notorious_access         = None
        self.fc_config.role                     = None
        self.fc_config.comment                  = None
        self.fc_config.decommission_timestamp   = None

        debug("[FC_Tracker] User said they don't own a fleet carrier, resetting the config.")
        self._save_fc_config()