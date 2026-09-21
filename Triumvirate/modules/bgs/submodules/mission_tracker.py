from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from Triumvirate.core.context import GameState, PluginContext
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module
from Triumvirate.modules.bgs.submodules.base import BGSSubmodule
from Triumvirate.modules.legacy import URL_GOOGLE


class MissionStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


@dataclass
class Mission:
    # ОБЯЗАН полностью соответствовать структуре таблицы, т.к. при SELECT используется `Mission(*row)`
    mission_id: int
    cmdr: str
    status: MissionStatus
    mission_type: str
    origin_system: str | None = None
    origin_system_id: int | None = None
    origin_faction: str | None = None
    timestamp_accepted: str | None = None
    timestamp_expires: str | None = None
    timestamp_finished: str | None = None


class MissionTracker(Module, BGSSubmodule):
    @property
    def localized_name(self) -> str:
        return _translate("Missions tracker")


    def __init__(self):
        self._closed = False
        self.core.database.execute("""
            CREATE TABLE IF NOT EXISTS missions(
                mission_id INTEGER PRIMARY KEY,
                cmdr TEXT NOT NULL,
                status TEXT NOT NULL,
                mission_type TEXT NOT NULL,
                origin_system TEXT,
                origin_system_id INT,
                origin_faction TEXT,
                timestamp_accepted TEXT,
                timestamp_expires TEXT,
                timestamp_finished TEXT
            )
        """)


    def on_journal_entry(self, entry: JournalEntry):
        raw = entry.data
        match raw["event"]:
            case "Missions": self.on_missions_event(raw)
            case "MissionAccepted": self.mission_accepted(raw)
            case "MissionCompleted": self.mission_completed(raw)
            case "MissionAbandoned": self.mission_abandoned(raw)
            case "MissionFailed": self.mission_failed(raw)


    def on_close(self):
        if self._closed:
            return
        self._closed = True
        self._find_expired_missions()


    def mission_accepted(self, entry: dict):
        mission_id = entry["MissionID"]
        if (GameState.cmdr is None
                or GameState.system is None
                or GameState.system_address is None):
            PluginContext.logger.error(f"Can't process accepted mission {mission_id} - missing cmdr/system info")
            return
        mission_obj = Mission(
            mission_id,
            cmdr=GameState.cmdr,
            timestamp_accepted=entry["timestamp"],
            timestamp_expires=entry.get("Expiry"),
            status=MissionStatus.ACTIVE,
            mission_type=entry["Name"],
            origin_system=GameState.system,
            origin_system_id=GameState.system_address,
            origin_faction=entry["Faction"]
        )
        self._insert_or_update(mission_obj)
        PluginContext.logger.debug(f"Mission {mission_id} accepted and saved to the database.")


    def mission_completed(self, entry: dict):
        mission_id = entry["MissionID"]
        PluginContext.logger.debug(f"Processing completion of mission {mission_id}:")

        res = self._select_by_id(mission_id)
        if res is not None:
            mission_obj = Mission(*res)
            mission_obj.status = MissionStatus.COMPLETED
            mission_obj.timestamp_finished = entry["timestamp"]
        else:
            PluginContext.logger.warning(f"Mission {mission_id} not found in the database.")
            if GameState.cmdr is None:
                PluginContext.logger.error(f"Can't process failed mission {mission_id} - missing cmdr info")
                return
            mission_obj = Mission(
                mission_id=mission_id,
                cmdr=GameState.cmdr,
                status=MissionStatus.COMPLETED,
                mission_type=entry["Name"],
                timestamp_finished=entry["timestamp"],
            )
        self._insert_or_update(mission_obj)

        effects: list[dict] = entry.get("FactionEffects", [])
        if not effects:
            PluginContext.logger.debug(f"Mission {mission_id} doesn't have any faction effects.")
            return
        for faction_data in effects:
            faction = faction_data["Faction"]
            inf_data: list[dict] = faction_data.get("Influence", [])
            if not inf_data:
                PluginContext.logger.warning(f"No influence data for faction {faction}.")
                continue
            for system_data in inf_data:
                sid = system_data["SystemAddress"]
                system = PluginContext.systems_cache.get_system_name(sid)
                if system is None:
                    PluginContext.logger.error(f"Couldn't determine system name for affected sid {sid} of faction {faction}.")
                    continue
                change = len(system_data["Influence"])
                if system_data["Trend"] == "DownBad":
                    change *= -1
                PluginContext.logger.debug(f"Faction {faction} affected in system {system}: influence change {change}.")
                self._send_data(mission_obj, faction, system, change)


    def mission_abandoned(self, entry: dict):
        mission_id = entry["MissionID"]
        PluginContext.logger.debug(f"Mission {mission_id} abandoned.")
        res = self._select_by_id(mission_id)
        if res is None:
            PluginContext.logger.debug(f"Mission {mission_id} not found in the database. Unable to mark as abandoned.")
            return
        mission_obj = Mission(*res)
        mission_obj.timestamp_finished = entry["timestamp"]
        mission_obj.status = MissionStatus.ABANDONED
        self._insert_or_update(mission_obj)


    def mission_failed(self, entry: dict):
        mission_id = entry["MissionID"]
        PluginContext.logger.debug(f"Mission {mission_id} failed.")
        res = self._select_by_id(mission_id)
        if res is None:
            PluginContext.logger.error(f"Mission {mission_id} not found in the database. Unable to determine the affected faction.")
            return
        mission_obj = Mission(*res)
        mission_obj.timestamp_finished = entry["timestamp"]
        mission_obj.status = MissionStatus.FAILED
        self._insert_or_update(mission_obj)
        self._send_data(mission_obj, mission_obj.origin_faction, mission_obj.origin_system, -2)  # pyright: ignore[reportArgumentType]


    def on_missions_event(self, entry: dict):
        cur = self.core.database.cursor()
        current_ts = datetime.fromisoformat(entry["timestamp"])
        active_missions: list[dict] = entry.get("Active", [])
        failed_missions: list[dict] = entry.get("Failed", [])
        PluginContext.logger.debug("Processing 'Missions' event...")

        # 1 - активные миссии, которые есть в ивенте, но отсутствуют в БД
        for mission in active_missions:
            mid = mission["MissionID"]
            # игнорируем миссии на постройку главного порта в колонии
            if "Colonisation_Initial" in mission["Name"]:
                PluginContext.logger.debug(f"Skipping the mission to construct colonisation primary port (id {mid})")
                continue
            cur.execute("SELECT 1 FROM missions WHERE mission_id = ?", (mid,))
            res = cur.fetchone()
            if res is None:
                cur.execute(
                    "INSERT INTO missions (mission_id, cmdr, status, mission_type) VALUES (?,?,?,?)",
                    (mid, GameState.cmdr, MissionStatus.ACTIVE, mission["Name"])
                )
                if (expires_sec := mission["Expires"]) != 0:
                    cur.execute(
                        "UPDATE missions SET timestamp_expires = ? WHERE mission_id = ?",
                        (datetime.isoformat(current_ts + timedelta(seconds=expires_sec)), mid)
                    )
                PluginContext.logger.debug(f"Unknown active mission reported by the game (ID {mid}). Saved to the database.")

        # 2 - проваленные миссии, которые у нас либо отсутствуют, либо всё ещё числятся активными
        for mission in failed_missions:
            mid = mission["MissionID"]
            cur.execute("SELECT status FROM missions WHERE mission_id = ?", (mid,))
            res = cur.fetchone()
            if res is None:
                cur.execute(
                    "INSERT INTO missions (mission_id, cmdr, status, mission_type, timestamp_finished) VALUES (?,?,?,?,?)",
                    (mid, GameState.cmdr, MissionStatus.FAILED, mission["Name"], current_ts.isoformat())
                )
                PluginContext.logger.debug(f"Unknown failed mission reported by the game (ID {mid}). Saved to the database.")
            elif res[0] == MissionStatus.ACTIVE:
                cur.execute(
                    "UPDATE missions SET status = ?, timestamp_finished = ? WHERE mission_id = ?",
                    (MissionStatus.FAILED, current_ts.isoformat(), mid)
                )
                PluginContext.logger.debug(f"Mission {mid} reported as failed. Local record updated.")

        # 3 - миссии, отсутствующие в ивенте, но у нас числющиеся как активные
        cur.execute("SELECT mission_id FROM missions WHERE status = ?", (MissionStatus.ACTIVE,))
        saved_active_ids = {row[0] for row in cur.fetchall()}
        all_event_ids = {m["MissionID"] for m in active_missions} | {m["MissionID"] for m in failed_missions}
        finished_ids = saved_active_ids - all_event_ids
        for mid in finished_ids:
            cur.execute("UPDATE missions SET status = ? WHERE mission_id = ?", (MissionStatus.UNKNOWN, mid))
            PluginContext.logger.debug(
                f"Mission {mid} was considered active but is missing from the event. "
                f"Status set to {MissionStatus.UNKNOWN}."
            )

        self.core.database.commit()
        PluginContext.logger.debug("All changes from 'Missions' event have been saved.")


    def _select_by_id(self, mission_id: int):
        cur = self.core.database.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,))
        res = cur.fetchone()
        return res


    def _insert_or_update(self, mission: Mission):
        self.core.database.execute(f"INSERT OR IGNORE INTO missions (mission_id) VALUES ({mission.mission_id})")
        self.core.database.execute(
            """
            UPDATE missions
            SET
                cmdr = ?,
                status = ?,
                mission_type = ?,
                timestamp_accepted = ?,
                timestamp_expires = ?,
                timestamp_finished = ?,
                origin_system = ?,
                origin_system_id = ?,
                origin_faction = ?
            WHERE mission_id = ?
            """,
            (
                mission.cmdr, mission.status, mission.mission_type, mission.timestamp_accepted, mission.timestamp_expires,
                mission.timestamp_finished, mission.origin_system, mission.origin_system_id, mission.origin_faction,
                mission.mission_id
            )
        )
        self.core.database.commit()


    def _find_expired_missions(self):
        cur = self.core.database.execute(
            "SELECT * FROM missions WHERE status = ? AND timestamp_expires != NULL", (MissionStatus.ACTIVE,)
        )
        results = cur.fetchall()
        now = datetime.now(UTC).replace(microsecond=0)
        for res in results:
            mission_obj = Mission(*res)
            expires = datetime.fromisoformat(mission_obj.timestamp_expires)  # pyright: ignore[reportArgumentType]
            if expires < now:
                mid = mission_obj.mission_id
                self.core.database.execute("UPDATE missions SET status = ? WHERE mission_id = ?", (MissionStatus.UNKNOWN, mid))
                PluginContext.logger.debug(
                    f"Mission {mid} has expired ({mission_obj.timestamp_expires}), status set to {MissionStatus.UNKNOWN}."
                )
        self.core.database.commit()


    def _send_data(self, mission: Mission, faction: str, system: str, inf_change: int):
        url = f'{URL_GOOGLE}/1FAIpQLSdlMUq4bcb4Pb0bUTx9C6eaZL6MZ7Ncq3LgRCTGrJv5yNO2Lw/formResponse'
        params = {
            "entry.1839270329": mission.cmdr,
            "entry.1889332006": mission.mission_type,
            "entry.350771392": mission.status,
            "entry.592164382": system,
            "entry.1812690212": faction,
            "entry.179254259": inf_change,
            "usp": "pp_url",
        }
        self.send_bgs_report(url, params, system)
