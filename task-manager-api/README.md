# task-manager-api

API de Gerenciamento de Tarefas desenvolvida em Python e Flask, refatorada para o padrão arquitetural **MVC (Model-View-Controller)** com camada de **Serviços de Integração**, validação de contratos via **Schemas (Marshmallow)**, **autenticação/autorização obrigatórias via middleware** (`token_required` / `role_required`), transações ACID com rollback automático, persistência relacional com **SQLAlchemy ORM** e configuração baseada em **12-Factor App** (segredo obrigatório com fail-fast em produção).

---

## Visão Geral

- **Runtime:** Python 3.10+ (otimizado para Python 3.12/3.14)
- **Framework Web:** Flask 3.0+
- **ORM / Persistência:** Flask-SQLAlchemy 3+ / SQLite (`tasks.db`)
- **Validação e Serialização:** Marshmallow 3+
- **Autenticação:** Tokens assinados criptograficamente via `itsdangerous.URLSafeTimedSerializer`, **obrigatoriamente validados** pelos decorators `token_required` / `role_required` (`middlewares/auth.py`) em todos os endpoints protegidos
- **Autorização:** Matriz de acesso por role (`user`, `manager`, `admin`) + regras de propriedade (self-or-admin) na camada Controller
- **Criptografia de Senhas:** `werkzeug.security` (hashing com salt via Scrypt/PBKDF2)
- **Integração de Notificações:** `NotificationService` com suporte a envio SMTP parametrizado
- **Transações:** Helper `database.transaction()` com commit/rollback automático em todas as escritas
- **Arquitetura:** MVC + Services + Schemas (DTO) + Centralized Error Middleware + Auth Middleware + Application Factory

---

## Estrutura do Projeto

```text
task-manager-api/
├── app.py                         # Application Factory (create_app) e Composition Root
├── database.py                    # Instanciação centralizada do SQLAlchemy (db)
├── seed.py                        # Script de inicialização e carga de dados de teste
├── config/
│   └── settings.py                # Configurações centralizadas via variáveis de ambiente
├── models/                        # Camada Model: entidades de domínio e persistência ORM
│   ├── category.py                # Entidade Category
│   ├── task.py                    # Entidade Task (com método de domínio is_overdue)
│   └── user.py                    # Entidade User (hashing seguro e to_dict sem senhas)
├── views/                         # Camada View: Blueprints HTTP finos e roteamento
│   ├── category_views.py          # Rotas de categorias (/categories)
│   ├── health_views.py            # Rotas de health check (/health e /)
│   ├── report_views.py            # Rotas de relatórios (/reports)
│   ├── task_views.py              # Rotas de tarefas (/tasks)
│   └── user_views.py              # Rotas de usuários e autenticação (/users e /login)
├── controllers/                   # Camada Controller: orquestração de casos de uso e transações
│   ├── auth_controller.py         # Login e emissão/validação de tokens assinados
│   ├── category_controller.py     # CRUD e integridade de categorias (nullify em cascade)
│   ├── report_controller.py       # Agregações de relatórios gerenciais e por usuário (GROUP BY único)
│   ├── task_controller.py         # Gerenciamento de tarefas, filtros, paginação e Eager Loading
│   ├── user_authz.py              # Regras de autorização (self-or-admin, role escalation)
│   └── user_controller.py         # CRUD de usuários, regras self-or-admin e consulta de tarefas
├── schemas/                       # Camada Schema (DTO): validação de entrada e serialização de resposta
│   ├── category_schema.py         # Schemas de criação, atualização e resposta de categorias
│   ├── common_schema.py           # PaginationSchema (page/per_page validado)
│   ├── task_schema.py             # Schemas de criação, atualização, busca e resposta de tarefas
│   └── user_schema.py             # Schemas de criação, atualização, login e resposta de usuários
├── services/                      # Camada Service: regras de domínio e integrações externas
│   └── notification_service.py    # Envio de notificações de atribuição/atraso via SMTP
├── middlewares/                   # Camada Middleware: tratamento transversal e observabilidade
│   ├── auth.py                    # Guards token_required / role_required e helpers de sessão
│   └── error_handler.py           # Classe AppError, tratadores de erro globais (com rollback) e logging
├── utils/
│   ├── helpers.py                 # Funções auxiliares puras (tags, datas, percentuais)
│   └── time.py                    # Fonte única de tempo UTC (utcnow / as_utc)
├── docs/                          # Relatórios da refatoração e documentação arquitetural
│   ├── playbook_refatoracao.md    # Playbook com os 8 padrões de transformação (Antes/Depois)
│   ├── project_analysis.txt       # Relatório Fase 1 (Stack & Arquitetura)
│   ├── project_issues.txt         # Relatório Fase 2 (Code Smells & Anti-patterns)
│   ├── project_refactored.txt     # Relatório Fase 3 (Resultado da Refatoração)
│   └── summary.md                 # Resumo executivo da refatoração
├── .cursor/skills/refactor-arch/  # Skill de automação e auditoria arquitetural
│   ├── SKILL.md                   # Definição do workflow em 4 fases
│   └── references/
│       ├── anti_patterns_catalog.md # Catálogo de anti-patterns e taxonomia
│       └── issues_severity.md     # Guia de severidade e matriz de decisão
├── .env.example                   # Modelo versionado de variáveis de ambiente
├── requirements.txt               # Dependências do projeto
├── AGENTS.md                      # Diretrizes e regras para agentes de IA
└── README.md
```

