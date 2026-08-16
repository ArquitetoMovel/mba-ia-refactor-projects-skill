---
name: refactor-arch
description: Refactor the architecture of the project MVC to improve performance, maintainability, and scalability independently of stack technology.
---

# Refactor Architecture

summary: Refactor the architecture of the project to improve performance, maintainability, and scalability independently of stack technology.
general: Save all output reports and playbooks in the `/docs` folder of the project.

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

### Input
- Project source code and configuration files.
- [issues_severity_ref](./references/issues_severity.md)
- [anti_patterns_catalog](./references/anti_patterns_catalog.md)

### Output (Sample)
- [project_issues_tpl_report](./templates/project_issues.txt)

- Present the findings in a structured format, including the severity level, description, and location of each issue.
- Ask the user to confirm to proceed to phase 3 (Refactor the architecture) or to stop the process.

## Phase 3: Refactor the architecture
- Refactor the project fixing the detected code smells and architecture issues antipatterns based on [anti_patterns_catalog](./references/anti_patterns_catalog.md).
- Refactor the project to adopt **MVC (Model-View-Controller)** architecture pattern, ensuring a clear separation of concerns between the Model, View, and Controller components.
- Validate the refactored code to ensure that project functionallity is preserved and that the project still run.
- Update the `README.md` and `AGENTS.md` files to reflect the new architecture and any changes made during the refactoring process.

### Output (Sample of the refactored code report)
- [project_refactored_tpl_report](./templates/project_refactored.txt)


## Phase 4: Generate Refactoring Playbook
- Always generate the architectural **Refactoring Playbook** (`docs/playbook_refatoracao.md`) documenting the transformation patterns applied during the refactoring.
- Detail the **8 transformation patterns** with:
  1. Diagnostic and context (detected code smell / anti-pattern and standard severity).
  2. Architectural transformation strategy (layers affected, responsibilities).
  3. Concrete **Before (Antes)** and **After (Depois)** code examples extracted directly from the codebase.
- Include an executive summary table, target MVC architecture diagram, and practical step-by-step execution guide.

### Output
- Architecture Playbook: `docs/playbook_refatoracao.md`
