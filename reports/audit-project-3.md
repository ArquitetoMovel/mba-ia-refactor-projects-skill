# Architecture Audit Report — Project 3: task-manager-api

**Stack:** Python 3 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + SQLite (`tasks.db`)  
**Domain:** Task Manager RESTful API (usuários, tarefas, categorias, relatórios de produtividade)  
**Execution Phase:** Phase 2 (Code Smells & Architecture Issues Detection)  
**Skill:** `refactor-arch`

---

## 1. Summary of Findings

| Severity | Count | Primary Impact Areas |
|----------|-------|----------------------|
| **CRITICAL** | 4 | Hardcoded Secrets, Insecure MD5 Password Hashing & Password Leaks, Fake Authentication Token, God Routes / Fat Controllers |
| **HIGH** | 4 | Incomplete MVC Architecture, Duplicated Logic across Endpoints (Shotgun Surgery), N+1 Queries on Task Listing, In-Memory Unused Notification State |
| **MEDIUM** | 4 | Long Methods in Routes, Misplaced Category CRUD in Report Routes, Dead Code / Unused Dependencies (`marshmallow`), Poor Error Handling (`print`/`bare except`) |
| **LOW** | 3 | Deprecated `datetime.utcnow()`, Inconsistent Naming & Redundant Booleans, Weak Password Validation Policy |
| **TOTAL** | **15** | **Exceeds minimum threshold (≥ 5 findings)** |

---

## 2. Detailed Findings (Ordered by Severity)

### [CRITICAL] Hardcoded Secrets in Source Code
- **Location:**
  - `file: app.py`; `line: 13-13`; `symbol: SECRET_KEY`
  - `file: services/notification_service.py`; `line: 7-10`; `symbol: SMTP_USER/SMTP_PASSWORD`
- **Description:** Chave secreta de sessão e credenciais de servidor de email SMTP inseridas diretamente nos arquivos fonte.
- **Impact:** Comprometimento da integridade das sessões e vazamento de credenciais em repositórios.
- **Recommendation:** Migrar para `config/settings.py` consumindo variáveis de ambiente via `os.getenv` com `.env.example`.

### [CRITICAL] Insecure MD5 Password Hashing & Password Hash Leaks in API
- **Location:**
  - `file: models/user.py`; `line: 16-25`; `symbol: User.to_dict`
  - `file: models/user.py`; `line: 27-32`; `symbol: User.set_password/check_password`
- **Description:** Uso do algoritmo quebrado MD5 para armazenar senhas e serialização do hash nos endpoints públicos de listagem de usuários, cadastro e login.
- **Impact:** Facilidade imediata de quebra por força bruta e exposição de credenciais para qualquer usuário da API.
- **Recommendation:** Substituir por `werkzeug.security` (`generate_password_hash`/`check_password_hash`) com salt dinâmico e remover a chave `password` de todas as serializações DTO/View.

### [CRITICAL] Fake Authentication Token Generator
- **Location:**
  - `file: routes/user_routes.py`; `line: 185-211`; `symbol: POST /login`
- **Description:** Rota de login gerava strings estáticas sem assinatura criptográfica, sem expiração e sem validação nos endpoints protegidos.
- **Impact:** Ausência total de proteção de rotas e falsa sensação de segurança.
- **Recommendation:** Implementar tokens assinados com expiração via `itsdangerous.URLSafeTimedSerializer` em `controllers/auth_controller.py`.

### [CRITICAL] God Routes / Fat Controllers (Violação de MVC)
- **Location:**
  - `file: routes/task_routes.py`; `line: 11-299`; `symbol: task route handlers`
  - `file: routes/user_routes.py`; `line: 10-211`; `symbol: user route handlers`
  - `file: routes/report_routes.py`; `line: 12-223`; `symbol: report and category route handlers`
- **Description:** Arquivos de rota concentrando orquestração HTTP, validação de tipos, regras de negócio complexas, queries ORM manuais e serialização JSON.
- **Impact:** Impossibilidade de reaproveitamento de código, testes acoplados a requisições e alta complexidade ciclomática.
- **Recommendation:** Decompor em camadas claras: Views (`views/task_views.py`), Controllers (`controllers/task_controller.py`), Schemas (`schemas/task_schema.py`) e Models (`models/task.py`).

