Param(
    [string]$ProjectPath = ".",
    [string]$DbPath = ".ops/shared.db",
    [string]$AgentId = "agent",
    [ValidateSet("wait", "terminate")]
    [string]$Strategy = "wait",
    [int]$WaitSeconds = 30,
    [int]$TtlSeconds = 1800,
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
    "--wait-seconds", "$WaitSeconds",
    "--ttl-seconds", "$TtlSeconds"
)

if ($FixforwardArgs) {
    $cmd += "--"
    $cmd += $FixforwardArgs
}

python @cmd
exit $LASTEXITCODE
