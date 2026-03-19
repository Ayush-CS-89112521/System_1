# Building System Workspace

This folder is the consolidation root for a federated monorepo strategy.

## Goals

- Centralize security policy and checks.
- Centralize documentation and onboarding.
- Keep each project independently versioned and runnable.

## Current Projects In Scope

- copilot-autopsy
- democratizequality-a11y-guard
- devflow
- fixforward
- Obsidian Memory

## Implementation Phases

1. Governance baseline and shared docs.
2. Security baseline and automated checks.
3. Documentation deduplication and canonical index.
4. Controlled migration with no runtime fusion.
5. Hardening and enforcement.

## Phase 1 Deliverables

- docs/SECURITY_BASELINE.md
- docs/SETUP_MATRIX.md
- docs/MIGRATION_TRACKER.md
- docs/WATCHDOG_PROTOCOL.md
- docs/SAFETY_PROXY.md
- docs/OPERATIONS_RUNBOOK.md
- .github/pull_request_template.md
- CODEOWNERS
- scripts/security-audit.ps1
- scripts/pre-flight.ps1
- scripts/panic-kill-switch.ps1

## Next

Use docs/MIGRATION_TRACKER.md to execute tasks in order and track completion.
