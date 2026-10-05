import logging
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from semantic_version import Version
from typing import TYPE_CHECKING, Protocol

# АХТУНГ: ничто из того, что здесь импортируется, не должно использовать начальные параметры контекста!
# См. load.py -> Updater.__use_local_version
from Triumvirate.lib.journal import Coords
from Triumvirate.lib.module import get_active_modules


if TYPE_CHECKING:
    from Triumvirate.core.journal_processor import JournalProcessor
    from Triumvirate.core.notifier import Notifier
    from Triumvirate.core.sound_player import SoundPlayer
    from Triumvirate.core.systems import SystemsCache
    from Triumvirate.lib.module import Module
    from Triumvirate.modules.bgs import BGS
    from Triumvirate.modules.canonn_api import CanonnRealtimeAPI
    from Triumvirate.modules.codex.providers.canonn_poi import CanonnPOI
    from Triumvirate.modules.codex.ui import CodexUI
    from Triumvirate.modules.colonisation import DeliveryTracker
    from Triumvirate.modules.fc_tracker import FC_Tracker
    from Triumvirate.modules.patrol import PatrolModule
    from Triumvirate.modules.squadron import SquadronTracker


class TranslateFunc(Protocol):
    def __call__(self, x: str, filepath: str, lang: str | None = None) -> str:
        """
        :param x: Ключ перевода
        :param filepath: Путь к файлу (__file__), в котором вызывается функция
        :param optional lang: Позволяет явно указать, для какого языка будет взят перевод
        """
        ...


