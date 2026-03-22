# Environment And Auth Matrix

## Purpose

This matrix defines secret boundaries and authentication flow ownership across projects in the consolidated workspace.

## Matrix

| Project | Primary Auth | Sensitive Values | Storage Boundary | Notes |
|---|---|---|---|---|
| copilot-autopsy | GitHub CLI auth | Copilot and GitHub tokens via gh | user machine and gh config | no project-level token storage expected |
| democratizequality-a11y-guard | planned GitHub/Copilot auth | planned hook and DB credentials | project-local config planned | implementation pending |
| devflow/apps/web | OAuth and JWT | JWT secrets, API secret, DB URI, OAuth secrets | web app environment only | do not share with agent host by default |
| devflow/apps/agent | OAuth device or browser flow | agent token and optional local config secrets | local user machine | separate from web server secret set |
| devflow/apps/agent-host | bearer token and service auth | host auth tokens and optional encryption key | host environment only | keep separate key rotation policy |
| fixforward | GitHub CLI auth and git permissions | Copilot context and git automation authority | local machine and repo scope | require review for generated patches |
| Obsidian Memory | local CLI execution | vault path and optional external tool settings | local machine and vault path | optional notesmd adapter increases command surface |

## Boundary Rules

1. Never reuse one secret across unrelated services.
2. Keep web, agent, and host secrets separated in devflow.
3. Keep Python and Node secret injection pipelines separate.
4. Enforce masked output in CI logs.

## Rotation Policy

- Rotate critical secrets every 90 days.
- Rotate immediately after security incidents.
- Track rotation date in project-local operations notes.
