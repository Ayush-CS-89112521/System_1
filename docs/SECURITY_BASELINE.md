# Security Baseline

## Scope

This baseline covers the consolidated workspace and all projects under it.

## Control Objectives

1. Prevent secret exposure in source and CI logs.
2. Detect known-vulnerable dependencies in Node and Python.
3. Enforce least privilege for automation tokens.
4. Require human review for AI-generated patches.

## Required Controls

### 1) Secret Hygiene

- Maintain a root .env.example policy only, never commit real secrets.
- Add secret scanning in CI for all paths.
- Mask sensitive values in logs.

### 2) Dependency Governance

- Run npm audit for each Node project.
- Run Python dependency checks for fixforward.
- Track exceptions with expiry dates.

### 3) Token and Key Governance

- Separate token scopes per service.
- Rotate long-lived credentials on a schedule.
- Do not share encryption keys across unrelated services.

### 4) AI Automation Safety

- Require explicit user approval before applying generated patches.
- Store generated patch diffs for audit.
- Block direct auto-commit on high-risk changes.
- Enforce watchdog rate-limit lock when AI actor burst threshold is exceeded.
- Require unlock command flow with token validation before lock removal.

### 5) Release Safety

- Require passing security checks before merge.
- Require CODEOWNERS approval on sensitive paths.

## Minimum CI Security Gate

A pull request is blocked unless all pass:

1. Secret scan
2. Dependency audit
3. Lint and tests for changed projects
4. Ownership checks

## Ownership

Security owner assignment is defined in CODEOWNERS.
