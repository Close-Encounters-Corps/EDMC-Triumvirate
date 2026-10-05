import functools
import tkinter as tk
from PIL import Image, ImageTk
from queue import Empty, Queue
from threading import Event, Thread

from config import config as edmc_config  # type: ignore

from Triumvirate.core.context import GameMode, GameState, PluginContext
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.journal import Coords, JournalEntry
from Triumvirate.modules import legacy


def mainthread(func):
    @functools.wraps(func)
    def wrapper(self: tk.Misc, *args):
        self.after(0, func, self, *args)
    return wrapper


class _WarningFrame(tk.Frame):
    warning_icon: ImageTk.PhotoImage

    @classmethod
    def load_icon(cls, scale: int):
        size = int(24 * scale / 100)
        image = Image.open(PluginContext.paths.assets_dir / 'icons' / 'core_warning_128.png').resize((size, size))
        cls.warning_icon = ImageTk.PhotoImage(image)

    def __init__(self, parent: 'JPWarnings', text: str, row: int):
        self.__row = row
        self.__parent = parent
        self.__shown = False
        super().__init__(parent)
        self.grid_columnconfigure(1, weight=1)
        self.__icon_label = tk.Label(self, image=self.warning_icon)
        self.__text_label = tk.Label(self, text=text)
        self.__icon_label.grid(row=0, column=0, pady=2, padx=5, sticky='W')
        self.__text_label.grid(row=0, column=1, pady=2, sticky='E')

    @mainthread
    def show(self):
        if self.__shown:
            return
        self.__shown = True
        self.grid(row=self.__row, column=0, sticky="NWSE")
        self.__parent._on_child_shown()

    @mainthread
    def hide(self):
        if not self.__shown:
            return
        self.__shown = False
        self.grid_remove()
        self.__parent._on_child_hidden()

    def is_shown(self):
        return self.__shown


class JPWarnings(tk.Frame):
    def __init__(self, parent: tk.Misc, row: int):
        super().__init__(parent)
        self.__row = row
        self.__displayed_warnings = 0
        _WarningFrame.load_icon(edmc_config.get_int("ui_scale", default=100))
        self.incomplete_system_data = _WarningFrame(self, _translate("<WARNING_INCOMPLETE_SYSTEM_INFO>"), 0)
        self.operation_gamemode = _WarningFrame(self, _translate("<WARNING_OPERATION_GAMEMODE>"), 1)
        self.unknown_gamemode = _WarningFrame(self, _translate("<WARNING_UNKNOWN_GAMEMODE>"), 2)

    def _on_child_shown(self):
        self.__displayed_warnings += 1
        if self.__displayed_warnings == 1:
            self.grid(column=0, row=self.__row)

    def _on_child_hidden(self):
        self.__displayed_warnings -= 1
        if self.__displayed_warnings == 0:
            self.grid_remove()


# Будем использовать threading.Thread вместо кастомного modules.lib.thread.Thread,
# чтобы избежать остановки обработчика до того, как он закончит разбирать очередь.

