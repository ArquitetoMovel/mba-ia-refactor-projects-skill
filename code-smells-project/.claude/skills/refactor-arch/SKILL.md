---
name: refactor-arch
description: Refactor the architecture of the project MVC to improve performance, maintainability, and scalability independently of stack technology.
disable-model-invocation: true
---

# Refactor Architecture

summary: Refactor the architecture of the project to improve performance, maintainability, and scalability independently of stack technology.
general: Save all output reports in the `/docs` folder of the project.

## Phase 1: Detect tecnology stack and architecture
- Detect the technology stack used in the project (e.g., programming languages, frameworks, libraries, databases, etc.).

### Input
- Project source code and configuration files.

### Output (Sample)
- [project_analises_tpl](./templates/project_analysis.txt)


## Phase 2: Detect code smells and architecture issues antipatterns
- Detect code smells and architecture issues antipatterns in the project.
- Consult the [anti_patterns_catalog](./references/anti_patterns_catalog.md) for taxonomy, detection markers, and architectural remediation strategies.
- Order findings by severity level (Critical, High, Medium, Low) based on the [issues_severity_ref](./references/issues_severity.md).
- Identify minimal of 5 code smells and architecture issues antipatterns in the project.
- Detect deprecated APIs if applicable.
- For every finding, capture the exact **code lines interval** (`line: start-end`, or a single line when the issue is one line) in the source file. Do not report a finding without `file` and `line`.

### Input
- Project source code and configuration files.
- [issues_severity_ref](./references/issues_severity.md)
- [anti_patterns_catalog](./references/anti_patterns_catalog.md)

### Output (Sample)
- [project_issues_tpl_report](./templates/project_issues.txt)

- Present the findings in a structured format, including the severity level, description, location (`file` + `line` interval) of each issue.
- Ask the user to confirm to proceed to Phase 3 (Update the audit report) or to stop the process.

## Phase 3: Update the audit report with line ranges
- Update only `## 2. Detailed Findings (Ordered by Severity)` in the repository-level `reports/audit-project-1.md` (`../reports/audit-project-1.md` when running from this project).
- Use the findings from Phase 2 and verify each location against the legacy source files analyzed by the audit.
- Record an exact, inclusive, 1-indexed line interval for every affected file using `line: START-END`; use `N-N` for a single-line finding.
- Add one location entry per file. If the finding affects disjoint sections in the same file, record each interval separately.
- Keep the existing severity order, finding titles, descriptions, impacts, recommendations, summary counts, and total unchanged unless Phase 2 provides an explicit correction.
- Replace approximate locations such as `~LOC`, `several functions`, or an unqualified file name with concrete file paths and line ranges.
- Do not report a finding without both `file` and `line` values, and validate that every range points to the described code.

### Input
- Phase 2 findings and source-code locations.
- Legacy source files used by `reports/audit-project-1.md`.
- [audit_detailed_findings_tpl](../../../.cursor/skills/refactor-arch/templates/audit_detailed_findings.txt)

### Output
- Updated `reports/audit-project-1.md`, with line ranges in Section 2 for every finding.
- After updating the report, ask the user to confirm before proceeding to Phase 4 (Refactor the architecture) or to stop the process.

## Phase 4: Refactor the architecture
- Refactor the project fixing the detected code smells and architecture issues antipatterns based on [anti_patterns_catalog](./references/anti_patterns_catalog.md).
- Refactor the project to adopt **MVC (Model-View-Controller)** architecture pattern, ensuring a clear separation of concerns between the Model, View, and Controller components.
- Validate the refactored code to ensure that project functionallity is preserved and that the project still run.
- Update the `README.md` and `AGENTS.md` files to reflect the new architecture and any changes made during the refactoring process.

### Output (Sample of the refactored code report)
- [project_refactored_tpl_report](./templates/project_refactored.txt)

## Phase 5: Generate Refactoring Playbook
- Always generate the architectural **Refactoring Playbook** (`docs/playbook_refatoracao.md`) documenting the transformation patterns applied during the refactoring.
- Detail the **8 transformation patterns** with:
  1. Diagnostic and context (detected code smell / anti-pattern and standard severity).
  2. Architectural transformation strategy (layers affected, responsibilities).
  3. Concrete **Before (Antes)** and **After (Depois)** code examples extracted directly from the codebase.
- Include an executive summary table, target MVC architecture diagram, and practical step-by-step execution guide.

### Output
- Architecture Playbook: `docs/playbook_refatoracao.md`
