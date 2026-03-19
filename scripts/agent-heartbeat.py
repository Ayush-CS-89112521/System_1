#!/usr/bin/env python3
"""Heartbeat updater for agent_registry.

Use this script for long-running agents that need periodic liveness updates.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS agent_registry (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL CHECK (status IN ('idle', 'running', 'locked')),
            last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def beat(conn: sqlite3.Connection, agent_id: str, status: str) -> None:
    conn.execute(
        """
        INSERT INTO agent_registry (id, status, last_seen)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            status = excluded.status,
            last_seen = CURRENT_TIMESTAMP
        """,
        (agent_id, status),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Update agent_registry heartbeat.")
    parser.add_argument("--db-path", default=".ops/shared.db")
    parser.add_argument("--agent-id", default="agent")
    parser.add_argument("--status", default="running", choices=["idle", "running", "locked"])
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(Path(args.db_path).resolve())
    try:
        ensure_schema(conn)
        if args.once:
            with conn:
                beat(conn, args.agent_id, args.status)
            return 0

        while True:
            with conn:
                beat(conn, args.agent_id, args.status)
            time.sleep(max(args.interval_seconds, 1))
    except KeyboardInterrupt:
        return 130
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
