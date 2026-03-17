# Architecture Map

## Federated Workspace Topology

1. copilot-autopsy
- Purpose: repository forensic analysis and reporting.
- Runtime: Node.
- Output: analysis markdown report.

2. democratizequality-a11y-guard
- Purpose: accessibility guardrail workflow and planned agentic checks.
- Runtime: Node planned.
- Current state: documentation and command specification heavy.

3. devflow
- Purpose: multi-component AI DevOps platform.
- Runtime: Node and TypeScript.
- Components: agent CLI, agent host service, web app.

4. fixforward
- Purpose: incident-to-fix automation and patch workflow.
- Runtime: Python.
- Behavior: test failure analysis and automated patch flow.

5. Obsidian Memory
- Purpose: memory management for Copilot workflows.
- Runtime: Node.
- Behavior: vault and plugin oriented command system.

## Cross-Cutting Controls

- Security baseline and dependency governance.
- Documentation ownership and canonical indexing.
- Pull request template and ownership enforcement.
- Runtime separation between Node and Python environments.

## Integration Boundaries

- Share policy, not runtime state.
- Share docs, not direct credential stores.
- Share CI quality standards, not forced release cycles.

## Planned Shared Layers

1. Governance layer
- CODEOWNERS
- PR templates
- security baseline

2. Documentation layer
- setup matrix
- architecture map
- migration tracker

3. Automation layer
- cross-project security audit script
- future CI workflows with path filters
