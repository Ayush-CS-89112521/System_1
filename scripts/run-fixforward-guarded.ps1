Param(
    [string]$ProjectPath = ".",
    [string]$DbPath = ".ops/shared.db",
    [string]$AgentId = "agent",
    [ValidateSet("wait", "terminate")]
    [string]$Strategy = "wait",
    [int]$MaxRetries = 5,
    [int]$BaseBackoffMs = 1000,
    [int]$JitterMs = 500,
    [int]$HeartbeatSeconds = 60,
    [int]$TtlSeconds = 1800,
    [string]$ObsidianLogPath = ".ops/obsidian-events.md",
    [string[]]$FixforwardArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "run-fixforward-guarded.py"
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing runner script: $scriptPath"
}

$cmd = @(
    $scriptPath,
    "--project-path", $ProjectPath,
    "--db-path", $DbPath,
    "--agent-id", $AgentId,
    "--strategy", $Strategy,
    "--max-retries", "$MaxRetries",
    "--base-backoff-ms", "$BaseBackoffMs",
    "--jitter-ms", "$JitterMs",
    "--heartbeat-seconds", "$HeartbeatSeconds",
    "--obsidian-log-path", $ObsidianLogPath,
    "--ttl-seconds", "$TtlSeconds"
)

if ($FixforwardArgs) {
    $cmd += "--"
    $cmd += $FixforwardArgs
}

python @cmd
exit $LASTEXITCODE
