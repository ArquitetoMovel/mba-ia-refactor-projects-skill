---
name: refactor-arch
description: Refactor the architecture of the project MVC to improve performance, maintainability, and scalability independently of stack technology.
---

# Refactor Architecture

summary: Refactor the architecture of the project to improve performance, maintainability, and scalability independently of stack technology.

## Phase 1: Detect tecnology stack and architecture
- Detect the technology stack used in the project (e.g., programming languages, frameworks, libraries, databases, etc.).

### Input
- Project source code and configuration files.

### Output (Sample)
- [project_analises_tpl](./templates/project_analysis.txt)


## Phase 2: Detect code smells and architecture issues antipatterns
- Detect code smells and architecture issues antipatterns in the project.
- Order findings by severity level (Critical, High, Medium, Low) based on the [issues_severity_ref](./references/issues_severity.md).
- Identify minimal of 5 code smells and architecture issues antipatterns in the project.
- Detect deprecated APIs if aplicable. 

### Input
- Project source code and configuration files.
- [issues_severity_ref](./references/issues_severity.md)

### Output (Sample)
```txt
 ================================
  PHASE 2: CODE SMELLS DETECTION
  ================================
  Code Smells Detected:
  - Long Method: 2 instances
  - Large Class: 1 instance
  - Duplicated Code: 3 instances
  - God Object: 1 instance
  - Feature Envy: 2 instances
  - Shotgun Surgery: 1 instance

  Architecture Issues Detected:
  - Tight Coupling between modules
  - Lack of Separation of Concerns
  - Inconsistent Naming Conventions
  - Poor Error Handling and Logging
  ================================================
```
- Present the findings in a structured format, including the severity level, description, and location of each issue.
- Ask the user to confirm to proceed to phase 3 (Refactor the architecture) or to stop the process.

## Phase 3: Refactor the architecture
- Refactor the project fixing the detected code smells and architecture issues antipatterns.
- Refactor the project to adopt **MVC (Model-View-Controller)** architecture pattern, ensuring a clear separation of concerns between the Model, View, and Controller components.
- Validate the refactored code to ensure that project functionallity is preserved and that the project still run.

### Output (Sample of the refactored code report)
```txt
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```
