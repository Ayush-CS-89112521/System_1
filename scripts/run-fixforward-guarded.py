#!/usr/bin/env python3
"""Run fixforward with a repo-local SQLite lock claim.

This wrapper enforces a claim in .ops/shared.db before invoking fixforward.
If an existing claim exists for the same lock key, it waits or exits.
"""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence


DEFAULT_DB = ".ops/shared.db"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
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
        """
    )


def claim_lock(
    conn: sqlite3.Connection,
    *,
    lock_key: str,
    agent_id: str,
    ttl_seconds: int,
    wait_seconds: int,
    strategy: str,
) -> bool:
    deadline = time.time() + max(wait_seconds, 0)

    while True:
        with conn:
            conn.execute(
                """
                DELETE FROM locks
                WHERE expires_at IS NOT NULL
                  AND datetime(expires_at) <= datetime('now')
                """
            )
            existing = conn.execute(
                "SELECT owner_agent_id FROM locks WHERE lock_key = ? AND status = 'claimed'",
                (lock_key,),
            ).fetchone()

            if not existing:
                conn.execute(
                    """
                    INSERT INTO locks (lock_key, owner_agent_id, expires_at, status)
                    VALUES (?, ?, datetime('now', ?), 'claimed')
                    """,
                    (lock_key, agent_id, f"+{ttl_seconds} seconds"),
                )
                conn.execute(
                    """
                    INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description)
                    VALUES (?, 'lock_claimed', ?, ?)
                    """,
                    (agent_id, lock_key, "fixforward guarded run claim acquired"),
                )
                return True

            conn.execute(
                """
                INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description)
                VALUES (?, 'lock_conflict', ?, ?)
                """,
                (
                    agent_id,
                    lock_key,
                    f"lock currently held by {existing[0]}",
                ),
            )

        if strategy == "terminate":
            return False

        if time.time() >= deadline:
            return False

        time.sleep(2)


def release_lock(conn: sqlite3.Connection, *, lock_key: str, agent_id: str) -> None:
    with conn:
        conn.execute(
            """
            UPDATE locks
            SET status = 'released', expires_at = datetime('now')
            WHERE lock_key = ? AND owner_agent_id = ?
            """,
            (lock_key, agent_id),
        )
        conn.execute(
            """
            INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description)
            VALUES (?, 'lock_released', ?, ?)
            """,
            (agent_id, lock_key, "fixforward guarded run claim released"),
        )


def run_fixforward(command: Sequence[str], project_path: Path) -> int:
    result = subprocess.run(command, cwd=str(project_path))
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixforward with shared lock guard.")
    parser.add_argument("--project-path", default=".", help="Target project path for fixforward run")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="SQLite path (default: .ops/shared.db)")
    parser.add_argument("--agent-id", default="agent", help="Agent identity for lock ownership")
    parser.add_argument(
        "--strategy",
        choices=["wait", "terminate"],
        default="wait",
        help="Conflict strategy if lock already exists",
    )
    parser.add_argument("--wait-seconds", type=int, default=30, help="Wait window in seconds")
    parser.add_argument("--ttl-seconds", type=int, default=1800, help="Lock TTL in seconds")
    parser.add_argument(
        "fixforward_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to fixforward (prefix with -- then args)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_path = Path(args.project_path).resolve()
    db_path = Path(args.db_path).resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    lock_key = f"fixforward:{project_path}"

    command = ["fixforward", "run", "--path", str(project_path)]
    if args.fixforward_args:
      tail = args.fixforward_args
      if tail and tail[0] == "--":
          tail = tail[1:]
      command.extend(tail)

    conn = sqlite3.connect(db_path)
    acquired = False
    try:
        ensure_schema(conn)

        acquired = claim_lock(
            conn,
            lock_key=lock_key,
            agent_id=args.agent_id,
            ttl_seconds=args.ttl_seconds,
            wait_seconds=args.wait_seconds,
            strategy=args.strategy,
        )
        if not acquired:
            print(
                f"Lock conflict for {lock_key}. Strategy={args.strategy}. "
                "Another agent already holds claim.",
                file=sys.stderr,
            )
            return 2

        return run_fixforward(command, project_path)
    finally:
        if acquired:
            release_lock(conn, lock_key=lock_key, agent_id=args.agent_id)
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
