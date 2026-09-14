from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS incidents (
  incident_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS detections (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS simulations (
  cache_key TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS analysis_artifacts (
  incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
  artifact_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (incident_id, artifact_type)
);
CREATE TABLE IF NOT EXISTS evidence_events (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
  payload TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS evidence_events_incident_time ON evidence_events(incident_id, occurred_at);
CREATE INDEX IF NOT EXISTS messages_incident_time ON messages(incident_id, created_at);
"""


class Store:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        path = Path(self.database_path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    @staticmethod
    def encode(payload: dict) -> str:
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def decode(payload: str) -> dict:
        return json.loads(payload)

    def save_artifact(self, incident_id: str, artifact_type: str, payload: dict, updated_at: str) -> None:
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO analysis_artifacts(incident_id, artifact_type, payload, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(incident_id, artifact_type) DO UPDATE SET
                  payload = excluded.payload, updated_at = excluded.updated_at""",
                (incident_id, artifact_type, self.encode(payload), updated_at),
            )

    def get_artifact(self, incident_id: str, artifact_type: str) -> dict | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT payload FROM analysis_artifacts WHERE incident_id = ? AND artifact_type = ?",
                (incident_id, artifact_type),
            ).fetchone()
        return self.decode(row["payload"]) if row else None

    def artifact_updated_at(self, incident_id: str, artifact_type: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT updated_at FROM analysis_artifacts WHERE incident_id = ? AND artifact_type = ?",
                (incident_id, artifact_type),
            ).fetchone()
        return row["updated_at"] if row else None

    def list_simulations(self, incident_id: str) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT payload FROM simulations WHERE json_extract(payload, '$.incident_id') = ? ORDER BY created_at DESC",
                (incident_id,),
            ).fetchall()
        return [self.decode(row["payload"]) for row in rows]