---

## Camadas Arquiteturais e Responsabilidades

| Camada | Diretório | Responsabilidade Principal | O que DEVE Conter |
|---|---|---|---|
| **View** | `views/` | Ponto de entrada HTTP e formatação | Blueprints, extração de parâmetros de request, delegação para Controller/Schema, retorno `jsonify` com status code |
| **Controller** | `controllers/` | Orquestração do caso de uso | Coordenação de fluxo, regras de negócio, autorização, transações via `transaction()`, chamadas a serviços |
| **Service** | `services/` | Regras de integração e efeitos colaterais | Comunicação externa (envio de emails SMTP), desacoplado de requests HTTP |
| **Model** | `models/` | Entidades de domínio e persistência ORM | Mapeamento de tabelas, relacionamentos, métodos de entidade (`is_overdue()`, `check_password()`) |
| **Schema** | `schemas/` | Validação de entrada e DTO | Regras de validação (tamanho, formato, obrigatoriedade), tipagem, campos `load_only` |
| **Middleware** | `middlewares/` | Tratamento transversal de erros e autenticação | Guards de acesso (`token_required`, `role_required`), handlers de exceções (`AppError`, `ValidationError`, `IntegrityError` com rollback, 404, 500), logging estruturado |
| **Config** | `config/` | Configurações do ambiente | Leitura de variáveis de ambiente (`os.getenv`), constantes padrão seguras |

---

## Variáveis de Ambiente

As configurações são gerenciadas em [config/settings.py](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/config/settings.py) e podem ser personalizadas via arquivo `.env`:

| Variável | Padrão | Descrição |
|---|---|---|
| `HOST` | `0.0.0.0` | Endereço de bind da aplicação |
| `PORT` | `5000` | Porta do servidor HTTP |
| `FLASK_DEBUG` | `0` | Modo debug do Flask (`1` para ativo, `0` para inativo) |
| `SECRET_KEY` | *(vazio)* | Chave de assinatura de tokens. **Obrigatória em produção** — a aplicação não sobe com chave ausente/fraca (fail-fast). Em `DEBUG`/`TESTS`, uma chave efêmera é gerada com warning. Gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI de conexão do SQLAlchemy |
| `TOKEN_MAX_AGE_SECONDS` | `86400` | Tempo de expiração do token de autenticação (em segundos) |
| `DEFAULT_PER_PAGE` | `20` | Tamanho de página padrão dos endpoints paginados |
| `MAX_PER_PAGE` | `100` | Máximo permitido por página |
| `SMTP_HOST` | `""` | Servidor SMTP para envio de notificações |
| `SMTP_PORT` | `587` | Porta do servidor SMTP |
| `SMTP_USER` | `""` | Usuário do servidor SMTP |
| `SMTP_PASSWORD` | `""` | Senha do servidor SMTP |
| `SMTP_ENABLED` | `0` | Habilita envio de e-mails (`1` para habilitar, `0` para desabilitar) |

