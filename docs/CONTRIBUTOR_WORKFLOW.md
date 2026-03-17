# Contributor Workflow

## Branching

1. Create short-lived branches per change.
2. Keep changes scoped to one or two projects when possible.
3. Use descriptive branch names.

## Pull Requests

1. Use the shared pull request template.
2. Select affected project scope accurately.
3. Provide validation commands and outcomes.
4. Flag AI-assisted code changes explicitly.

## Review Rules

1. CODEOWNERS approval required on security-sensitive files.
2. High-risk automation paths require ai-patch-reviewed label.
3. No direct merge without passing required security workflows.

## Quality Gates

1. Secret scan must pass.
2. Dependency audit must pass.
3. Path-based tests and lint checks must pass for changed projects.

## Documentation

1. Update canonical docs in this folder for workspace-wide changes.
2. Keep project-local docs for implementation details.
3. Remove duplicate docs once a canonical document exists.