### [HIGH] Incomplete MVC & Lack of Separation of Concerns
- **Location:**
  - `file: routes/task_routes.py`; `line: 1-299`; `symbol: route module`
  - `file: routes/user_routes.py`; `line: 1-211`; `symbol: route module`
  - `file: routes/report_routes.py`; `line: 1-223`; `symbol: route module`
  - `file: models/task.py`; `line: 1-60`; `symbol: Task model`
  - `file: models/user.py`; `line: 1-38`; `symbol: User model`
  - `file: models/category.py`; `line: 1-21`; `symbol: Category model`
- **Description:** Apesar da existência de diretórios, a arquitetura carecia de controladores dedicados e schemas de validação.
- **Recommendation:** Instituir padrão MVC rigoroso com Application Factory em `app.py`.

### [HIGH] Duplicated Business Logic (Shotgun Surgery)
- **Location:**
  - `file: routes/task_routes.py`; `line: 30-39`; `symbol: overdue calculation`
  - `file: routes/task_routes.py`; `line: 110-114`; `symbol: status/priority validation`
  - `file: routes/task_routes.py`; `line: 176-183`; `symbol: update validation`
  - `file: routes/task_routes.py`; `line: 283-287`; `symbol: overdue stats`
  - `file: routes/user_routes.py`; `line: 171-180`; `symbol: user task overdue calculation`
  - `file: routes/report_routes.py`; `line: 33-43`; `symbol: summary overdue calculation`
  - `file: routes/report_routes.py`; `line: 129-135`; `symbol: user report overdue calculation`
  - `file: models/task.py`; `line: 38-60`; `symbol: Task validation/domain methods`
  - `file: utils/helpers.py`; `line: 57-89`; `symbol: process_task_data validation`
  - `file: utils/helpers.py`; `line: 110-115`; `symbol: duplicated status/priority constants`
- **Description:** Regra de cálculo de atraso de tarefas (`overdue`), validações de status e prioridade duplicadas em múltiplos arquivos.
- **Recommendation:** Centralizar regra no método de domínio `Task.is_overdue()` e validações em Schemas Marshmallow.

### [HIGH] N+1 Query Problem in Task Listing
- **Location:**
  - `file: routes/task_routes.py`; `line: 14-59`; `symbol: GET /tasks`
- **Description:** Loop iterando sobre as tarefas e executando consultas individuais `User.query.get(t.user_id)` e `Category.query.get(t.category_id)`.
- **Recommendation:** Aplicar Eager Loading com `joinedload(Task.user)` e `joinedload(Task.category)` na query do SQLAlchemy.

### [HIGH] In-Memory Unused Notification State
- **Location:**
  - `file: services/notification_service.py`; `line: 6-6`; `symbol: NotificationService.notifications`
- **Description:** Histórico de notificações mantido em memória volátil, sem integração com as rotas de criação e atualização de tarefas.
- **Recommendation:** Integrar `NotificationService` ao controller de tarefas com suporte a envio SMTP configurável por ambiente.

### [MEDIUM] Long Methods in Routes
- **Location:**
  - `file: routes/report_routes.py`; `line: 12-101`; `symbol: summary_report`
  - `file: routes/task_routes.py`; `line: 11-63`; `symbol: get_tasks`
- **Recommendation:** Mover agregações para `ReportController` e consultas otimizadas no SQLAlchemy.

### [MEDIUM] Misplaced Category CRUD in Report Routes
- **Location:**
  - `file: routes/report_routes.py`; `line: 157-223`; `symbol: category CRUD handlers`
- **Description:** Endpoints de gerenciamento de categorias declarados dentro do arquivo de relatórios gerenciais.
- **Recommendation:** Extrair para `views/category_views.py` e `controllers/category_controller.py`.

### [MEDIUM] Dead Code & Unused Dependencies
- **Location:**
  - `file: requirements.txt`; `line: 4-6`; `symbol: marshmallow/requests/python-dotenv dependencies`
  - `file: utils/helpers.py`; `line: 9-108`; `symbol: unused helper functions`
  - `file: routes/task_routes.py`; `line: 7-7`; `symbol: unused imports`
- **Recommendation:** Efetivamente utilizar Marshmallow para validação DTO, remover dependências desnecessárias (`requests`) e limpar imports órfãos.

