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
- **Location:** `app.py:13` (`SECRET_KEY = 'super-secret-key-change-in-production'`), `services/notification_service.py:7-10` (`SMTP_USER`, `SMTP_PASSWORD`)
- **Description:** Chave secreta de sessão e credenciais de servidor de email SMTP inseridas diretamente nos arquivos fonte.
- **Impact:** Comprometimento da integridade das sessões e vazamento de credenciais em repositórios.
- **Recommendation:** Migrar para `config/settings.py` consumindo variáveis de ambiente via `os.getenv` com `.env.example`.

### [CRITICAL] Insecure MD5 Password Hashing & Password Hash Leaks in API
- **Location:** `models/user.py:27-32` (`hashlib.md5(password.encode()).hexdigest()`), `models/user.py:21` (`to_dict` contendo chave `password`)
- **Description:** Uso do algoritmo quebrado MD5 para armazenar senhas e serialização do hash nos endpoints públicos de listagem de usuários, cadastro e login.
- **Impact:** Facilidade imediata de quebra por força bruta e exposição de credenciais para qualquer usuário da API.
- **Recommendation:** Substituir por `werkzeug.security` (`generate_password_hash`/`check_password_hash`) com salt dinâmico e remover a chave `password` de todas as serializações DTO/View.

### [CRITICAL] Fake Authentication Token Generator
- **Location:** `routes/user_routes.py:185-211` (`return 'fake-jwt-token-' + str(user.id)`)
- **Description:** Rota de login gerava strings estáticas sem assinatura criptográfica, sem expiração e sem validação nos endpoints protegidos.
- **Impact:** Ausência total de proteção de rotas e falsa sensação de segurança.
- **Recommendation:** Implementar tokens assinados com expiração via `itsdangerous.URLSafeTimedSerializer` em `controllers/auth_controller.py`.

### [CRITICAL] God Routes / Fat Controllers (Violação de MVC)
- **Location:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Description:** Arquivos de rota concentrando orquestração HTTP, validação de tipos, regras de negócio complexas, queries ORM manuais e serialização JSON.
- **Impact:** Impossibilidade de reaproveitamento de código, testes acoplados a requisições e alta complexidade ciclomática.
- **Recommendation:** Decompor em camadas claras: Views (`views/task_views.py`), Controllers (`controllers/task_controller.py`), Schemas (`schemas/task_schema.py`) e Models (`models/task.py`).

### [HIGH] Incomplete MVC & Lack of Separation of Concerns
- **Location:** Estrutura geral de pastas (`models/` e `routes/` apenas)
- **Description:** Apesar da existência de diretórios, a arquitetura carecia de controladores dedicados e schemas de validação.
- **Recommendation:** Instituir padrão MVC rigoroso com Application Factory em `app.py`.

### [HIGH] Duplicated Business Logic (Shotgun Surgery)
- **Location:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`, `models/task.py`, `utils/helpers.py`
- **Description:** Regra de cálculo de atraso de tarefas (`overdue`), validações de status e prioridade duplicadas em múltiplos arquivos.
- **Recommendation:** Centralizar regra no método de domínio `Task.is_overdue()` e validações em Schemas Marshmallow.

### [HIGH] N+1 Query Problem in Task Listing
- **Location:** `routes/task_routes.py:14-59` (`GET /tasks`)
- **Description:** Loop iterando sobre as tarefas e executando consultas individuais `User.query.get(t.user_id)` e `Category.query.get(t.category_id)`.
- **Recommendation:** Aplicar Eager Loading com `joinedload(Task.user)` e `joinedload(Task.category)` na query do SQLAlchemy.

### [HIGH] In-Memory Unused Notification State
- **Location:** `services/notification_service.py:6` (`self.notifications = []`)
- **Description:** Histórico de notificações mantido em memória volátil, sem integração com as rotas de criação e atualização de tarefas.
- **Recommendation:** Integrar `NotificationService` ao controller de tarefas com suporte a envio SMTP configurável por ambiente.

### [MEDIUM] Long Methods in Routes
- **Location:** `routes/report_routes.py` (`summary_report` ~90 LOC), `routes/task_routes.py` (`get_tasks`).
- **Recommendation:** Mover agregações para `ReportController` e consultas otimizadas no SQLAlchemy.

### [MEDIUM] Misplaced Category CRUD in Report Routes
- **Location:** `routes/report_routes.py:157-223`
- **Description:** Endpoints de gerenciamento de categorias declarados dentro do arquivo de relatórios gerenciais.
- **Recommendation:** Extrair para `views/category_views.py` e `controllers/category_controller.py`.

### [MEDIUM] Dead Code & Unused Dependencies
- **Location:** `marshmallow`, `requests`, `python-dotenv` no `requirements.txt` sem utilização nas rotas originais; funções mortas em `helpers.py`.
- **Recommendation:** Efetivamente utilizar Marshmallow para validação DTO, remover dependências desnecessárias (`requests`) e limpar imports órfãos.

### [MEDIUM] Poor Error Handling and Print Logging
- **Location:** `routes/*.py` com blocos `try/except Exception as e:` seguidos de `print(e)`.
- **Recommendation:** Implementar `middlewares/error_handler.py` com classe customizada `AppError` e logging estruturado do Python.

### [LOW] Deprecated `datetime.utcnow()`
- **Location:** `models/*.py`, `routes/*.py`, `seed.py`, `services/notification_service.py`
- **Description:** Uso de `datetime.utcnow()` que gera avisos de obsolescência a partir do Python 3.12.
- **Recommendation:** Substituir por `datetime.now(timezone.utc)`.

### [LOW] Inconsistent Naming & Verbose Booleans
- **Location:** `routes/report_routes.py` (`cat` vs `category`), `models/user.py` (`is_admin`).
- **Recommendation:** Padronizar nomenclatura e simplificar expressões booleanas.

### [LOW] Weak Password Validation Policy
- **Location:** `utils/helpers.py` (`MIN_PASSWORD_LENGTH = 4`)
- **Recommendation:** Aumentar tamanho mínimo para 8 caracteres e aplicar validação via Marshmallow.
