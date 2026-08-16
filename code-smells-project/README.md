# code-smells-project

API RESTful de E-commerce em Python/Flask, refatorada a partir de uma base de código monolítica (code smells e anti-patterns) para o padrão arquitetural **MVC em camadas com Service Layer**, em conformidade com o desafio `refactor-arch`.

---

## 1. Visão Geral e Estado Atual do Projeto

O projeto passou por uma refatoração arquitetural completa e saneamento de segurança (v2.0.0):
- **Arquitetura em Camadas:** Separação estrita de responsabilidades entre Views (Rotas), Controllers (Adapters HTTP), Services (Regras de Negócio e Domínio) e Models (Persistência e Mappers).
- **Segurança da Informação:** Eliminação de injeção de SQL via queries 100% parametrizadas (`?`), hashing seguro de senhas com Werkzeug (`scrypt`/`pbkdf2`), proteção contra vazamento de senhas em endpoints e remoção de endpoints administrativos inseguros (`/admin/query`).
- **Gerenciamento de Recursos:** Conexões com banco SQLite gerenciadas por ciclo de vida da requisição via Flask `g` (`teardown_appcontext`) e eliminação de queries N+1 no carregamento de pedidos e itens.
- **Configuração 12-Factor:** Configurações e segredos externalizados via variáveis de ambiente com validação centralizada.

---

## 2. Tecnologias e Stack

| Camada | Tecnologia | Versão / Detalhes |
|--------|------------|-------------------|
| Linguagem | Python | 3.12+ (compatível com 3.14) |
| Framework Web | Flask | 3.1.1 (App Factory em `src/app.py`) |
| CORS | flask-cors | 5.0.1 |
| Banco de Dados | SQLite | Conexão escopada por requisição (`g.db`) |
| Persistência | sqlite3 | Queries SQL parametrizadas sem ORM |
| Segurança de Senhas | Werkzeug Security | Hashes com salt at rest |
| Testes Automatizados | pytest | `tests/unit`, `tests/integration` (9 testes ativos) |

---

## 3. Como Executar

### Pré-requisitos
- Python 3.12+
- `uv` (recomendado) ou `pip` / `venv`

### Opção A: Utilizando `venv` e `pip`

```bash
# 1. Clonar ou acessar o diretório
cd code-smells-project

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Executar a aplicação
python app.py
```

### Opção B: Utilizando `uv`

```bash
uv sync
uv run python app.py
```

A API iniciará no endereço `http://127.0.0.1:5003`. O banco de dados SQLite (`loja.db`) é inicializado e populado automaticamente com produtos e usuários no boot da aplicação.

---

## 4. Variáveis de Ambiente

Todas as configurações podem ser sobrescritas via variáveis de ambiente:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | `dev-only-change-me` | Chave secreta da aplicação Flask |
| `FLASK_DEBUG` | `0` | `1` para modo debug ativo |
| `HOST` | `127.0.0.1` | Endereço de bind do servidor |
| `PORT` | `5003` | Porta de escuta HTTP |
| `DB_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `AMBIENTE` | `desenvolvimento` | Identificador de ambiente exibido no `/health` |
| `ADMIN_TOKEN` | _(vazio)_ | Token exigido no header `X-Admin-Token` para `POST /admin/reset-db` |

---

## 5. Estrutura do Repositório

```text
code-smells-project/
├── app.py                     # Entrypoint de execução
├── pyproject.toml             # Metadados e configuração do projeto
├── requirements.txt           # Dependências de produção
├── requirements-dev.txt       # Dependências de desenvolvimento (pytest, ruff)
├── AGENTS.md                  # Diretrizes operacionais para agentes IA
├── README.md                  # Documentação principal
├── docs/                      # Relatórios da skill refactor-arch e Playbook
│   ├── project_analysis.txt   # Fase 1: Análise de Stack e Arquitetura inicial
│   ├── project_issues.txt     # Fase 2: Diagnóstico de Code Smells e Riscos
│   ├── project_refactored.txt # Fase 3: Resumo das transformações aplicadas
│   └── playbook_refatoracao.md# Playbook com os 8 padrões de transformação
├── src/                       # Código-fonte refatorado (MVC + Services)
│   ├── app.py                 # App factory (create_app) e registro de rotas
│   ├── config/                # Módulo de configurações e Settings
│   │   └── settings.py
│   ├── controllers/           # Adaptadores HTTP (request/response/status)
│   │   ├── health_controller.py
│   │   ├── pedido_controller.py
│   │   ├── produto_controller.py
│   │   ├── relatorio_controller.py
│   │   └── usuario_controller.py
│   ├── db/                    # Inicialização, schema DDL, seed e lifecycle
│   │   └── database.py
│   ├── middlewares/           # Handlers centralizados de exceções HTTP
│   │   └── error_handler.py
│   ├── models/                # Persistência SQL parametrizada e mappers
│   │   ├── mappers.py
│   │   ├── pedido_model.py
│   │   ├── produto_model.py
│   │   ├── relatorio_model.py
│   │   └── usuario_model.py
│   ├── services/              # Camada de regras de negócio puras
│   │   ├── errors.py
│   │   ├── notificacao_service.py
│   │   ├── pedido_service.py
│   │   ├── produto_service.py
│   │   ├── relatorio_service.py
│   │   └── usuario_service.py
│   └── views/                 # Registro e roteamento de Blueprints
│       └── routes.py
└── tests/                     # Suíte de testes automatizados
    ├── conftest.py
    ├── integration/           # Testes de integração de rotas e segurança
    │   └── test_api.py
    └── unit/                  # Testes unitários de serviços
        └── test_relatorio_service.py