### [MEDIUM] Poor Error Handling and Print Logging
- **Location:**
  - `file: routes/task_routes.py`; `line: 62-63`; `symbol: GET /tasks error handler`
  - `file: routes/task_routes.py`; `line: 135-138`; `symbol: POST /tasks date handler`
  - `file: routes/task_routes.py`; `line: 146-154`; `symbol: POST /tasks persistence handler`
  - `file: routes/task_routes.py`; `line: 200-205`; `symbol: PUT /tasks date handler`
  - `file: routes/task_routes.py`; `line: 217-223`; `symbol: PUT /tasks persistence handler`
  - `file: routes/task_routes.py`; `line: 231-238`; `symbol: DELETE /tasks persistence handler`
  - `file: routes/user_routes.py`; `line: 80-90`; `symbol: POST /users persistence handler`
  - `file: routes/user_routes.py`; `line: 127-132`; `symbol: PUT /users persistence handler`
  - `file: routes/user_routes.py`; `line: 144-151`; `symbol: DELETE /users persistence handler`
  - `file: routes/report_routes.py`; `line: 182-188`; `symbol: POST /categories persistence handler`
  - `file: routes/report_routes.py`; `line: 204-209`; `symbol: PUT /categories persistence handler`
  - `file: routes/report_routes.py`; `line: 217-223`; `symbol: DELETE /categories persistence handler`
- **Recommendation:** Implementar `middlewares/error_handler.py` com classe customizada `AppError` e logging estruturado do Python.

### [LOW] Deprecated `datetime.utcnow()`
- **Location:**
  - `file: models/user.py`; `line: 14-14`; `symbol: User.created_at`
  - `file: models/task.py`; `line: 15-16`; `symbol: Task.created_at/updated_at`
  - `file: models/task.py`; `line: 50-60`; `symbol: Task.is_overdue`
  - `file: models/category.py`; `line: 11-11`; `symbol: Category.created_at`
  - `file: routes/user_routes.py`; `line: 172-172`; `symbol: get_user_tasks`
  - `file: routes/task_routes.py`; `line: 31-31`; `symbol: get_tasks`
  - `file: routes/task_routes.py`; `line: 72-72`; `symbol: get_task`
  - `file: routes/task_routes.py`; `line: 215-215`; `symbol: update_task`
  - `file: routes/task_routes.py`; `line: 285-285`; `symbol: task_stats`
  - `file: routes/report_routes.py`; `line: 35-35`; `symbol: summary_report`
  - `file: routes/report_routes.py`; `line: 42-42`; `symbol: summary_report`
  - `file: routes/report_routes.py`; `line: 45-45`; `symbol: summary_report`
  - `file: routes/report_routes.py`; `line: 71-71`; `symbol: summary_report`
  - `file: routes/report_routes.py`; `line: 133-133`; `symbol: user_report`
  - `file: seed.py`; `line: 66-74`; `symbol: seed task dates`
  - `file: services/notification_service.py`; `line: 35-35`; `symbol: notify_task_assigned`
  - `file: utils/helpers.py`; `line: 38-38`; `symbol: log_action`
- **Description:** Uso de `datetime.utcnow()` que gera avisos de obsolescência a partir do Python 3.12.
- **Recommendation:** Substituir por `datetime.now(timezone.utc)`.

### [LOW] Inconsistent Naming & Verbose Booleans
- **Location:**
  - `file: routes/report_routes.py`; `line: 157-164`; `symbol: cat variable`
  - `file: routes/report_routes.py`; `line: 190-202`; `symbol: cat/cat_id variables`
  - `file: models/user.py`; `line: 34-38`; `symbol: User.is_admin`
- **Recommendation:** Padronizar nomenclatura e simplificar expressões booleanas.

### [LOW] Weak Password Validation Policy
- **Location:**
  - `file: utils/helpers.py`; `line: 114-114`; `symbol: MIN_PASSWORD_LENGTH`
  - `file: routes/user_routes.py`; `line: 64-65`; `symbol: create_user password validation`
  - `file: routes/user_routes.py`; `line: 114-116`; `symbol: update_user password validation`
- **Recommendation:** Aumentar tamanho mínimo para 8 caracteres e aplicar validação via Marshmallow.
