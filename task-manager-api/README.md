# task-manager-api

API de Gerenciamento de Tarefas desenvolvida em Python e Flask, completamente refatorada para o padrão arquitetural **MVC (Model-View-Controller)** com camada de **Serviços de Integração**, validação de contratos via **Schemas (Marshmallow)**, persistência relacional com **SQLAlchemy ORM** e configuração baseada em **12-Factor App**.

---

## Visão Geral

- **Runtime:** Python 3.10+ (otimizado para Python 3.12/3.14)
- **Framework Web:** Flask 3.0+
- **ORM / Persistência:** Flask-SQLAlchemy 3+ / SQLite (`tasks.db`)
- **Validação e Serialização:** Marshmallow 3+
- **Autenticação:** Tokens assinados criptograficamente via `itsdangerous.URLSafeTimedSerializer`
- **Criptografia de Senhas:** `werkzeug.security` (hashing com salt via Scrypt/PBKDF2)
- **Integração de Notificações:** `NotificationService` com suporte a envio SMTP parametrizado
- **Arquitetura:** MVC + Services + Schemas (DTO) + Centralized Error Middleware + Application Factory

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
│   ├── category_controller.py     # CRUD e integridade de categorias
│   ├── report_controller.py       # Agregações de relatórios gerenciais e por usuário
│   ├── task_controller.py         # Gerenciamento de tarefas, filtros e Eager Loading
│   └── user_controller.py         # CRUD de usuários e consulta de tarefas por usuário
├── schemas/                       # Camada Schema (DTO): validação de entrada e serialização
│   ├── category_schema.py         # Schemas de criação e atualização de categorias
│   ├── task_schema.py             # Schemas de criação e atualização de tarefas
│   └── user_schema.py             # Schemas de criação, atualização e login de usuários
├── services/                      # Camada Service: regras de domínio e integrações externas
│   └── notification_service.py    # Envio de notificações de atribuição/atraso via SMTP
├── middlewares/                   # Camada Middleware: tratamento transversal e observabilidade
│   └── error_handler.py           # Classe AppError, tratadores de erro globais e logging
├── utils/
│   └── helpers.py                 # Funções auxiliares (validação de cores hexadecimais)
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
| **Controller** | `controllers/` | Orquestração do caso de uso | Coordenação de fluxo, regras de negócio, transações (`db.session.commit()`), chamadas a serviços |
| **Service** | `services/` | Regras de integração e efeitos colaterais | Comunicação externa (envio de emails SMTP), desacoplado de requests HTTP |
| **Model** | `models/` | Entidades de domínio e persistência ORM | Mapeamento de tabelas, relacionamentos, métodos de entidade (`is_overdue()`, `check_password()`) |
| **Schema** | `schemas/` | Validação de entrada e DTO | Regras de validação (tamanho, formato, obrigatoriedade), tipagem, campos `load_only` |
| **Middleware** | `middlewares/` | Tratamento transversal de erros | Handler de exceções (`AppError`, `ValidationError`, `IntegrityError`, 500), logging estruturado |
| **Config** | `config/` | Configurações do ambiente | Leitura de variáveis de ambiente (`os.getenv`), constantes padrão seguras |

---

## Variáveis de Ambiente

As configurações são gerenciadas em [config/settings.py](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/task-manager-api/config/settings.py) e podem ser personalizadas via arquivo `.env`:

| Variável | Padrão | Descrição |
|---|---|---|
| `HOST` | `127.0.0.1` | Endereço de bind da aplicação |
| `PORT` | `5000` | Porta do servidor HTTP |
| `DEBUG` | `0` | Modo debug do Flask (`1` para ativo, `0` para inativo) |
| `SECRET_KEY` | `dev-secret-key-change-in-prod` | Chave de criptografia para assinatura de tokens e sessão |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI de conexão do SQLAlchemy |
| `TOKEN_MAX_AGE_SECONDS` | `86400` | Tempo de expiração do token de autenticação (em segundos) |
| `SMTP_HOST` | `smtp.gmail.com` | Servidor SMTP para envio de notificações |
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
| Maria Souza | `maria@email.com` | `abcd1234` | `user` |
| Pedro Santos | `pedro@email.com` | `pass1234` | `manager` |

---

## Endpoints da API

### 1. Sistema e Health Check
- `GET /` — Mensagem de boas-vindas e versão da API.
- `GET /health` — Status de operação e timestamp ISO UTC.

### 2. Autenticação
- `POST /login` — Autenticação de usuário com email e senha. Retorna dados do usuário e token assinado (`token`).

### 3. Gerenciamento de Usuários
- `GET /users` — Lista todos os usuários ativos (com contagem de tarefas associadas).
- `GET /users/<id>` — Detalha um usuário específico.
- `POST /users` — Cria um novo usuário com validação de email e senha forte.
- `PUT /users/<id>` — Atualiza dados cadastrais de um usuário.
- `DELETE /users/<id>` — Remove um usuário da base.
- `GET /users/<id>/tasks` — Lista todas as tarefas atribuídas ao usuário.

### 4. Gerenciamento de Tarefas
- `GET /tasks` — Lista tarefas com Eager Loading (`joinedload` de usuário e categoria) e cálculo de atraso (`overdue`).
- `GET /tasks/<id>` — Detalha uma tarefa específica com seus relacionamentos.
- `POST /tasks` — Cria uma nova tarefa e dispara notificação de atribuição se configurado.
- `PUT /tasks/<id>` — Atualiza dados, status, prioridade ou prazo de uma tarefa.
- `DELETE /tasks/<id>` — Remove uma tarefa.
- `GET /tasks/search?q=...&status=...&priority=...` — Busca textual em títulos/descrições e filtros compostos.
- `GET /tasks/stats` — Estatísticas agregadas de tarefas por status e tarefas atrasadas.

### 5. Gerenciamento de Categorias
- `GET /categories` — Lista todas as categorias cadastradas.
- `POST /categories` — Cria uma nova categoria com validação de cor hexadecimal.
- `PUT /categories/<id>` — Atualiza nome, descrição ou cor da categoria.
- `DELETE /categories/<id>` — Remove uma categoria.

### 6. Relatórios
- `GET /reports/summary` — Relatório executivo consolidado com métricas de usuários, tarefas e categorias.
- `GET /reports/user/<id>` — Relatório analítico detalhado do volume e status de tarefas por usuário.

---

## Exemplos de Requisições (curl)

```bash
# Health Check
curl -s http://localhost:5000/health

# Login
curl -s -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"12345678"}'

# Listar Tarefas (com relações carregadas sem N+1)
curl -s http://localhost:5000/tasks

# Criar Nova Tarefa
curl -s -X POST http://localhost:5000/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Configurar pipeline de CI/CD",
    "description": "Implementar GitHub Actions para testes e build",
    "priority": 4,
    "status": "in_progress",
    "user_id": 1,
    "category_id": 1,
    "due_date": "2026-12-31T23:59:59Z"
  }'

# Estatísticas de Tarefas
curl -s http://localhost:5000/tasks/stats

# Relatório Gerencial Consolidado
curl -s http://localhost:5000/reports/summary
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
