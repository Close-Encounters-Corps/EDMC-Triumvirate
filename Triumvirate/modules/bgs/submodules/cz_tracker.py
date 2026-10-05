import functools
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk
from typing import Any, Literal

from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module
from Triumvirate.modules.bgs.submodules.base import BGSSubmodule
from Triumvirate.modules.legacy import URL_GOOGLE


def mainthread(func):
    @functools.wraps(func)
    def wrapper(*args):
        from tkinter import _default_root  # pyright: ignore[reportAttributeAccessIssue]
        _default_root.after(0, func, *args)
    return wrapper


MINIMUM_SPACE_KILLS = 5
MINIMUM_ONFOOT_KILLS = 20


INTENSITY_TRANSLATIONS = {
    "High": _translate("High intensity"),
    "Medium": _translate("Medium intensity"),
    "Low": _translate("Low intensity"),
    "_unknown": _translate("??? intensity")
}


@dataclass
class Conflict:
    cmdr: str
    conflict_type: Literal['Space', 'OnFoot']
    system: str
    intensity: Literal['Low', 'Medium', 'High'] | None = None
    kills: int = 0
    bonds: int = 0
    timestamp_started: datetime | None = None
    timestamp_finished: datetime | None = None
    ally_faction: str | None = None
    enemy_faction: str | None = None
    winner_faction: str | None = None
    on_foot_body: str | None = None
    on_foot_settlement: str | None = None
    on_foot_deaths: int | None = None


class DisplayTimer:
    def __init__(
        self,
        initial_value: int,
        stringvar: tk.StringVar,
        pattern: str,
        format: bool = True,
        increasing: bool = False,
        callback: Callable | None = None,
        *args, **kwargs
    ):
        """
        `pattern` должен иметь плейсхолдер `{val}` - в него будет подставляться значение таймера.

        `format` определяет, будет ли значение таймера форматировано в MM:SS.

        `callback` вызывается при достижении таймером нуля, если `increasing == False`.

        `args` и `kwargs` передаются в callback. При отсутствии оного игнорируются.
        """
        # Обновлять stringvar надо в главном потоке, потому что любимый наш tkinter.
        # Нужен .after. Чтобы не наследствовать таймер от виджета, ибо зачем,
        # воспользуемся костылём с tk._default_root.
        self.__root: tk.Tk = tk._default_root  # pyright: ignore[reportAttributeAccessIssue]

        self.callback = callback
        self.callback_args = args
        self.callback_kwargs = kwargs

        self.step = 1 if increasing else -1
        self.var = stringvar
        self.pattern = pattern
        self.format = format
        self.value = initial_value

        self._running = False
        self._stop = False

    def __tick(self):
        if self._stop:
            return
        if self.step == -1 and self.value == 0:  # защита от increasing=True, initial_value=0
            if self.callback:
                self.callback(*self.callback_args, **self.callback_kwargs)
            return
        self.value += self.step
        value = f"{int(self.value / 60)}:{self.value % 60:02}" if self.format else str(self.value)
        self.var.set(self.pattern.format(val=value))
        self.__root.after(1000, self.__tick)

    @mainthread
    def start(self):
        """
        Запускает таймер.
        """
        if not self._running:
            self._running = True
            value = f"{int(self.value / 60)}:{self.value % 60:02}" if self.format else str(self.value)
            self.var.set(self.pattern.format(val=value))
            self.__root.after(1000, self.__tick)

    @mainthread
    def stop(self):
        """
        Досрочно прерывает выполнение таймера. callback не вызывается.
        """
        self._stop = True


class ConflictInfoFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, row: int):
        super().__init__(parent)
        self.row = row
        self._enabled = True
        self._in_conflict = False

        # прогресс закрытия конфликта
        self.__status_var = tk.StringVar()
        self.status_label = tk.Label(self, textvariable=self.__status_var)

        # секундомер
        self.__time_label_text_var = tk.StringVar()
        self.__time_label_timer: DisplayTimer | None = None
        self.time_label = tk.Label(self, textvariable=self.__time_label_text_var)

        # локация - система или тело (для пеших)
        self.__location_var = tk.StringVar()
        self.location_label = tk.Label(self, textvariable=self.__location_var)

        # напряжённость
        self.__intensity_var = tk.StringVar()
        self.intensity_label = tk.Label(self, textvariable=self.__intensity_var)

        # поселение (для пеших)
        self.__settlement_var = tk.StringVar()
        self.settlement_label = tk.Label(self, textvariable=self.__settlement_var)

        # счётчик ранений (для пеших)
        self.__deaths_counter_var = tk.StringVar()
        self.deaths_counter_label = tk.Label(self, textvariable=self.__deaths_counter_var)

        # плашка "победитель" над союзной фракцией
        self.ally_winner_label = tk.Label(self, text=_translate("Winner"))

        # плашка "победитель" над вражеской фракцией
        self.enemy_winner_label = tk.Label(self, text=_translate("Winner"))

        # союзная фракция
        self.__ally_faction_var = tk.StringVar()
        self.ally_faction_label = tk.Label(self, textvariable=self.__ally_faction_var)

        # счётчик бондов
        self.__bonds_counter_var = tk.StringVar()
        self.bonds_counter_label = tk.Label(self, textvariable=self.__bonds_counter_var)

        # вражеская фракция
        self.__enemy_faction_var = tk.StringVar()
        self.enemy_faction_label = tk.Label(self, textvariable=self.__enemy_faction_var)

        # счётчик убийств
        self.__kills_counter_var = tk.StringVar()
        self.kills_counter_label = tk.Label(self, textvariable=self.__kills_counter_var)

        # неопределённость победителя: выбор левой (союзной) фракции
        self.choose_winner_button_left = ttk.Button(self, text=_translate("Choose"))

        # неопределённость победителя: выбор правой (вражеской) фракции
        self.choose_winner_button_right = ttk.Button(self, text=_translate("Choose"))

        # закрытие окна после завершения кз
        self.__close_button_text_var = tk.StringVar()
        self.__close_button_timer: DisplayTimer | None = None
        self.close_button = ttk.Button(self, textvariable=self.__close_button_text_var, command=self.__close_button_callback)

        # заглушка неизвестных фракций-участников
        self.factions_unknown_label = tk.Label(self, text=_translate("<FACTIONS_UNKNOWN_LABEL_TEXT>"))

        # заглушка неизвестной интенсивности (для пеших)
        self.intensity_unknown_label = tk.Label(self, text=_translate("<INTENSITY_UNKNOWN_LABEL_TEXT>"))

        # плашка о неизвестном победителе (из-за опена)
        self.winner_unknown_label = tk.Label(self, text=_translate("<WINNER_UNKNOWN_LABEL_TEXT>"))


    @mainthread
    def conflict_started(self, conflict: Conflict):
        if self.__close_button_timer:
            self.__close_button_timer.stop()
            self.__close_button_timer = None
        self.__clear()
        self.__status_var.set(_translate("IN CONFLICT"))
        self.__map(self.status_label)
        self.__time_label_timer = DisplayTimer(0, self.__time_label_text_var, "{val}", increasing=True)
        self.__map(self.time_label)
        if conflict.conflict_type == "Space":
            self.__location_var.set(conflict.system)
            self.__map(self.location_label)
            self.__intensity_var.set(INTENSITY_TRANSLATIONS[conflict.intensity or "_unknown"])
            self.__map(self.intensity_label)
            self.__map(self.factions_unknown_label)
        else:
            self.__location_var.set(conflict.on_foot_body)  # pyright: ignore[reportArgumentType]
            self.__map(self.location_label)
            self.__intensity_var.set(INTENSITY_TRANSLATIONS["_unknown"])
            self.__map(self.intensity_label)
            self.__settlement_var.set(conflict.on_foot_settlement)  # pyright: ignore[reportArgumentType]
            self.__map(self.settlement_label)
            self.__deaths_counter_var.set(_translate("{n} deaths").format(n=0))
            self.__map(self.deaths_counter_label)
            self.__map(self.factions_unknown_label)
            self.__map(self.intensity_unknown_label)
        self._in_conflict = True
        if self._enabled:
            self.__show()
        self.__time_label_timer.start()


    @mainthread
    def conflict_updated(self, conflict: Conflict):
        if not self._in_conflict:
            return
        if conflict.intensity:
            self.intensity_unknown_label.grid_forget()
            self.__intensity_var.set(INTENSITY_TRANSLATIONS[conflict.intensity])
            self.__map(self.intensity_label)
        if conflict.conflict_type == "OnFoot":
            self.__deaths_counter_var.set(_translate("{n} deaths").format(n=conflict.on_foot_deaths))
        if conflict.ally_faction and conflict.enemy_faction:
            self.factions_unknown_label.grid_forget()
            self.__ally_faction_var.set(conflict.ally_faction)
            self.__map(self.ally_faction_label)
            self.__enemy_faction_var.set(conflict.enemy_faction)
            self.__map(self.enemy_faction_label)
            self.__bonds_counter_var.set(_translate("{n}cr").format(n=f"{conflict.bonds:,}"))
            self.__map(self.bonds_counter_label)
            self.__kills_counter_var.set(_translate("{n} kills").format(n=conflict.kills))
            self.__map(self.kills_counter_label)


    @mainthread
    def conflict_ended(self, conflict: Conflict):
        if not self._in_conflict:
            return

        self.winner_unknown_label.grid_forget()
        self.choose_winner_button_left.grid_forget()
        self.choose_winner_button_right.grid_forget()
        if self.__time_label_timer:
            self.__time_label_timer.stop()
            self.__time_label_timer = None

        if not conflict.winner_faction:
            self.__status_var.set(_translate("Conflict left early"))
        else:
            self.__status_var.set(_translate("Conflict ended"))
            if conflict.winner_faction == conflict.ally_faction:
                self.__map(self.ally_winner_label)
            elif conflict.winner_faction == conflict.enemy_faction:
                self.__map(self.enemy_winner_label)

        self.__close_button_timer = DisplayTimer(
            initial_value=59,
            stringvar=self.__close_button_text_var,
            pattern=_translate("Close ({val})"),
            format=False,
            callback=self.__close_button_callback
        )
        self.__close_button_timer.start()
        self.__map(self.close_button)
        self._in_conflict = False


    @mainthread
    def conflict_ended_winner_unknown(
        self,
        conflict: Conflict,
        ally_callback: Callable[[Conflict], Any],
        enemy_callback: Callable[[Conflict], Any]
    ):
        if not self._in_conflict:
            return
        if self.__time_label_timer:
            self.__time_label_timer.stop()
            self.__time_label_timer = None
        self.__status_var.set(_translate("Conflict ended"))
        self.__map(self.winner_unknown_label)
        self.choose_winner_button_left.configure(command=lambda: ally_callback(conflict))
        self.choose_winner_button_right.configure(command=lambda: enemy_callback(conflict))
        self.__map(self.choose_winner_button_left)
        self.__map(self.choose_winner_button_right)


    def __map(self, obj: tk.Misc):
        match obj:
            case self.status_label: obj.grid(row=0, column=0, columnspan=2)
            case self.time_label: obj.grid(row=1, column=0, columnspan=2)
            case self.location_label: obj.grid(row=2, column=0)
            case self.intensity_label: obj.grid(row=2, column=1)
            case self.settlement_label: obj.grid(row=3, column=0)
            case self.deaths_counter_label: obj.grid(row=3, column=1)
            case self.factions_unknown_label: obj.grid(row=4, column=0, columnspan=2)
            case self.intensity_unknown_label: obj.grid(row=5, column=0, columnspan=2)
            case self.winner_unknown_label: obj.grid(row=6, column=0, columnspan=2)
            case self.ally_winner_label: obj.grid(row=7, column=0)
            case self.enemy_winner_label: obj.grid(row=7, column=1)
            case self.ally_faction_label: obj.grid(row=8, column=0)
            case self.enemy_faction_label: obj.grid(row=8, column=1)
            case self.bonds_counter_label: obj.grid(row=9, column=0)
            case self.kills_counter_label: obj.grid(row=9, column=1)
            case self.choose_winner_button_left: obj.grid(row=10, column=0)
            case self.choose_winner_button_right: obj.grid(row=10, column=1)
            case self.close_button: obj.grid(row=11, column=0, columnspan=2)
            case _: PluginContext.logger.warning(f"Tried to map unknown object: {obj}")


    def __close_button_callback(self):
        if self.__close_button_timer:
            self.__close_button_timer.stop()
            self.__close_button_timer = None
        self.__clear()
        self.__hide()


    def __clear(self):
        for child in self.winfo_children():
            if not isinstance(child, tk.Toplevel):
                child.grid_forget()
        self.master.update()

    def __show(self):
        self.grid(row=self.row, column=0, sticky="NWSE")

    def __hide(self):
        self.grid_forget()


