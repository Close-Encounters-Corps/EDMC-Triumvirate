from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from semantic_version import Version
from typing import Protocol, TYPE_CHECKING

# АХТУНГ: ничто из того, что здесь импортируется, не должно использовать начальные параметры контекста!
# См. load.py -> Updater.__use_local_version
import settings
from modules.lib.module import get_active_modules

if TYPE_CHECKING:
    # им можно, они тут для аннотаций типов и в рантайме не импортируются
    import logging
    from queue import Queue
    from journal_processor import JournalProcessor
    from modules.lib.module import Module
    from modules.notifier import Notifier
    from modules.bgs import BGS
    from modules.canonn_api import CanonnRealtimeAPI
    from modules.colonisation import DeliveryTracker
    from modules.fc_tracker import FC_Tracker
    from modules.systems import SystemsModule
    from modules.squadron import Squadron_Tracker
    from modules.patrol import PatrolModule
    from modules.exploring.visualizer import Visualizer
    from modules.exploring.canonn_codex_poi import CanonnCodexPOI


class TranslateFunc(Protocol):
    def __call__(self, x: str, filepath: str, lang: str = None) -> str:
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
class PluginContext:
    """
    Хранит параметры плагина и ссылки на его компоненты.
    """
    # параметры
    plugin_name: str                = "EDMC-Triumvirate"
    plugin_version: Version         = Version(settings.version)
    client_version: str             = f"{plugin_name}.{plugin_version}"
    edmc_version: Version           = None
    plugin_dir: str                 = None

    # объекты
    logger: 'logging.Logger'        = None
    _event_queue: 'Queue'           = None
    _tr_template: TranslateFunc     = None
    journal_processor: 'JournalProcessor'   = None
    notifier: 'Notifier'            = None

    # модули
    bgs_module: 'BGS'               = None
    canonn_api: 'CanonnRealtimeAPI' = None
    canonn_codex_poi: 'CanonnCodexPOI'  = None
    sq_tracker: 'Squadron_Tracker'  = None
    fc_tracker: 'FC_Tracker'        = None
    colonisation_tracker: 'DeliveryTracker' = None
    friendfoe                       = None      # TODO: оживить
    systems_module: 'SystemsModule' = None
    patrol_module: 'PatrolModule'   = None
    exp_visualizer: 'Visualizer'    = None

    @_ClassProperty
    def active_modules(cls) -> list['Module']:
        return get_active_modules()


@dataclass
class GameState:
    """
    Хранит текущее состояние игры, включая полную репрезентацию status.json.
    """
    # параметры
    cmdr: str                   = None
    squadron: str               = None
    legacy_sqid: str            = None

    odyssey: bool               = None
    game_in_beta: bool          = None
    pips: list[int, int, int]   = None
    firegroup: int              = None
    gui_focus: 'GuiFocus'       = None
    fuel_main: float            = None
    fuel_reservoir: float       = None
    cargo: int                  = None
    legal_state: 'LegalState'   = None
    balance: int                = None
    destination: str            = None

    system: str                 = None
    system_address: int         = None
    pending_jump_system: str    = None
    station: str                = None
    body_name: str              = None
    latitude: float             = None
    longitude: float            = None
    altitude: int               = None
    heading: int                = None
    planet_radius: float        = None

    # пешие параметры
    oxygen: float               = None      # (0.0 .. 1.0)
    health: float               = None      # (0.0 .. 1.0)
    temperature: int            = None      # в кельвинах
    selected_weapon: str        = None
    gravity: float              = None

    # флаги
    flags_raw: int              = None
    flags2_raw: int             = None
    in_ship: bool               = None
    in_fighter: bool            = None
    in_srv: bool                = None
    on_foot: bool               = None


# вспомогательные классы

class LegalState(str, Enum):
    CLEAN               = "Clean"
    ILLEGAL_CARGO       = "IllegalCargo"
    SPEEDING            = "Speeding"
    WANTED              = "Wanted"
    HOSTILE             = "Hostile"
    PASSENGER_WANTED    = "PassengerWanted"
    WARRANT             = "Warrant"


class GuiFocus(int, Enum):
    NO_FOCUS            = 0
    INTERNAL_PANEL      = 1     # левая панель
    EXTERNAL_PANEL      = 2     # правая панель
    COMMS_PANEL         = 3
    ROLE_PANEL          = 4
    STATION_SERVICES    = 5
    GALAXY_MAP          = 6
    SYSTEM_MAP          = 7
    ORRERY              = 8
    FSS_MODE            = 9
    SAA_MODE            = 10
    CODEX               = 11


class Flags(IntFlag):
    DOCKED                  = auto()
    LANDED                  = auto()
    LANDING_GEAR_DOWN       = auto()
    SHIELDS_UP              = auto()
    SUPERCRUISE             = auto()
    FLIGHT_ASSIST_OFF       = auto()
    HARDPOINTS_DEPLOYED     = auto()
    IN_WING                 = auto()
    LIGHTS_ON               = auto()
    CARGO_SCOOP_DEPLOYED    = auto()
    SILENT_RUNNING          = auto()
    SCOOPING_FUEL           = auto()
    SRV_HANDBRAKE           = auto()
    SRV_TURRET_VIEW         = auto()
    SRV_TURRET_RETRACKED    = auto()
    SRV_DRIVE_ASSIST        = auto()
    FSD_MASS_LOCKED         = auto()
    FSD_CHARGING            = auto()
    FSD_COOLDOWN            = auto()
    LOW_FUEL                = auto()    # <25%
    OVERHEATING             = auto()    # >100%
    HAS_LAT_LONG            = auto()
    IS_IN_DANGER            = auto()
    BEING_INTERDICTED       = auto()
    IN_MAIN_SHIP            = auto()
    IN_FIGHTER              = auto()
    IN_SRV                  = auto()
    HUD_IN_ANALYSIS_MODE    = auto()
    NIGHT_VISION            = auto()
    ALT_FROM_AVERAGE_RADIUS = auto()
    FSD_JUMP                = auto()
    SRV_HIGH_BEAM           = auto()


class Flags2(IntFlag):
    ON_FOOT                 = auto()
    IN_TAXI                 = auto()    # или в десантном шаттле
    IN_MULTICREW            = auto()    # т.е. в чужом корабле
    ON_FOOT_IN_STATION      = auto()
    ON_FOOT_ON_PLANET       = auto()
    AIM_DOWN_SIGHT          = auto()
    LOW_OXYGEN              = auto()
    LOW_HEALTH              = auto()
    COLD                    = auto()
    HOT                     = auto()
    VERY_COLD               = auto()
    VERY_HOT                = auto()
    GLIDE_MODE              = auto()
    ON_FOOT_IN_HANGAR       = auto()
    ON_FOOT_SOCIAL_SPACE    = auto()
    ON_FOOT_EXTERIOR        = auto()
    BREATHABLE_ATMOSPHERE   = auto()
    TELEPRESENCE_MULTICREW  = auto()
    PHYSICAL_MULTICREW      = auto()
    FSD_HYPERDRIVE_CHARGING = auto()
