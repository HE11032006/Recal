from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from recal.domain.entities import (
    Opportunity,
    OpportunityStatus,
    OpportunityType,
    RunStatus,
    UserProfile,
    WatchRun,
    WatchSettings,
    WatchState,
)


class SQLiteStore:
    def __init__(self, database_path: str = "recal.db") -> None:
        self.database_path = database_path
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                relevance_score REAL NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS watch_state (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            """
        )
        self.connection.commit()


class SQLiteProfileRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    async def get_default(self) -> UserProfile:
        row = self.store.connection.execute(
            "SELECT payload FROM profiles WHERE id = 'default'"
        ).fetchone()
        if row is None:
            return UserProfile(interests=["software engineering"])
        data = json.loads(row["payload"])
        if isinstance(data.get("watch"), dict):
            data["watch"] = WatchSettings(**data["watch"])
        return UserProfile(**data)

    async def save(self, profile: UserProfile) -> UserProfile:
        payload = json.dumps(asdict(profile))
        self.store.connection.execute(
            "INSERT OR REPLACE INTO profiles (id, payload) VALUES (?, ?)",
            (profile.id, payload),
        )
        self.store.connection.commit()
        return profile


class SQLiteOpportunityRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        min_score: float | None = None,
        status: str | None = None,
        since: datetime | None = None,
    ) -> tuple[Sequence[Opportunity], int]:
        conditions: list[str] = []
        values: list[object] = []
        if min_score is not None:
            conditions.append("relevance_score >= ?")
            values.append(min_score)
        if status is not None:
            conditions.append("status = ?")
            values.append(status)
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        if since is None:
            count = self.store.connection.execute(
                f"SELECT COUNT(*) AS count FROM opportunities{where}", values
            ).fetchone()["count"]
            values.extend([page_size, (page - 1) * page_size])
            rows = self.store.connection.execute(
                f"SELECT payload FROM opportunities{where} ORDER BY relevance_score DESC LIMIT ? OFFSET ?",
                values,
            ).fetchall()
            return [self._deserialize(row["payload"]) for row in rows], count
        # Filtre temporel : verified_at vit dans le payload JSON, on filtre
        # côté Python (table petite, MVP). Un index dédié viendra en prod.
        rows = self.store.connection.execute(
            f"SELECT payload FROM opportunities{where}", values
        ).fetchall()
        items = [self._deserialize(row["payload"]) for row in rows]
        items = [item for item in items if item.verified_at >= since]
        items.sort(key=lambda item: item.relevance_score, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    async def get(self, opportunity_id: str) -> Opportunity | None:
        row = self.store.connection.execute(
            "SELECT payload FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        return None if row is None else self._deserialize(row["payload"])

    async def save_if_new(self, opportunity: Opportunity) -> bool:
        payload = json.dumps(self._serialize(opportunity))
        cursor = self.store.connection.execute(
            "INSERT OR IGNORE INTO opportunities (id, relevance_score, status, payload) VALUES (?, ?, ?, ?)",
            (opportunity.id, opportunity.relevance_score, opportunity.status.value, payload),
        )
        self.store.connection.commit()
        return cursor.rowcount == 1

    async def update(self, opportunity: Opportunity) -> Opportunity:
        payload = json.dumps(self._serialize(opportunity))
        self.store.connection.execute(
            "UPDATE opportunities SET relevance_score = ?, status = ?, payload = ? WHERE id = ?",
            (opportunity.relevance_score, opportunity.status.value, payload, opportunity.id),
        )
        self.store.connection.commit()
        return opportunity

    @staticmethod
    def _serialize(opportunity: Opportunity) -> dict:
        payload = asdict(opportunity)
        payload["type"] = opportunity.type.value
        payload["status"] = opportunity.status.value
        payload["verified_at"] = opportunity.verified_at.isoformat()
        payload["deadline"] = opportunity.deadline.isoformat() if opportunity.deadline else None
        return payload

    @staticmethod
    def _deserialize(payload: str) -> Opportunity:
        data = json.loads(payload)
        data["type"] = OpportunityType(data["type"])
        data["status"] = OpportunityStatus(data["status"])
        data["verified_at"] = datetime.fromisoformat(data["verified_at"])
        data["deadline"] = date.fromisoformat(data["deadline"]) if data["deadline"] else None
        return Opportunity(**data)


class SQLiteRunRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    async def save(self, run: WatchRun) -> WatchRun:
        payload = asdict(run)
        payload["id"] = str(run.id)
        payload["status"] = run.status.value
        payload["created_at"] = run.created_at.isoformat()
        payload["completed_at"] = run.completed_at.isoformat() if run.completed_at else None
        self.store.connection.execute(
            "INSERT OR REPLACE INTO runs (id, status, payload) VALUES (?, ?, ?)",
            (str(run.id), run.status.value, json.dumps(payload)),
        )
        self.store.connection.commit()
        return run

    async def get(self, run_id: str) -> WatchRun | None:
        row = self.store.connection.execute(
            "SELECT payload FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        return None if row is None else self._deserialize(row["payload"])

    async def get_active(self) -> WatchRun | None:
        rows = self.store.connection.execute(
            "SELECT payload FROM runs WHERE status IN ('queued', 'running')"
        ).fetchall()
        active_runs = [self._deserialize(row["payload"]) for row in rows]
        if not active_runs:
            return None
        return max(active_runs, key=lambda run: run.created_at)

    @staticmethod
    def _deserialize(payload: str) -> WatchRun:
        from uuid import UUID

        data = json.loads(payload)
        data["id"] = UUID(data["id"])
        data["status"] = RunStatus(data["status"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["completed_at"] = (
            datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None
        )
        return WatchRun(**data)


class SQLiteWatchStateRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    async def get(self) -> WatchState:
        row = self.store.connection.execute(
            "SELECT payload FROM watch_state WHERE id = 'default'"
        ).fetchone()
        if row is None:
            return WatchState()
        return self._deserialize(row["payload"])

    async def save(self, state: WatchState) -> WatchState:
        payload = json.dumps(self._serialize(state))
        self.store.connection.execute(
            "INSERT OR REPLACE INTO watch_state (id, payload) VALUES ('default', ?)",
            (payload,),
        )
        self.store.connection.commit()
        return state

    @staticmethod
    def _serialize(state: WatchState) -> dict:
        return {
            "last_run_at": state.last_run_at.isoformat() if state.last_run_at else None,
            "next_run_at": state.next_run_at.isoformat() if state.next_run_at else None,
            "last_successful_run_at": (
                state.last_successful_run_at.isoformat() if state.last_successful_run_at else None
            ),
            "runs_today": state.runs_today,
            "runs_today_date": (
                state.runs_today_date.isoformat() if state.runs_today_date else None
            ),
            "processed_urls": state.processed_urls,
        }

    @staticmethod
    def _deserialize(payload: str) -> WatchState:
        data = json.loads(payload)
        data["last_run_at"] = (
            datetime.fromisoformat(data["last_run_at"]) if data["last_run_at"] else None
        )
        data["next_run_at"] = (
            datetime.fromisoformat(data["next_run_at"]) if data["next_run_at"] else None
        )
        data["last_successful_run_at"] = (
            datetime.fromisoformat(data["last_successful_run_at"])
            if data["last_successful_run_at"]
            else None
        )
        data["runs_today_date"] = (
            date.fromisoformat(data["runs_today_date"]) if data["runs_today_date"] else None
        )
        return WatchState(**data)
