# Consolidation Report

## Executive Decision

Proceed with a federated monorepo approach.

Do not fuse all source code into a single application. Keep each project independently versioned and runnable while centralizing security and documentation governance.

## Why This Model

1. The workspace contains both Node and Python projects.
2. Project maturity differs significantly across repositories.
3. Security exposure increases if all automation and credentials are merged into one runtime boundary.
4. Documentation and policy centralization can be done immediately without destabilizing implementations.

## Evidence Summary

### Runtime And Packaging

- copilot-autopsy: Node CLI package.
- devflow: multi-app Node and TypeScript system with agent, host, and web components.
- Obsidian Memory: Node CLI with plugin packaging flow.
- fixforward: Python package and CLI flow.
- democratizequality-a11y-guard: documentation and specification heavy, implementation still maturing.

### Security Risk Surface

- Multiple projects rely on Copilot and GitHub tooling.
- Automation-heavy workflows include file writes, patching, and git operations.
- Secret and token governance is currently project-scoped and should be normalized at workspace policy level.

### Documentation Opportunity

- Consolidation can reduce drift and duplication by introducing canonical root-level documents and ownership.

## Target State

1. One consolidation root with governance files.
2. Shared security checks and policy gates.
3. Canonical documentation index and setup matrix.
4. Independent project release paths retained.

## Initial Deliverables Completed

- Consolidation workspace root created.
- Security baseline document created.
- Setup matrix created.
- Migration tracker created.
- PR template and CODEOWNERS created.
- Cross-project security audit script created.

## Next Implementation Steps

1. Add CI workflows for secret scanning and dependency audits.
2. Add docs index and architecture map as canonical references.
3. Add path-based quality checks for each project.
4. Add approval gates for AI-generated patch application.
5. Plan history-preserving migration sequence for repository movement.

## Success Criteria

- Security gates run on every pull request.
- Documentation has a single source of truth per topic.
- All existing project entry points remain operational.
- No forced cross-language runtime merge.