class _ClassProperty:
    """
    Заменяет связку @classmethod и @property (depricated в Python 3.11).
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return self.func(owner)


@dataclass
class _PluginPaths:
    _loader_dir: Path
    plugin_dir: Path
    assets_dir: Path
    userdata_dir: Path


@dataclass
class PluginContext:
    """
    Хранит параметры плагина и ссылки на его компоненты.
    """
    # начальные параметры
    plugin_name: str
    plugin_version: Version
    user_agent: str
    edmc_version: Version
    paths: _PluginPaths
    logger: logging.Logger
    _tr_template: TranslateFunc

    # объекты ядра
    journal_processor: 'JournalProcessor'
    notifier: 'Notifier'
    sound_player: 'SoundPlayer'
    systems_cache: 'SystemsCache'

    # модули
    bgs_module: 'BGS'
    canonn_api: 'CanonnRealtimeAPI'
    codex_ui: 'CodexUI'
    codex_canonn_poi: 'CanonnPOI'
    sq_tracker: 'SquadronTracker'
    fc_tracker: 'FC_Tracker'
    colonisation_tracker: 'DeliveryTracker'
    patrol_module: 'PatrolModule'

    @_ClassProperty
    def active_modules(cls) -> list['Module']:
        return get_active_modules()


# вспомогательные классы

class LegalState(StrEnum):
    CLEAN               = "Clean"
    ILLEGAL_CARGO       = "IllegalCargo"
    SPEEDING            = "Speeding"
    WANTED              = "Wanted"
    HOSTILE             = "Hostile"
    PASSENGER_WANTED    = "PassengerWanted"
    WARRANT             = "Warrant"


class GuiFocus(IntEnum):
    NO_FOCUS            = 0
    INTERNAL_PANEL      = 1  # левая панель
    EXTERNAL_PANEL      = 2  # правая панель
    COMMS_PANEL         = 3
    ROLE_PANEL          = 4
    STATION_SERVICES    = 5
    GALAXY_MAP          = 6
    SYSTEM_MAP          = 7
    ORRERY              = 8
    FSS_MODE            = 9
    SAA_MODE            = 10
    CODEX               = 11


class _FlagsBase:
    def __init__(self):
        self._raw = 0

    def update(self, val: int):
        self._raw = val


class _Flag:
    def __init__(self, value):
        self.value = value

    def __get__(self, instance, owner):
        if instance is None:
            return self.value
        return bool(instance._raw & self.value)


class Flags(_FlagsBase):
    DOCKED                  = _Flag(1 << 0)
    LANDED                  = _Flag(1 << 1)
    LANDING_GEAR_DOWN       = _Flag(1 << 2)
    SHIELDS_UP              = _Flag(1 << 3)
    SUPERCRUISE             = _Flag(1 << 4)
    FLIGHT_ASSIST_OFF       = _Flag(1 << 5)
    HARDPOINTS_DEPLOYED     = _Flag(1 << 6)
    IN_WING                 = _Flag(1 << 7)
    LIGHTS_ON               = _Flag(1 << 8)
    CARGO_SCOOP_DEPLOYED    = _Flag(1 << 9)
    SILENT_RUNNING          = _Flag(1 << 10)
    SCOOPING_FUEL           = _Flag(1 << 11)
    SRV_HANDBRAKE           = _Flag(1 << 12)
    SRV_TURRET_VIEW         = _Flag(1 << 13)
    SRV_TURRET_RETRACKED    = _Flag(1 << 14)
    SRV_DRIVE_ASSIST        = _Flag(1 << 15)
    FSD_MASS_LOCKED         = _Flag(1 << 16)
    FSD_CHARGING            = _Flag(1 << 17)
    FSD_COOLDOWN            = _Flag(1 << 18)
    LOW_FUEL                = _Flag(1 << 19)  # <25%
    OVERHEATING             = _Flag(1 << 20)  # >100%
    HAS_LAT_LONG            = _Flag(1 << 21)
    IS_IN_DANGER            = _Flag(1 << 22)
    BEING_INTERDICTED       = _Flag(1 << 23)
    IN_MAIN_SHIP            = _Flag(1 << 24)
    IN_FIGHTER              = _Flag(1 << 25)
    IN_SRV                  = _Flag(1 << 26)  # или в SLV, то есть Nomad-е :brab_fun:
    HUD_IN_ANALYSIS_MODE    = _Flag(1 << 27)
    NIGHT_VISION            = _Flag(1 << 28)
    ALT_FROM_AVERAGE_RADIUS = _Flag(1 << 29)
    FSD_JUMP                = _Flag(1 << 30)
    SRV_HIGH_BEAM           = _Flag(1 << 31)


class Flags2(_FlagsBase):
    ON_FOOT                 = _Flag(1 << 0)
    IN_TAXI                 = _Flag(1 << 1)  # или в десантном шаттле
    IN_MULTICREW            = _Flag(1 << 2)  # т.е. в чужом корабле
    ON_FOOT_IN_STATION      = _Flag(1 << 3)
    ON_FOOT_ON_PLANET       = _Flag(1 << 4)
    AIM_DOWN_SIGHT          = _Flag(1 << 5)
    LOW_OXYGEN              = _Flag(1 << 6)
    LOW_HEALTH              = _Flag(1 << 7)
    COLD                    = _Flag(1 << 8)
    HOT                     = _Flag(1 << 9)
    VERY_COLD               = _Flag(1 << 10)
    VERY_HOT                = _Flag(1 << 11)
    GLIDE_MODE              = _Flag(1 << 12)
    ON_FOOT_IN_HANGAR       = _Flag(1 << 13)
    ON_FOOT_SOCIAL_SPACE    = _Flag(1 << 14)
    ON_FOOT_EXTERIOR        = _Flag(1 << 15)
    BREATHABLE_ATMOSPHERE   = _Flag(1 << 16)
    TELEPRESENCE_MULTICREW  = _Flag(1 << 17)
    PHYSICAL_MULTICREW      = _Flag(1 << 18)
    FSD_HYPERDRIVE_CHARGING = _Flag(1 << 19)
    SUPERCRUISE_OVERCHARGE  = _Flag(1 << 20)
    SUPERCRUISE_ASSIST      = _Flag(1 << 21)
    NPC_CREW_ACTIVE         = _Flag(1 << 22)


class GameMode(StrEnum):
    MainGame = "MainGame"
    Operation = "Operation"
    not_in_game = "[not_in_game]"
    unknown = "[unknown]"


@dataclass
class GameState:
    """
    Хранит текущее состояние игры, включая полную репрезентацию status.json.
    """
    # параметры
    cmdr: str | None            = None
    squadron: str | None        = None
    legacy_sqid: str | None     = None

    odyssey: bool | None                = None
    gamemode: GameMode                  = GameMode.unknown
    game_in_beta: bool | None           = None
    pips: tuple[int, int, int] | None   = None
    firegroup: int | None               = None
    gui_focus: GuiFocus | None          = None
    fuel_main: float | None             = None
    fuel_reservoir: float | None        = None
    cargo: int | None                   = None
    legal_state: LegalState | None      = None
    balance: int | None                 = None
    destination: str | None             = None

    system: str | None                  = None
    system_address: int | None          = None
    system_coords: Coords | None        = None
    pending_jump_system: str | None     = None
    pending_jump_system_id: int | None  = None
    station: str | None                 = None
    body_name: str | None               = None
    latitude: float | None              = None
    longitude: float | None             = None
    altitude: int | None                = None
    heading: int | None                 = None
    planet_radius: float | None         = None

    # пешие параметры
    oxygen: float | None        = None  # (0.0 .. 1.0)
    health: float | None        = None  # (0.0 .. 1.0)
    temperature: int | None     = None  # в кельвинах
    selected_weapon: str | None = None
    gravity: float | None       = None

    # флаги
    flags = Flags()
    flags2 = Flags2()