---

## Instalação e Execução

### Pré-requisitos
- Python 3.10+ instalado
- Virtualenv (`venv`)

### Passo a Passo

```bash
# 1. Acessar o diretório do projeto
cd task-manager-api

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env

# 5. Popular o banco de dados inicial
python seed.py

# 6. Iniciar o servidor
python app.py
```

A aplicação estará disponível em `http://localhost:5000`.

---

## Usuários de Demonstração (Seed)

O script [seed.py](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/seed.py) popula a base com usuários de teste criptografados com senhas seguras (mínimo 8 caracteres):

| Nome | Email | Senha | Role |
|---|---|---|---|
| João Silva | `joao@email.com` | `12345678` | `admin` |
| Maria Santos | `maria@email.com` | `abcd1234` | `user` |
| Pedro Oliveira | `pedro@email.com` | `pass1234` | `manager` |

---

## Autenticação e Autorização

Endpoints protegidos exigem o header `Authorization: Bearer <token>`, obtido via `POST /login` (token assinado com expiração configurável). Requisições sem token válido respondem `401`; sem permissão de role, `403`.

**Matriz de acesso:**

| Scope | Público | `user` autenticado | `manager` | `admin` |
|---|---|---|---|---|
| `GET /`, `GET /health`, `POST /login`, `POST /users` (cadastro) | ✅ | ✅ | ✅ | ✅ |
| `/tasks/*` (CRUD, busca, stats) | — | ✅ | ✅ | ✅ |
| `GET /users/<id>`, `PUT /users/<id>`, `GET /users/<id>/tasks` (próprio) | — | ✅ | ✅ | ✅ (qualquer um) |
| `GET /users`, `DELETE /users/<id>` | — | — | — | ✅ |
| Escrita em `/categories/*` (POST/PUT/DELETE) | — | — | ✅ | ✅ |
| `GET /categories` | — | ✅ | ✅ | ✅ |
| `/reports/*` | — | — | ✅ | ✅ |

**Paginação:** `GET /tasks`, `GET /users` e `GET /tasks/search` retornam o envelope `{items, page, per_page, total, pages}` com `?page=` e `?per_page=` (máx. `MAX_PER_PAGE`). Parâmetros inválidos respondem `400`.

## Endpoints da API

### 1. Sistema e Health Check
- `GET /` — Mensagem de boas-vindas e versão da API.
- `GET /health` — Status de operação e timestamp ISO UTC.

### 2. Autenticação
- `POST /login` — Autenticação de usuário com email e senha. Retorna dados do usuário e token assinado (`token`).

### 3. Gerenciamento de Usuários
- `GET /users` — **[admin]** Lista paginada de usuários com contagem de tarefas agregada em uma única query.
- `GET /users/<id>` — **[self|admin]** Detalha um usuário específico.
- `POST /users` — Cria um novo usuário com validação de email e senha forte (público).
- `PUT /users/<id>` — **[self|admin]** Atualiza dados cadastrais; alteração de `role` é exclusiva de admin.
- `DELETE /users/<id>` — **[admin]** Remove usuário e suas tarefas em transação atômica.
- `GET /users/<id>/tasks` — **[self|admin]** Lista tarefas atribuídas ao usuário.