class CZTracker(Module, BGSSubmodule):
    @property
    def localized_name(self) -> str:
        return _translate("Combat zones tracker")

    def __init__(self, ui_row: int):
        self.__gui = ConflictInfoFrame(self.core.ui_frame, ui_row)
        self.conflict: Conflict | None = None
        self.gamemode: Literal['Open', 'Group', 'Solo'] = 'Open'  # если наверняка не знаем, будем предполагать небезопасный вариант
        self._on_foot_died: bool | None = None


    def on_journal_entry(self, entry: JournalEntry):
        if GameState.gamemode != 'MainGame':
            return
        raw = entry.data
        event = raw["event"]
        match event:
            case "LoadGame": self.gamemode = raw["GameMode"]
            case "SupercruiseDestinationDrop": self.on_supercruise_drop(raw)
            case "ApproachSettlement": self.on_settlement_approached(raw)
            case "DropshipDeploy": self.on_dropship_deploy(raw)
            case "FactionKillBond": self.on_kill(raw)
            case "StartJump": self.end_conflict(raw)
            case "BookDropship" | "BookTaxi": self.on_book_dropship(raw)
            case "Music": self.on_music_event(raw)
            case "Shutdown" | "Died" | "SelfDestruct": self.end_conflict(raw, early=True)


    def on_dashboard_entry(self, cmdr: str, is_beta: bool, entry: dict):
        if GameState.gamemode != 'MainGame':
            return
        if self.conflict is None or self.conflict.conflict_type != "OnFoot":
            return
        if GameState.health == 0.0 and not self._on_foot_died:  # флаг нужен, чтобы только один раз смерть засчитать
            self._on_foot_died = True
            self.conflict.on_foot_deaths += 1  # pyright: ignore[reportOperatorIssue]
            PluginContext.logger.debug(f"Detected in-conflict death ({self.conflict.on_foot_deaths} total).")
            self.__gui.conflict_updated(self.conflict)


    def on_supercruise_drop(self, entry: dict):
        signal: str = entry["Type"]
        if "$Warzone_PointRace" not in signal:
            return
        # "$Warzone_PointRace_High:#index=1;"
        intensity: str = signal.removeprefix("$Warzone_PointRace_").split(":")[0]
        if intensity == "Med":
            intensity = "Medium"
        self.conflict = Conflict(
            cmdr=GameState.cmdr,  # pyright: ignore[reportArgumentType]
            conflict_type='Space',
            system=GameState.system,  # pyright: ignore[reportArgumentType]
            intensity=intensity,  # pyright: ignore[reportArgumentType]
            timestamp_started=datetime.fromisoformat(entry["timestamp"])
        )
        PluginContext.logger.debug(f"Entered space conflict: system: {self.conflict.system}, intensity {self.conflict.intensity}.")
        self.__gui.conflict_started(self.conflict)


    def on_settlement_approached(self, entry: dict):
        if self.conflict is not None:
            return
        if not (
            entry["StationFaction"].get("FactionState", "") in ("War", "CivilWar")
            and "dock" not in entry["StationServices"]
        ):
            return
        self.conflict = Conflict(
            cmdr=GameState.cmdr,  # pyright: ignore[reportArgumentType]
            conflict_type='OnFoot',
            system=GameState.system,  # pyright: ignore[reportArgumentType]
            on_foot_body=entry["BodyName"],
            on_foot_settlement=entry["Name"],
            on_foot_deaths=0
        )
        self._on_foot_died = False
        PluginContext.logger.debug(
            f"Entered on-foot conflict: body {self.conflict.on_foot_body}, settlement {self.conflict.on_foot_settlement}."
        )


    def on_dropship_deploy(self, entry: dict):
        if self.conflict is None:
            return
        self._on_foot_died = False
        if self.conflict.timestamp_started is None:
            self.conflict.timestamp_started = datetime.fromisoformat(entry["timestamp"])
            PluginContext.logger.debug("Conflict started.")
            self.__gui.conflict_started(self.conflict)


    def on_kill(self, entry: dict):
        if self.conflict is None:
            return
        self.conflict.ally_faction = entry["AwardingFaction"]
        self.conflict.enemy_faction = entry["VictimFaction"]
        reward = entry["Reward"]
        self.conflict.bonds += reward
        self.conflict.kills += 1
        PluginContext.logger.debug(
            f"Conflict kill: awarding {self.conflict.ally_faction}, victim {self.conflict.enemy_faction}. "
            f"Bonds: {self.conflict.bonds} (+{reward})."
        )
        if self.conflict.conflict_type == "OnFoot" and not self.conflict.intensity:
            if 1896 <= reward < 4172:
                self.conflict.intensity = "Low"
            elif 11858 <= reward <= 33762:
                self.conflict.intensity = "Medium"
            elif 39642 <= reward <= 87362:
                self.conflict.intensity = "High"
            PluginContext.logger.debug(f"Intensity set to {self.conflict.intensity}.")
        self.__gui.conflict_updated(self.conflict)


    def on_book_dropship(self, entry: dict):
        if self.conflict is None:
            return
        if entry.get("Retreat") is True:
            if GameState.health == 0.0:
                PluginContext.logger.debug("Detected retreat after death, conflict left prematurely.")
                self.end_conflict(entry, early=True)
            else:
                PluginContext.logger.debug("Detected retreat, conflict ended.")
                self.end_conflict(entry)


    def on_music_event(self, entry: dict):
        if self.conflict is None or entry["MusicTrack"] != "MainMenu":
            return
        # в космических это досрочный выход
        # в пеших - возможный релог после завершения
        if self.conflict.conflict_type == "Space":
            PluginContext.logger.debug("Detected exiting to main menu, conflict ended prematurely.")
            self.end_conflict(entry, early=True)
        else:
            PluginContext.logger.debug("Detected exiting to main menu, assuming relog. Conflict ended.")
            self.end_conflict(entry, early=False)


    def end_conflict(self, entry: dict, early: bool = False):
        self._on_foot_died = None
        if self.conflict is None:
            return
        if early:
            self.__gui.conflict_ended(self.conflict)
            self.conflict = None
            return
        if self.conflict.timestamp_started is None:
            PluginContext.logger.error("timestamp_finished was None on conflict end!")
            PluginContext.notifier.display(_translate("Conflict's results couldn't be processed due to an internal error."))
            self.__gui.conflict_ended(self.conflict)
            self.conflict = None
            return

        self.conflict.timestamp_finished = datetime.fromisoformat(entry["timestamp"])
        lasted_for = (self.conflict.timestamp_finished - self.conflict.timestamp_started).seconds
        PluginContext.logger.debug(f"Conflict lasted for {lasted_for} seconds.")

        kills_needed = MINIMUM_SPACE_KILLS if self.conflict.conflict_type == 'Space' else MINIMUM_ONFOOT_KILLS
        if self.conflict.kills < kills_needed:
            # недостаточно убийств - досрочный выход
            PluginContext.logger.debug(f"Not enough kills ({self.conflict.kills}/{kills_needed}). Assuming premature leaving.")
            self.__gui.conflict_ended(self.conflict)
            self.conflict = None
            return

        if self.gamemode == 'Open':
            PluginContext.logger.debug(
                "Game mode is Open or unknown. Can't be sure the ally faction won. Asking the user for confirmation."
            )
            self.__gui.conflict_ended_winner_unknown(
                self.conflict,
                self.__ally_winner_button_callback,
                self.__enemy_winner_button_callback
            )
        else:
            PluginContext.logger.debug(f"Game mode is {self.gamemode}, assuming that the ally faction won.")
            self.conflict.winner_faction = self.conflict.ally_faction
            self.__gui.conflict_ended(self.conflict)
            self._send_conflict_info(self.conflict)
        self.conflict = None


    def _send_conflict_info(self, conflict: Conflict):
        match conflict.intensity:
            case "Low":     weight = 0.25
            case "Medium":  weight = 0.5
            case "High":    weight = 1
            case _:         weight = 0.25
        url = f'{URL_GOOGLE}/1FAIpQLSepTjgu1U8NZXskFbtdCPLuAomLqmkMAYCqk1x0JQG9Btgb9A/formResponse'
        params = {
            "entry.1673815657": conflict.timestamp_started,
            "entry.1896400912": conflict.timestamp_finished,
            "entry.1178049789": conflict.cmdr,
            "entry.721869491": conflict.system,
            # "entry.1671504189": conflict.conflict_type,
            "entry.461250117": conflict.on_foot_settlement,
            "entry.428944810": conflict.intensity,
            "entry.1396326275": str(weight).replace('.', ','),
            "entry.1674382418": conflict.ally_faction,
            "entry.1383403456": conflict.winner_faction,
            "usp": "pp_url"
        }

        # TODO: убрать после перехода на сервер. Фикс для совместимости со старыми данными таблицы
        conflict_type = "Space" if conflict.conflict_type == 'Space' else 'Foot'
        params["entry.1671504189"] = conflict_type

        self.send_bgs_report(url, params, conflict.system)


    def __ally_winner_button_callback(self, conflict: Conflict):
        PluginContext.logger.debug("User stated that the ally faction won.")
        conflict.winner_faction = conflict.ally_faction
        self.__gui.conflict_ended(conflict)
        self._send_conflict_info(conflict)


    def __enemy_winner_button_callback(self, conflict: Conflict):
        PluginContext.logger.debug("User stated that the enemy faction won.")
        conflict.winner_faction = conflict.enemy_faction
        self.__gui.conflict_ended(conflict)
        self._send_conflict_info(conflict)
