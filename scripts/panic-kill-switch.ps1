Param(
    [string]$DbPath = ".ops/shared.db",
    [switch]$ForceKillAll
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $DbPath)) {
    throw "Shared DB not found at $DbPath"
}

$python = @'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1]).resolve()
conn = sqlite3.connect(db_path)
conn.executescript("""
CREATE TABLE IF NOT EXISTS automation_gates (
    gate_id TEXT PRIMARY KEY,
    is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    failure_count INTEGER NOT NULL DEFAULT 0
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
conn.execute("UPDATE automation_gates SET is_active = 0 WHERE gate_id = 'global_kill_switch'")
conn.execute(
    "INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description) VALUES (?, ?, ?, ?)",
    ("panic", "gate_disabled", "automation_gates", "panic kill switch activated"),
)
conn.commit()
conn.close()
print("Global kill switch set to inactive.")
'@

python -c $python $DbPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($ForceKillAll) {
    Write-Host "Force killing node.exe and python.exe processes..."
    taskkill /F /IM node.exe /IM python.exe | Out-Null
}

Write-Host "Panic procedure completed."