### 4. Gerenciamento de Tarefas (autenticado)
- `GET /tasks` — Lista paginada com Eager Loading (`joinedload` de usuário e categoria) e cálculo de atraso (`overdue`).
- `GET /tasks/<id>` — Detalha uma tarefa específica com seus relacionamentos.
- `POST /tasks` — Cria uma nova tarefa e dispara notificação de atribuição se configurado.
- `PUT /tasks/<id>` — Atualiza dados, status, prioridade ou prazo de uma tarefa.
- `DELETE /tasks/<id>` — Remove uma tarefa.
- `GET /tasks/search?q=...&status=...&priority=...&user_id=...` — Busca textual e filtros compostos (validados via schema, paginados).
- `GET /tasks/stats` — Estatísticas agregadas por status/atraso em consultas `GROUP BY` únicas.

### 5. Gerenciamento de Categorias
- `GET /categories` — **[autenticado]** Lista categorias com contagem de tarefas agregada em uma única query.
- `POST /categories` — **[admin|manager]** Cria categoria com validação de cor hexadecimal.
- `PUT /categories/<id>` — **[admin|manager]** Atualiza nome, descrição ou cor.
- `DELETE /categories/<id>` — **[admin|manager]** Remove a categoria e desvincula (NULL) as tarefas associadas na mesma transação — sem deixar referências órfãs.

### 6. Relatórios
- `GET /reports/summary` — **[admin|manager]** Relatório executivo consolidado (agregações SQL, sem full-table loads).
- `GET /reports/user/<id>` — **[admin|manager]** Relatório analítico de volume e status de tarefas por usuário.

---

## Exemplos de Requisições (curl)

```bash
# Health Check (público)
curl -s http://localhost:5000/health

# Login → extrai o token
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"12345678"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Listar Tarefas paginadas (com relações carregadas sem N+1)
curl -s "http://localhost:5000/tasks?page=1&per_page=20" \
  -H "Authorization: Bearer $TOKEN"

# Criar Nova Tarefa
curl -s -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Configurar pipeline de CI/CD",
    "description": "Implementar GitHub Actions para testes e build",
    "priority": 4,
    "status": "in_progress",
    "user_id": 1,
    "category_id": 1,
    "due_date": "2026-12-31"
  }'

# Estatísticas de Tarefas
curl -s http://localhost:5000/tasks/stats -H "Authorization: Bearer $TOKEN"

# Relatório Gerencial Consolidado (role admin/manager)
curl -s http://localhost:5000/reports/summary -H "Authorization: Bearer $TOKEN"
```

---

## Documentação Arquitetural e Auditoria

Para detalhes aprofundados sobre a refatoração e padrões implementados:

- **Playbook de Refatoração:** [docs/playbook_refatoracao.md](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/docs/playbook_refatoracao.md) detalha os 8 padrões de transformação com exemplos de código antes e depois.
- **Relatório de Análise Inicial (Fase 1):** [docs/project_analysis.txt](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/docs/project_analysis.txt).
- **Relatório de Diagnóstico de Code Smells (Fase 2):** [docs/project_issues.txt](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/docs/project_issues.txt).
- **Relatório de Conclusão da Refatoração (Fase 3):** [docs/project_refactored.txt](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/docs/project_refactored.txt).
- **Resumo Executivo da Refatoração:** [docs/summary.md](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/docs/summary.md).
- **Catálogo de Anti-Patterns e Guia MVC:** [.cursor/skills/refactor-arch/references/anti_patterns_catalog.md](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/.cursor/skills/refactor-arch/references/anti_patterns_catalog.md).
- **Guia de Severidade de Problemas:** [.cursor/skills/refactor-arch/references/issues_severity.md](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/.cursor/skills/refactor-arch/references/issues_severity.md).
- **Diretrizes para Agentes de IA:** [AGENTS.md](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/AGENTS.md).