class JournalProcessor(Thread):
    def __init__(self, event_queue: Queue[dict], app_frame: tk.Frame, row: int):
        super().__init__(name="Triumvirate journal entry processor")
        self.warnings = JPWarnings(app_frame, row)
        self.queue = event_queue
        self._startup = True
        self._stop = Event()  # флаг остановки потока

        # После выхода Operations фронтиры добавили ивент GameModeChange, который показывает,
        # входит игрок в основную игру или операцию. Однако он прописывается после ивентов Commander и LoadGame,
        # поэтому при получении Commander мы будем класть последующие ивенты во временную очередь до получения GameModeChange,
        # чтобы выставить правильный режим в GameState, и только после этого обработаем накопившиеся ивенты.
        self.awaiting_gamemode = False
        self.gamemode_queue = Queue()


    def set_stop(self):
        self._stop.set()


    def run(self):
        while not (self._stop.is_set() and self.queue.empty()):  # мы хотим обработать очередь ивентов до конца перед выходом
            try:
                entry = self.queue.get(timeout=1)
            except Empty:
                continue
            try:
                self.process_entry(entry)
            except Exception as e:
                PluginContext.logger.error("Uncaught exception in JournalProcessor internals!", exc_info=e)
                # TODO: отправка логов
                # TODO: убрать после тестирования 1.12.0
                PluginContext.notifier.display(
                    (
                        "Неожиданная ошибка при обработке логов! "
                        "Дальнейшая корректная работа плагина не гарантирована - перезапустите EDMC. "
                        "Пожалуйста, сообщите @elcy."
                    ),
                    timeout=0
                )


    def process_entry(self, entry: dict):
        # Здесь в основном расположена логика обработки GameMode, потому что она требует
        # несколько нетривиального подхода, отличного от отслеживания локации, командира
        # и других аспектов игрокого состояния.

        if entry["type"] == "journal_entry":
            data = entry["data"][4]
            event = data["event"]

            if event == "StartUp":
                PluginContext.logger.debug(
                    f"Detected synthesized StartUp event. Gamemode cannot be determined and is set to {GameMode.unknown}."
                )
                GameState.gamemode = GameMode.unknown
                if self.awaiting_gamemode:
                    # На самом деле, никогда не должно произойти, но вдруг...
                    # Раз у нас уже был Commander, значит, баг EDMC? Короче, проигнорим.
                    PluginContext.logger.warning("Unexpected StartUp event while awaiting for GameModeChange.")
                    return
                self.route_entry(entry)
                return

            elif (event in ('Shutdown', 'Died', 'SelfDestruct')
                    or event == "Music" and data["MusicTrack"] == "MainMenu"):
                text = "game" if event == 'Shutdown' else "session"
                PluginContext.logger.debug(f"Detected exit from the {text} ({event} event).")
                if self.awaiting_gamemode:
                    # Реалистично только для для Shutdown, но вдруг (2)
                    PluginContext.logger.warning(
                        f"Unexpected {event} event while awaiting for GameModeChange. "
                        "Processing the remaining queue with unknown gamemode."
                    )
                    self.awaiting_gamemode = False
                    while not self.gamemode_queue.empty():
                        self.route_entry(self.gamemode_queue.get_nowait())
                self.route_entry(entry)
                GameState.gamemode = GameMode.not_in_game
                PluginContext.logger.debug(f"Gamemode set to {GameMode.not_in_game}.")
                return

            elif event == "Commander":
                if self.awaiting_gamemode:
                    PluginContext.logger.warning(
                        "Got Commander event, but `awaiting_gamemode` was already True. "
                        "Processing the old queue with unknown gamemode."
                    )
                    while not self.gamemode_queue.empty():
                        self.route_entry(self.gamemode_queue.get_nowait())
                PluginContext.logger.debug("Got Commander event, delaying journal processing until GameModeChange is received.")
                GameState.gamemode = GameMode.unknown
                self.awaiting_gamemode = True
                self.gamemode_queue.put_nowait(entry)
                return

            elif event == "GameModeChange":
                if not self.awaiting_gamemode:
                    PluginContext.logger.warning("Got GameModeChange event, but `awaiting_gamemode` was False.")
                raw_gm = data["GameMode"]
                match raw_gm:
                    case "MainGame":
                        gm = GameMode.MainGame
                        self.warnings.operation_gamemode.hide()
                        self.warnings.unknown_gamemode.hide()
                    case "Operation":
                        gm = GameMode.Operation
                        self.warnings.operation_gamemode.show()
                    case _:
                        PluginContext.logger.warning(f"Received GameModeChange event with unknown GameMode value: {raw_gm!r}!")
                        gm = GameMode.unknown
                        self.warnings.unknown_gamemode.show()
                GameState.gamemode = gm
                PluginContext.logger.debug(f"Gamemode set to {gm}. Processing the delayed events.")
                self.awaiting_gamemode = False
                while not self.gamemode_queue.empty():
                    self.route_entry(self.gamemode_queue.get_nowait())
                self.route_entry(entry)  # process GameModeChange too
                return

        if self.awaiting_gamemode:
            self.gamemode_queue.put_nowait(entry)
        else:
            self.route_entry(entry)


    def route_entry(self, entry: dict):
        try:
            match entry["type"]:
                case "journal_entry": self.on_journal_entry(*entry["data"])
                case "dashboard_entry": self.on_dashboard_entry(*entry["data"])
                case "cmdr_data": self.on_cmdr_data(*entry["data"])
                case _: raise ValueError(f"unknown entry type: {entry['type']}")
        except Exception as e:
            PluginContext.logger.error(f"Uncaught exception while processing a journal entry:\n{entry}", exc_info=e)


    def on_journal_entry(self, cmdr: str | None, is_beta: bool, system: str | None, station: str | None, entry: dict, state: dict):
        GameState.game_in_beta = is_beta
        GameState.station = station
        GameState.odyssey = state["Odyssey"]

        # ПРОВЕРКА КОМАНДИРА
        new_cmdr = GameState.cmdr
        if entry["event"] == "Commander":
            new_cmdr = entry["Name"]
        elif entry["event"] == "LoadGame":
            new_cmdr = entry["Commander"]
        elif GameState.cmdr is None and cmdr:  # доверимся данным EDMC
            new_cmdr = cmdr

        if new_cmdr != GameState.cmdr:
            if new_cmdr is None:
                PluginContext.logger.debug("CMDR and squadron info are reset to None.")
                GameState.cmdr, GameState.squadron, GameState.legacy_sqid = None, None, None
            else:
                GameState.cmdr = new_cmdr
                PluginContext.logger.debug(f"New CMDR: {GameState.cmdr}. Fetching the squadron.")
                GameState.squadron, GameState.legacy_sqid = legacy.fetch_squadron()
                PluginContext.logger.debug(f"Squadron set to {GameState.squadron}, SQID set to {GameState.legacy_sqid}.")

        # РЕПОРТ ВЕРСИИ ПЛАГИНА ПРИ ЗАПУСКЕ
        if self._startup and GameState.cmdr is not None:
            PluginContext.logger.debug("Reporting the plugin version.")
            legacy.report_version()
            self._startup = False

        # ПРОВЕРКА ЛОКАЦИИ
        system_data = self.update_location(entry, state)
        if None in system_data and not self.warnings.incomplete_system_data.is_shown():
            PluginContext.logger.debug("System data incomplete, showing user warning.")
            self.warnings.incomplete_system_data.show()
        elif None not in system_data and self.warnings.incomplete_system_data.is_shown():
            PluginContext.logger.debug("Hiding incomplete system data warning.")
            self.warnings.incomplete_system_data.hide()
        GameState.system, GameState.system_address, GameState.system_coords = system_data

        if entry["event"] == "NavRoute":
            PluginContext.logger.debug("Processing NavRoute event:")
            route: list[dict] = entry["Route"]
            for item in route:
                system_id, system_name, coords = item["SystemAddress"], item["StarSystem"], Coords(*item["StarPos"])
                PluginContext.systems_cache.add_system(system_id, system_name, coords)
            PluginContext.logger.debug(f"Processed {len(route)} waypoints.")

        # ПЕРЕДАЧА ДАННЫХ МОДУЛЯМ
        # Как видно, после перехода на GameState - JournalEntry как таковой стал не нужен.
        # TODO: отказ от него будет долгим и болезненным, но надо.
        journal_entry = JournalEntry(
            cmdr=GameState.cmdr,
            is_beta=GameState.game_in_beta,
            system=GameState.system,
            systemAddress=GameState.system_address,
            station=GameState.station,
            data=entry,
            state=state,
            coords=GameState.system_coords
        )
        for mod in PluginContext.active_modules:
            try:
                mod.on_journal_entry(journal_entry)
            except Exception as e:
                PluginContext.logger.error(f"Exception in module {mod} while processing a journal entry.", exc_info=e)


    def on_dashboard_entry(self, cmdr: str | None, is_beta: bool, entry: dict):
        GameState.game_in_beta = is_beta

        GameState.pips = entry.get("Pips")
        GameState.firegroup = entry.get("Firegroup")
        GameState.gui_focus = entry.get("GuiFocus")
        GameState.fuel_main = entry.get("Fuel", dict()).get("FuelMain")
        GameState.fuel_reservoir = entry.get("Fuel", dict()).get("FuelReservoir")
        GameState.cargo = entry.get("Cargo")
        GameState.legal_state = entry.get("LegalState")
        GameState.latitude = entry.get("Latitude")
        GameState.longitude = entry.get("Longitude")
        GameState.altitude = entry.get("Altitude")
        GameState.heading = entry.get("Heading")
        GameState.body_name = entry.get("BodyName")
        GameState.planet_radius = entry.get("PlanetRadius")
        GameState.balance = entry.get("Balance")
        GameState.destination = entry.get("Destination")
        GameState.oxygen = entry.get("Oxygen")
        GameState.health = entry.get("Health")
        GameState.selected_weapon = entry.get("SelectedWeapon")
        GameState.temperature = entry.get("Temperature")
        GameState.gravity = entry.get("Gravity")

        if (flags := entry.get("Flags")) is not None:
            GameState.flags.update(flags)
        if (flags2 := entry.get("Flags2")) is not None:
            GameState.flags2.update(flags2)

        for mod in PluginContext.active_modules:
            mod.on_dashboard_entry(cmdr, is_beta, entry)


    def on_cmdr_data(self, data: dict, is_beta: bool):
        GameState.game_in_beta = is_beta
        for mod in PluginContext.active_modules:
            mod.on_cmdr_data(data, is_beta)


    def update_location(self, entry: dict, state: dict) -> tuple[str | None, int | None, Coords | None]:
        # Проверка локации - комплексная тема, тут может быть несколько сценариев.
        # 1) Обычный вход в игру или прыжок
        if entry["event"] in ("Location", "FSDJump", "CarrierJump"):
            system, address, coords = entry["StarSystem"], entry["SystemAddress"], Coords(*entry["StarPos"])
            PluginContext.systems_cache.add_system(system, address, coords)
            GameState.pending_jump_system = None
            GameState.pending_jump_system_id = None
            PluginContext.logger.debug(
                f"Event {entry['event']} detected. Location change: system {system} (id {address}), coords {coords}."
            )
            return system, address, coords

        # 2) Игрок запустил плагин после входа в игру, и у нас ничего нет. Придётся полагаться на данные EDMC
        elif entry["event"] == "StartUp":
            PluginContext.logger.debug("Seems like the game is already running. Using EDMC's location data.")
            system = state.get("SystemName")
            address = state.get("SystemAddress")
            coords = (
                Coords(*state["StarPos"])
                if "StarPos" in state and state["StarPos"] is not None
                else PluginContext.systems_cache.get_system_coords(address) if address is not None
                else None
            )
            PluginContext.logger.debug(f"Location change: system {system} (id {address}), coords {coords}.")
            return system, address, coords

        # 3) Готовящийся прыжок - мы всё ещё в старой системе
        elif entry["event"] == "StartJump" and entry["JumpType"] == "Hyperspace":
            GameState.pending_jump_system = entry.get("StarSystem")
            GameState.pending_jump_system_id = entry.get("SystemAddress")
            PluginContext.logger.debug(
                f"Jump initiated, pending system set to {GameState.pending_jump_system} (id {entry['SystemAddress']})."
            )
            return GameState.system, GameState.system_address, GameState.system_coords

        # 4) Прыжок совершён, но FSD/CarrierJump ещё не было, а данные из новой системы уже пошли
        elif entry["event"] == "FSSSignalDiscovered" and entry["SystemAddress"] != GameState.system_address:
            PluginContext.logger.debug("Detected SystemAddress mismatch in FSSSignalDiscovered event.")
            address = entry["SystemAddress"]
            if address == GameState.pending_jump_system_id:
                system = GameState.pending_jump_system
                coords = PluginContext.systems_cache.get_system_coords(address)
                PluginContext.logger.debug(
                    f"New id ({address}) corresponds with the pending jump. Current system set to {system}."
                )
            else:
                if GameState.system_address is None and GameState.pending_jump_system_id is None:
                    # частный случай (1)+(4): мы только входим в игру, локации не знаем, а сигналы уже получили
                    PluginContext.logger.debug(f"Got system ID {address} from FSSSignalDiscovered.")
                else:
                    # прыгнули не пойми куда??
                    PluginContext.logger.warning(
                        f"Unexpected misjump: new system id ({address}) doesn't match the pending one "
                        f"({GameState.pending_jump_system_id})."
                    )
                system = PluginContext.systems_cache.get_system_name(address)
                coords = PluginContext.systems_cache.get_system_coords(address)
            # pending-и сохраним до ивента прыжка, там сбросим
            return system, address, coords

        # 5) Вход в игру рядом с поселением. ApproachSettlement опережает в логах Location и даже FSSSignalDiscovered
        elif entry["event"] == "ApproachSettlement" and GameState.system_address is None:
            sid: int = entry["SystemAddress"]
            system = PluginContext.systems_cache.get_system_name(sid)
            coords = PluginContext.systems_cache.get_system_coords(sid)
            PluginContext.logger.debug(
                "Detected ApproachSettlement on game startup. "
                f"Got system id {sid}, fetched system name {system}, fetched coords {coords}."
            )
            return system, sid, coords

        # 6) Ещё неизвестные нам случаи, тут только логировать
        elif (
            "SystemAddress" in entry
            and entry["SystemAddress"] != GameState.system_address
            and entry["event"] not in ("NavRoute", "FSDTarget", "CarrierBuy", "CarrierJumpRequest", "CarrierLocation")
        ):
            PluginContext.logger.warning(
                "Unexpected SystemAddress mismatch: "
                f"event {entry['event']}, current {GameState.system_address}, got {entry['SystemAddress']}."
            )
        return GameState.system, GameState.system_address, GameState.system_coords