```

---

## 6. Arquitetura em Camadas (MVC + Services)

O fluxo de processamento de cada requisição segue o ciclo abaixo:

```text
HTTP Client
    |
    v
View (`src/views/routes.py`)
    |  (Roteamento de URL para Controller)
    v
Controller (`src/controllers/`)
    |  (Parsing de parâmetros, validação de formato e status HTTP)
    v
Service (`src/services/`)
    |  (Regras de negócio, descontos, validação de estoque, regras de autenticação)
    v
Model (`src/models/`)
    |  (Queries SQL parametrizadas com placeholders '?')
    v
Database (`src/db/database.py`)
    |  (Conexão SQLite via Flask 'g' por ciclo de requisição)
    v
`loja.db`
```

---

## 7. Superfície de API (Endpoints)

Base URL: `http://127.0.0.1:5003`

### Rotas Públicas e Operacionais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Informações básicas da API e status |
| `GET` | `/health` | Healthcheck com status, contagem de tabelas e versão (sem segredos) |

### Produtos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/produtos` | Lista produtos (filtros opcionais: `categoria`, `busca`) |
| `GET` | `/produtos/<id>` | Detalhes de um produto específico |
| `POST` | `/produtos` | Criação de novo produto |
| `PUT` | `/produtos/<id>` | Atualização de produto existente |
| `DELETE` | `/produtos/<id>` | Remoção de produto |

### Usuários e Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/usuarios` | Lista usuários (senhas omitidas) |
| `GET` | `/usuarios/<id>` | Detalhes de um usuário específico (senhas omitidas) |
| `POST` | `/usuarios` | Cadastro de novo usuário com senha hasheada |
| `POST` | `/login` | Autenticação com e-mail e senha via verificação de hash |

### Pedidos e Vendas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/pedidos` | Lista pedidos com itens carregados em consulta otimizada (sem N+1) |
| `GET` | `/pedidos/<id>` | Detalhes de um pedido específico com seus itens |
| `POST` | `/pedidos` | Criação de pedido com validação de estoque e cálculo de total |
| `PUT` | `/pedidos/<id>/status` | Atualização de status (`pendente`, `aprovado`, `enviado`, `entregue`, `cancelado`) |
| `GET` | `/relatorios/vendas` | Relatório consolidado com cálculo de descontos por faixa e métricas |

### Administração

| Método | Endpoint | Requisitos e Comportamento |
|--------|----------|----------------------------|
| `POST` | `/admin/query` | **REMOVIDO DEFINITIVAMENTE** por razões de segurança (execução arbitrária de SQL) |
| `POST` | `/admin/reset-db` | Reset e re-seeding do banco. Exige header `X-Admin-Token: <ADMIN_TOKEN>` |

---

## 8. Dados de Seed (Desenvolvimento)

Ao iniciar pela primeira vez, o banco é populado com as seguintes credenciais padrão (senhas armazenadas com hash):

| E-mail | Senha (Plaintext) | Tipo / Permissão |
|--------|-------------------|------------------|
| `admin@loja.com` | `admin123` | `admin` |
| `joao@email.com` | `123456` | `cliente` |
| `maria@email.com` | `senha123` | `cliente` |

Categorias padrão: `informatica`, `moveis`, `vestuario`, `geral`, `eletronicos`, `livros`.

---

## 9. Execução de Testes Automatizados

A suíte inclui testes unitários e de integração validando integridade de regras, sanitização SQL, prevenção de vazamento de segredos e endpoints administrativos:

```bash
# Executar suíte completa de testes
pytest -v

# Executar com saída resumida
pytest -q
```

---

## 10. Documentação e Relatórios de Refatoração

Os documentos gerados durante o ciclo de refatoração encontram-se na pasta [`docs/`](./docs/):
- [`docs/project_analysis.txt`](./docs/project_analysis.txt): Análise inicial de stack e problemas arquiteturais.
- [`docs/project_issues.txt`](./docs/project_issues.txt): Diagnóstico detalhado de code smells classificados por severidade.
- [`docs/project_refactored.txt`](./docs/project_refactored.txt): Relatório de validação e fechamento da refatoração.
- [`docs/playbook_refatoracao.md`](./docs/playbook_refatoracao.md): Playbook com os 8 padrões de transformação aplicados.
