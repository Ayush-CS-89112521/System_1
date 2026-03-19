#!/usr/bin/env python3
"""Run fixforward with a repo-local SQLite lock claim.

This wrapper enforces a claim in .ops/shared.db before invoking fixforward.
If an existing claim exists for the same lock key, it waits or exits.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence


DEFAULT_DB = ".ops/shared.db"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS agent_registry (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL CHECK (status IN ('idle', 'running', 'locked')),
            last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        """
    )
    conn.execute(
        """
        INSERT INTO automation_gates (gate_id, is_active, failure_count)
        VALUES ('global_kill_switch', 1, 0)
        ON CONFLICT(gate_id) DO NOTHING
        """
    )


def log_event(
    conn: sqlite3.Connection,
    *,
    agent_id: str,
    action_type: str,
    file_path: str,
    intent_description: str,
) -> None:
    conn.execute(
        """
        INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description)
        VALUES (?, ?, ?, ?)
        """,
        (agent_id, action_type, file_path, intent_description),
    )


def record_obsidian_event(obsidian_log_path: Path, *, title: str, details: str) -> None:
    obsidian_log_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    line = f"- [{now}] {title}: {details}\n"
    with obsidian_log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def claim_lock(
    conn: sqlite3.Connection,
    *,
    lock_key: str,
    agent_id: str,
    ttl_seconds: int,
    max_retries: int,
    base_backoff_ms: int,
    jitter_ms: int,
    strategy: str,

) -> tuple[bool, int]:
    attempt = 0

    while attempt < max_retries:
        attempt += 1
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
                return True, attempt

            holder = existing[0]
            log_event(
                conn,
                agent_id=agent_id,
                action_type="lock_conflict",
                file_path=lock_key,
                intent_description=f"attempt {attempt}; lock currently held by {holder}",
            )

        if strategy == "terminate":
            return False, attempt

        if attempt >= max_retries:
            break

        sleep_ms = (attempt * base_backoff_ms) + random.randint(0, jitter_ms)
        time.sleep(sleep_ms / 1000)

    return False, max_retries


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
        log_event(
            conn,
            agent_id=agent_id,
            action_type="lock_released",
            file_path=lock_key,
            intent_description="fixforward guarded run claim released",
        )


def heartbeat_once(conn: sqlite3.Connection, *, agent_id: str, status: str) -> None:
    with conn:
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


def heartbeat_loop(
    *,
    db_path: Path,
    agent_id: str,
    stop_event: threading.Event,
    interval_seconds: int,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        ensure_schema(conn)
        while not stop_event.is_set():
            heartbeat_once(conn, agent_id=agent_id, status="running")
            stop_event.wait(interval_seconds)
    finally:
        conn.close()


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
    parser.add_argument("--max-retries", type=int, default=5, help="Maximum lock claim retries")
    parser.add_argument(
        "--base-backoff-ms",
        type=int,
        default=1000,
        help="Base backoff per attempt in milliseconds",
    )
    parser.add_argument(
        "--jitter-ms",
        type=int,
        default=500,
        help="Jitter range in milliseconds added to each wait",
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=60,
        help="Heartbeat interval for agent_registry updates",
    )
    parser.add_argument("--ttl-seconds", type=int, default=1800, help="Lock TTL in seconds")
    parser.add_argument(
        "--obsidian-log-path",
        default=".ops/obsidian-events.md",
        help="Obsidian-compatible markdown log path for exhaustion events",
    )
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
    obsidian_log_path = Path(args.obsidian_log_path).resolve()

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
    heartbeat_thread: Optional[threading.Thread] = None
    heartbeat_stop = threading.Event()
    try:
        ensure_schema(conn)

        heartbeat_once(conn, agent_id=args.agent_id, status="locked")

        acquired, attempts = claim_lock(
            conn,
            lock_key=lock_key,
            agent_id=args.agent_id,
            ttl_seconds=args.ttl_seconds,
            max_retries=max(args.max_retries, 1),
            base_backoff_ms=max(args.base_backoff_ms, 1),
            jitter_ms=max(args.jitter_ms, 0),
            strategy=args.strategy,
        )
        if not acquired:
            with conn:
                log_event(
                    conn,
                    agent_id=args.agent_id,
                    action_type="concurrency_exhaustion",
                    file_path=lock_key,
                    intent_description=f"failed after {attempts} attempt(s)",
                )
            record_obsidian_event(
                obsidian_log_path,
                title="Concurrency Exhaustion",
                details=f"agent={args.agent_id} lock={lock_key} attempts={attempts}",
            )
            print(
                f"Lock conflict for {lock_key}. Strategy={args.strategy}. "
                f"Retries exhausted after {attempts} attempt(s).",
                file=sys.stderr,
            )
            return 130

        heartbeat_thread = threading.Thread(
            target=heartbeat_loop,
            kwargs={
                "db_path": db_path,
                "agent_id": args.agent_id,
                "stop_event": heartbeat_stop,
                "interval_seconds": max(args.heartbeat_seconds, 1),
            },
            daemon=True,
        )
        heartbeat_thread.start()

        return run_fixforward(command, project_path)
    finally:
        heartbeat_stop.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=2)

        if acquired:
            release_lock(conn, lock_key=lock_key, agent_id=args.agent_id)

        with conn:
            heartbeat_once(conn, agent_id=args.agent_id, status="idle")
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
