# Operations Runbook

## 1) Initialize Shared DB

```bash
python scripts/init-shared-db.py --db-path .ops/shared.db
```

## 2) Pre-Flight Recovery On Boot

Use this before starting agent jobs:

```powershell
./scripts/pre-flight.ps1 -DbPath .ops/shared.db -StaleMinutes 30
```

Behavior:

1. If latest heartbeat is stale beyond threshold, it clears locks and re-enables gate
2. If heartbeat is active, locks are preserved

## 3) Start Safety Proxy

```bash
pnpm --filter safety-proxy start
```

## 4) Run Guarded FixForward

```powershell
./scripts/run-fixforward-guarded.ps1 -ProjectPath ../fixforward -AgentId agent -Strategy wait -MaxRetries 5 -BaseBackoffMs 1000 -JitterMs 500 -HeartbeatSeconds 60
```

## 5) Panic Kill Switch

Disable all automation immediately:

```powershell
./scripts/panic-kill-switch.ps1 -DbPath .ops/shared.db
```

Optional process termination:

```powershell
./scripts/panic-kill-switch.ps1 -DbPath .ops/shared.db -ForceKillAll
```

## 6) Watchdog Unlock via Webhook Bridge

Dispatch to repository with payload:

- `event_type=watchdog_unlock`
- `command=unlock`
- `unlock_token=<WATCHDOG_UNLOCK_TOKEN>`
- `source=<allowed-source>`
- `timestamp=<ISO-8601>`
- `signature=<hmac-if-configured>`

## 7) Required Repo Settings

Variables:

- `WATCHDOG_AI_ACTORS=agent`
- `WATCHDOG_THRESHOLD_PER_HOUR=10`
- `WATCHDOG_UNLOCK_ALLOWED_ACTORS=<comma-separated actors>`
- `WATCHDOG_UNLOCK_ALLOWED_SOURCES=manual,slack,discord,telegram`
- `WATCHDOG_UNLOCK_MAX_AGE_SECONDS=300`

Secrets:

- `WATCHDOG_ALERT_WEBHOOK_URL`
- `WATCHDOG_UNLOCK_TOKEN`
- `WATCHDOG_UNLOCK_HMAC_SECRET` (optional but recommended)
