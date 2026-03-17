# Migration Tracker

## Status Legend

- [ ] Not started
- [~] In progress
- [x] Done

## Phase 1: Governance And Documentation Baseline

- [x] Create consolidation root scaffold.
- [x] Create security baseline document.
- [x] Create setup matrix document.
- [x] Add initial PR template.
- [x] Add initial CODEOWNERS.
- [x] Add security audit script.

## Phase 2: Security Automation

- [x] Add CI workflow for secret scan.
- [x] Add CI workflow for dependency audits.
- [x] Add CI workflow for path-based test execution.
- [x] Add patch approval gate for AI-generated changes.

## Phase 3: Documentation Consolidation

- [x] Create canonical docs index.
- [ ] De-duplicate overlapping DevFlow docs.
- [x] Add architecture map covering all projects.
- [x] Add environment variable and auth matrix.

## Phase 4: Controlled Workspace Migration

- [ ] Define target folder layout.
- [ ] Move projects into workspace with history-preserving strategy.
- [ ] Add workspace-level scripts for validation.
- [ ] Validate all CLI entry points post-move.

## Phase 5: Hardening And Enforcement

- [ ] Require CODEOWNERS approval on sensitive paths.
- [ ] Enforce mandatory checks before merge.
- [ ] Publish contributor workflow.
- [ ] Run rollback drill and archive legacy layout.
