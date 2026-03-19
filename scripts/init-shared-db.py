#!/usr/bin/env python3
"""Initialize shared SQLite coordination database for agent workflows."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS agent_registry (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('idle', 'running', 'locked')),
    last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_incidents (
    incident_id TEXT PRIMARY KEY,
    source_project TEXT NOT NULL,
    forensic_report_link TEXT,
    resolution_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS automation_gates (
    gate_id TEXT PRIMARY KEY,
    is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    failure_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS locks (
    lock_key TEXT PRIMARY KEY,
    owner_agent_id TEXT NOT NULL,
    claimed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    status TEXT NOT NULL DEFAULT 'claimed' CHECK (status IN ('claimed', 'released'))
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    agent_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    file_path TEXT,
    diff_hash TEXT,
    intent_description TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_diff_hash
    ON agent_logs (diff_hash, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_locks_expires_at
    ON locks (expires_at);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            """
            INSERT INTO automation_gates (gate_id, is_active, failure_count)
            VALUES (?, ?, ?)
            ON CONFLICT(gate_id) DO NOTHING
            """,
            ("global_kill_switch", 1, 0),
        )
        conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize shared coordination SQLite database.")
    parser.add_argument(
        "--db-path",
        default=".ops/shared.db",
        help="Path to SQLite database (default: .ops/shared.db)",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path).resolve()
    init_db(db_path)
    print(f"Initialized shared DB at: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
