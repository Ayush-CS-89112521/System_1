Param(
    [string]$DbPath = ".ops/shared.db",
    [int]$StaleMinutes = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $DbPath)) {
    Write-Host "No shared DB found at $DbPath. Nothing to clean."
    exit 0
}

$python = @'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1]).resolve()
stale_minutes = int(sys.argv[2])

conn = sqlite3.connect(db_path)
conn.executescript("""
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
INSERT INTO automation_gates (gate_id, is_active, failure_count)
VALUES ('global_kill_switch', 1, 0)
ON CONFLICT(gate_id) DO NOTHING;
""")

latest = conn.execute(
    "SELECT MAX(last_seen) FROM agent_registry"
).fetchone()[0]

is_stale = True
if latest is not None:
    age_seconds = conn.execute(
        "SELECT CAST((julianday('now') - julianday(?)) * 86400 AS INTEGER)",
        (latest,),
    ).fetchone()[0]
    is_stale = age_seconds is None or age_seconds > stale_minutes * 60

if is_stale:
    conn.execute("DELETE FROM locks")
    conn.execute(
        "UPDATE automation_gates SET is_active = 1 WHERE gate_id = 'global_kill_switch'"
    )
    conn.execute(
        "INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description) VALUES (?, ?, ?, ?)",
        ("preflight", "stale_lock_reset", "locks", f"stale>{stale_minutes}m, locks cleared and gate re-enabled"),
    )
    print("Pre-flight reset applied: stale heartbeat detected.")
else:
    print("Pre-flight check passed: active heartbeat found, locks preserved.")

conn.commit()
conn.close()
'@

python -c $python $DbPath $StaleMinutes
exit $LASTEXITCODE
