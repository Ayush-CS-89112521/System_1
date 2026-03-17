# Setup Matrix

## Tooling Requirements

| Project | Runtime | Package Tool | Required External CLI |
|---|---|---|---|
| copilot-autopsy | Node >= 18 | npm | gh with Copilot |
| democratizequality-a11y-guard | Node >= 18 (planned) | npm | gh with Copilot (planned) |
| devflow/apps/agent | Node >= 18 | npm | gh, GitHub auth |
| devflow/apps/agent-host | Node >= 20 | npm | Docker optional |
| devflow/apps/web | Node >= 20 | npm | None mandatory |
| fixforward | Python >= 3.9 | pip/setuptools | gh with Copilot, git |
| Obsidian Memory | Node >= 18 | npm | notesmd-cli optional |

## Consolidation Rules

1. Keep Node and Python execution environments separate.
2. Keep project-specific environment files isolated.
3. Use shared governance files at the consolidation root.

## Standard Validation Commands

Run at project roots as applicable:

- npm test
- npm run lint
- npm audit --audit-level=high
- python -m pip check
- python -m pytest

## Notes

- Some commands depend on each project maturity and current test coverage.
- Missing commands should be added during migration phases.
