from queue import Queue

import settings
from context import PluginContext, GameState, Flags, Flags2
from modules import legacy
from modules.lib.journal import JournalEntry
from modules.lib.thread import Thread


class JournalProcessor(Thread):
    def __init__(self):
        super().__init__(name="Triumvirate journal entry processor")
        self.queue: Queue = PluginContext._event_queue
        self._startup = True


    def do_run(self):
        while True:
            if self.queue.empty():
                self.sleep(1)
                continue
            try:
                entry = self.queue.get(block=False)
                match entry["type"]:
                    case "journal_entry":
                        self.on_journal_entry(*entry["data"])
                    case "dashboard_entry":
                        self.on_dashboard_entry(*entry["data"])
                    case "cmdr_data":
                        self.on_cmdr_data(*entry["data"])
                    case _:
                        raise ValueError("unknown entry type")
            except Exception as e:
                PluginContext.logger.error("Uncatched exception while processing a journal entry.\n%s", str(entry), exc_info=e)
                # TODO: отправка логов


    def on_journal_entry(self, cmdr: str | None, is_beta: bool, system: str | None, station: str | None, entry: dict, state: dict):
        GameState.game_in_beta = is_beta
        GameState.station = station

        new_cmdr = GameState.cmdr
        if entry["event"] == "Commander":
            new_cmdr = entry["Name"]
        elif entry["event"] == "LoadGame":
            new_cmdr = entry["Commander"]
        elif GameState.cmdr is None and cmdr:
            new_cmdr = cmdr

        if new_cmdr != GameState.cmdr:
            GameState.cmdr = new_cmdr
            PluginContext.logger.debug(f"New CMDR: {GameState.cmdr}. Fetching the squadron.")
            GameState.squadron, GameState.legacy_sqid = legacy.fetch_squadron()
            PluginContext.logger.debug(f"Squadron set to {GameState.squadron}, SQID set to {GameState.legacy_sqid}.")

        if self._startup and GameState.cmdr is not None:
            PluginContext.logger.debug("Reporting the plugin version.")
            legacy.report_version()
            self._startup = False

        if GameState.odyssey is None:
            if entry["event"] == "LoadGame":        # ВАЖНО: Fileheader даёт Odyssey=true и в Горизонтах тоже
                GameState.odyssey = entry.get("Odyssey", False)
            # ивенты, возможные лишь в Одиссее
            elif entry["event"] in settings.odyssey_events:
                GameState.odyssey = True

        # иногда FSDJump приходит позже, чем нам хотелось бы, и имеющаяся у нас система не совпадает с реальной
        if (
            "SystemAddress" in entry
            and GameState.system_address != entry["SystemAddress"]
            and entry["event"] not in ("NavRoute", "FSDTarget")
        ):
            PluginContext.logger.debug(
                "Detected SystemAddress mismatch: current {}, from entry {}.".format(
                    GameState.system_address, entry["SystemAddress"]
                ))
            if entry["event"] == "StartJump":
                # мы ещё в актуальной системе, но сохраним ту, в которую прыгаем
                GameState.pending_jump_system = entry.get("StarSystem")
                PluginContext.logger.debug(
                    "StartJump. Pending jump system set to {}, id {}. Raw entry: {!r}".format(
                        GameState.pending_jump_system, entry["SystemAddress"], entry
                    ))
            else:
                # мы уже прыгнули, но FSDJump в логах пока не получили
                GameState.system_address = entry["SystemAddress"]
                GameState.system = GameState.pending_jump_system or system
                PluginContext.logger.debug(
                    "We jumped to another system; system_address set to {}, system set to {}.".format(
                        GameState.system_address, GameState.system
                    ))

        # а ещё нас могут дёрнуть таргоиды, поэтому мы окажемся в той же системе, из которой прыгали.
        if (
            entry.get("event") == "FSDJump"
            and entry["StarSystem"] != GameState.pending_jump_system
        ):
            PluginContext.logger.debug("Detected misjump; are we hyperdicted? Leaving system_address unchanged.")

        if GameState.system != system and system is not None and GameState.pending_jump_system is None:
            PluginContext.logger.debug(
                "GameState.system was {}, but EDMC reported {}. No pending jump detected. Changing system to {}.".format(
                    GameState.system, system, system
                ))
            GameState.system = system

        if entry.get("event") == "FSDJump":
            GameState.body_name = None
            GameState.pending_jump_system = None

        x, y, z = None, None, None
        if GameState.system:
            val = PluginContext.systems_module.get_system_coords(GameState.system)
            if val is not None:
                x, y, z = val

        # Как видно, после перехода на GameState - JournalEntry как таковой стал не нужен.
        # TODO: отказ от него будет долгим и болезненным, но надо.
        journal_entry = JournalEntry(
            cmdr=GameState.cmdr,
            is_beta=GameState.game_in_beta,
            system=GameState.system,
            systemAddress=GameState.system_address,
            station=GameState.station,
            data=entry,
            x=x, y=y, z=z
        )

        if entry["event"] in ('SendText', 'RecieveText'):
            for mod in PluginContext.active_modules:
                try:
                    mod.on_chat_message(journal_entry)
                except Exception as e:
                    PluginContext.logger.error(f"Exception in module {mod} while processing a chat message.", exc_info=e)
        else:
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

        if flags := entry.get("Flags") is not None:
            GameState.flags_raw     = flags
            GameState.in_ship       = flags & Flags.IN_MAIN_SHIP
            GameState.in_fighter    = flags & Flags.IN_FIGHTER
            GameState.in_srv        = flags & Flags.IN_SRV
        if flags2 := entry.get("Flags2") is not None:
            GameState.flags2_raw    = flags2
            GameState.on_foot       = flags2 & Flags2.ON_FOOT


    def on_cmdr_data(self, data: dict, is_beta: bool):
        GameState.game_in_beta = is_beta
        for mod in PluginContext.active_modules:
            mod.on_cmdr_data(data, is_beta)
