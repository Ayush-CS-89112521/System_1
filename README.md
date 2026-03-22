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

- docs/README.md
- docs/00-overview/SETUP_MATRIX.md
- docs/02-governance/SECURITY_BASELINE.md
- docs/03-implementation/WATCHDOG_PROTOCOL.md
- docs/03-implementation/SAFETY_PROXY.md
- docs/04-operations/OPERATIONS_RUNBOOK.md
- docs/05-planning/MIGRATION_TRACKER.md
- .github/pull_request_template.md
- CODEOWNERS
- scripts/security-audit.ps1
- scripts/pre-flight.ps1
- scripts/panic-kill-switch.ps1

## Next

Use docs/README.md for reading order and docs/05-planning/MIGRATION_TRACKER.md to track execution.
