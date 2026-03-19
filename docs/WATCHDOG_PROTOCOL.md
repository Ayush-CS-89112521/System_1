# Watchdog Protocol

## Purpose

Prevent runaway AI-driven commit bursts from draining API usage or destabilizing repository operations.

## What Is Implemented

1. PR gate workflow: `.github/workflows/rate-limit-gate.yml`
2. Unlock command workflow: `.github/workflows/watchdog-unlock-command.yml`
3. Shared DB initializer: `scripts/init-shared-db.py`
4. Guarded FixForward launcher: `scripts/run-fixforward-guarded.py` and `scripts/run-fixforward-guarded.ps1`

## Rate-Limit Gate Logic

1. Trigger: pull_request and workflow_dispatch
2. Checks open watchdog lock issue (`watchdog-lock` label)
3. Counts actor commits in last hour with `[AI]` marker
4. If `actor == agent` and count > threshold, it:
- creates lock issue
- fails the workflow
- sends webhook POST alert
5. While lock issue is open, subsequent PRs fail

## Required Repository Variables And Secrets

### Variables

- `WATCHDOG_AI_ACTORS`
- `WATCHDOG_THRESHOLD_PER_HOUR`

Recommended defaults:

- `WATCHDOG_AI_ACTORS=agent`
- `WATCHDOG_THRESHOLD_PER_HOUR=10`

### Secrets

- `WATCHDOG_ALERT_WEBHOOK_URL`
- `WATCHDOG_UNLOCK_TOKEN`

## Unlock Command

Unlock workflow supports:

1. Manual run via Actions (workflow_dispatch)
2. External bridge call via repository_dispatch (`watchdog_unlock`)

Expected payload keys:

- `command=unlock`
- `unlock_token=<WATCHDOG_UNLOCK_TOKEN>`

Example repository_dispatch call:

```bash
curl -L -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <GITHUB_PAT_WITH_REPO_SCOPE>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/Ayush-CS-89112521/System_1/dispatches \
  -d '{
    "event_type":"watchdog_unlock",
    "client_payload":{
      "command":"unlock",
      "unlock_token":"<WATCHDOG_UNLOCK_TOKEN>"
    }
  }'
```

## Shared SQLite Database

Initialize DB:

```bash
python scripts/init-shared-db.py --db-path .ops/shared.db
```

This initializes:

- `agent_registry`
- `system_incidents`
- `automation_gates`
- `locks`
- `agent_logs`

## Guarded FixForward Usage

PowerShell wrapper:

```powershell
./scripts/run-fixforward-guarded.ps1 -ProjectPath ../fixforward -AgentId agent -Strategy wait -WaitSeconds 30
```

Python wrapper:

```bash
python scripts/run-fixforward-guarded.py --project-path ../fixforward --agent-id agent --strategy wait --wait-seconds 30
```

Behavior:

1. Acquire lock in `locks` table before run
2. If claim exists, wait or terminate by strategy
3. Release lock after process exits
4. Append lock lifecycle events to `agent_logs`
