Param(
    [string]$WorkspaceRoot = ".."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-IfExists {
    param(
        [string]$Path,
        [scriptblock]$Action
    )

    if (Test-Path -LiteralPath $Path) {
        Push-Location $Path
        try {
            & $Action
        }
        finally {
            Pop-Location
        }
    }
}

$root = Resolve-Path -LiteralPath $WorkspaceRoot
Write-Host "Security audit root: $root"

# Node projects
$nodeProjects = @(
    "copilot-autopsy",
    "devflow/apps/agent",
    "devflow/apps/agent-host",
    "devflow/apps/web",
    "Obsidian Memory"
)

foreach ($project in $nodeProjects) {
    $projectPath = Join-Path $root $project
    Invoke-IfExists -Path $projectPath -Action {
        if (Test-Path -LiteralPath "package.json") {
            Write-Host "Running npm audit in $project"
            npm audit --audit-level=high
        }
    }
}

# Python project
$pythonProject = Join-Path $root "fixforward"
Invoke-IfExists -Path $pythonProject -Action {
    if (Test-Path -LiteralPath "pyproject.toml") {
        Write-Host "Running pip check in fixforward"
        python -m pip check
    }
}

Write-Host "Security audit completed."
