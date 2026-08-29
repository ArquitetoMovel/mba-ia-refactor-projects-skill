# Architecture Audit Report — Project 1: code-smells-project

**Stack:** Python 3 + Flask 3.1.1 + SQLite (`loja.db`)  
**Domain:** E-commerce RESTful API (produtos, pedidos, usuários, relatórios de vendas)  
**Execution Phase:** Phase 2 (Code Smells & Architecture Issues Detection)  
**Skill:** `refactor-arch`

---

## 1. Summary of Findings

| Severity | Count | Primary Impact Areas |
|----------|-------|----------------------|
| **CRITICAL** | 5 | SQL Injection, Arbitrary SQL Execution, Unauthenticated DB Reset, Plaintext Credentials Leakage, God Class/Module |
| **HIGH** | 5 | Broken MVC, Business Logic in Controllers, Global Mutable DB Connection, Tight Coupling, N+1 Queries |
| **MEDIUM** | 4 | Duplicated Code, Long Methods, Generic Error Handling / Leaked Exceptions, Weak Input Validation |
| **LOW** | 3 | Magic Numbers in Discounts, Port/Config Inconsistencies, Unused Imports |
| **TOTAL** | **17** | **Exceeds minimum threshold (≥ 5 findings)** |

---

## 2. Detailed Findings (Ordered by Severity)

### [CRITICAL] SQL Injection via String Concatenation
- **Location:**
  - `file: models.py`; `line: 24-28`; `symbol: get_produto_por_id`
  - `file: models.py`; `line: 43-50`; `symbol: criar_produto`
  - `file: models.py`; `line: 54-61`; `symbol: atualizar_produto`
  - `file: models.py`; `line: 65-68`; `symbol: deletar_produto`
  - `file: models.py`; `line: 89-92`; `symbol: get_usuario_por_id`
  - `file: models.py`; `line: 105-111`; `symbol: login_usuario`
  - `file: models.py`; `line: 122-129`; `symbol: criar_usuario`
  - `file: models.py`; `line: 133-169`; `symbol: criar_pedido`
  - `file: models.py`; `line: 171-201`; `symbol: get_pedidos_usuario`
  - `file: models.py`; `line: 203-233`; `symbol: get_todos_pedidos`
  - `file: models.py`; `line: 275-283`; `symbol: atualizar_status_pedido`
  - `file: models.py`; `line: 285-299`; `symbol: buscar_produtos`
- **Description:** Queries SQL construídas concatenando strings com dados fornecidos diretamente pelo usuário sem uso de queries parametrizadas (`?`).
- **Impact:** Permite evasão de autenticação, extração integral de dados, bypass de estoque e alteração arbitrária da base.
- **Recommendation:** Substituir todas as queries por queries 100% parametrizadas com placeholders `?` e cursores do SQLite.

### [CRITICAL] Arbitrary SQL Execution Endpoint (`POST /admin/query`)
- **Location:**
  - `file: app.py`; `line: 59-78`; `symbol: executar_query`
- **Description:** Rota administrativa pública que aceita strings SQL arbitrárias no corpo da requisição JSON e as executa diretamente no banco sem autenticação.
- **Impact:** RCE equivalente no banco de dados com poder de leitura, escrita e exclusão DDL irrestrita.
- **Recommendation:** Remover permanentemente o endpoint da aplicação.

### [CRITICAL] Unauthenticated Destructive Database Reset (`POST /admin/reset-db`)
- **Location:**
  - `file: app.py`; `line: 47-57`; `symbol: reset_database`
- **Description:** Endpoint que apaga todas as tabelas e dados do banco sem autenticação ou confirmação de token.
- **Impact:** Negação de serviço e perda irreversível de dados por agentes maliciosos.
- **Recommendation:** Proteger o endpoint exigindo header `X-Admin-Token` configurado via variável de ambiente `ADMIN_TOKEN`.

### [CRITICAL] Plaintext Credentials & Secrets Exposure
- **Location:**
  - `file: app.py`; `line: 7-7`; `symbol: SECRET_KEY`
  - `file: controllers.py`; `line: 264-290`; `symbol: health_check`
  - `file: database.py`; `line: 75-82`; `symbol: plaintext user seed`
  - `file: models.py`; `line: 72-87`; `symbol: get_todos_usuarios`
  - `file: models.py`; `line: 89-103`; `symbol: get_usuario_por_id`
- **Description:** Chave secreta embutida no código, senhas salvas em texto puro sem salt/hash e vazamento do hash/senha em endpoints de listagem de usuários e health check.
- **Impact:** Comprometimento total de contas de usuários e administradores.
- **Recommendation:** Externalizar `SECRET_KEY` para variáveis de ambiente, adotar hashing forte via Werkzeug (`generate_password_hash`/`check_password_hash`) e sanitizar saídas HTTP.

### [CRITICAL] God Object / God Module (`models.py`)
- **Location:**
  - `file: models.py`; `line: 1-314`; `symbol: module`
- **Description:** Arquivo único contendo persistência SQL, regras de estoque, cálculos de faturamento, autenticação, mappers de dados e envio de notificações para 4 domínios diferentes.
- **Impact:** Violação severa de SRP (Single Responsibility Principle), impossibilidade de testes unitários isolados e alto risco de regressão.
- **Recommendation:** Decompor em models (`produto_model.py`, `usuario_model.py`, `pedido_model.py`, `relatorio_model.py`) e serviços de domínio dedicados.

### [HIGH] Lack of Separation of Concerns (Quebra de MVC)
- **Location:**
  - `file: app.py`; `line: 1-88`; `symbol: application bootstrap and routes`
  - `file: controllers.py`; `line: 1-292`; `symbol: HTTP handlers`
  - `file: models.py`; `line: 1-314`; `symbol: persistence and domain logic`
  - `file: database.py`; `line: 1-86`; `symbol: connection, schema, and seed`
- **Description:** Controladores contendo regras de negócio e validações; models contendo lógica de desconto e SQL; ausência de camada de serviços e ausência de desacoplamento.
- **Recommendation:** Reestruturar em Views (rotas e status HTTP), Controllers (adaptadores), Services (regras de negócio) e Models (persistência).

### [HIGH] Business Logic & Side Effects in Controllers
- **Location:**
  - `file: controllers.py`; `line: 24-62`; `symbol: criar_produto`
  - `file: controllers.py`; `line: 64-96`; `symbol: atualizar_produto`
  - `file: controllers.py`; `line: 188-220`; `symbol: criar_pedido`
  - `file: controllers.py`; `line: 237-255`; `symbol: atualizar_status_pedido`
- **Description:** Notificações mockadas (e-mail, SMS, push) e validações de regras de catálogo acopladas diretamente nos manipuladores HTTP.
- **Recommendation:** Extrair para `services/notificacao_service.py` e `services/produto_service.py`.

### [HIGH] Global Mutable Database Connection
- **Location:**
  - `file: database.py`; `line: 4-12`; `symbol: db_connection/get_db`
- **Description:** Objeto de conexão SQLite único e global compartilhado com `check_same_thread=False`.
- **Recommendation:** Gerenciar conexões por ciclo de vida de requisição usando o contexto `flask.g` com fechamento automático em `teardown_appcontext`.

### [HIGH] Tight Coupling without Dependency Injection
- **Location:**
  - `file: controllers.py`; `line: 1-3`; `symbol: direct models/database imports`
- **Description:** Acoplamento estático e direto impedindo mock e testes unitários independentes.
- **Recommendation:** Estruturar controllers e services com injeção de dependências em `deps.py`.

### [HIGH] N+1 Query Antipattern
- **Location:**
  - `file: models.py`; `line: 171-201`; `symbol: get_pedidos_usuario`
  - `file: models.py`; `line: 203-233`; `symbol: get_todos_pedidos`
- **Description:** Para cada pedido retornado, uma query secundária é executada para buscar `itens_pedido` e outra para `produtos`.
- **Recommendation:** Utilizar queries otimizadas com `JOIN` agrupando itens de pedido em uma única consulta.

### [MEDIUM] Duplicated Code
- **Location:**
  - `file: controllers.py`; `line: 24-54`; `symbol: criar_produto validation`
  - `file: controllers.py`; `line: 64-90`; `symbol: atualizar_produto validation`
  - `file: models.py`; `line: 4-22`; `symbol: produto row mapper`
  - `file: models.py`; `line: 31-40`; `symbol: produto row mapper`
  - `file: models.py`; `line: 72-87`; `symbol: usuario list mapper`
  - `file: models.py`; `line: 89-103`; `symbol: usuario detail mapper`
  - `file: models.py`; `line: 114-119`; `symbol: login mapper`
  - `file: models.py`; `line: 178-200`; `symbol: pedido item mapper`
  - `file: models.py`; `line: 211-231`; `symbol: pedido item mapper`
  - `file: models.py`; `line: 301-313`; `symbol: search result mapper`
- **Recommendation:** Centralizar mappers de dados em `models/mappers.py` e validações nos serviços.

### [MEDIUM] Long Methods
- **Location:**
  - `file: controllers.py`; `line: 24-62`; `symbol: criar_produto`
  - `file: models.py`; `line: 133-169`; `symbol: criar_pedido`
  - `file: models.py`; `line: 235-273`; `symbol: relatorio_vendas`
  - `file: models.py`; `line: 203-233`; `symbol: get_todos_pedidos`
- **Recommendation:** Quebrar métodos longos em funções especializadas de validação, cálculo e persistência.

### [MEDIUM] Poor Error Handling and Logging
- **Location:**
  - `file: controllers.py`; `line: 5-12`; `symbol: listar_produtos`
  - `file: controllers.py`; `line: 24-62`; `symbol: criar_produto`
  - `file: controllers.py`; `line: 98-109`; `symbol: deletar_produto`
  - `file: controllers.py`; `line: 146-165`; `symbol: criar_usuario`
  - `file: controllers.py`; `line: 167-186`; `symbol: login`
  - `file: controllers.py`; `line: 188-220`; `symbol: criar_pedido`
- **Recommendation:** Implementar middleware centralizado `middlewares/error_handler.py` com exceções customizadas (`AppError`) e módulo padrão `logging`.

### [MEDIUM] Weak Input Validation
- **Location:**
  - `file: controllers.py`; `line: 146-158`; `symbol: criar_usuario`
  - `file: controllers.py`; `line: 167-174`; `symbol: login`
  - `file: controllers.py`; `line: 188-201`; `symbol: criar_pedido`
- **Recommendation:** Validar formato de e-mail, tipos de dados, preços positivos e limites de campos.

### [LOW] Magic Numbers
- **Location:**
  - `file: models.py`; `line: 256-262`; `symbol: relatorio_vendas discount rules`
- **Recommendation:** Extrair constantes nomeadas `DESCONTO_FAIXAS` em `config/settings.py`.

### [LOW] Inconsistent Documentation / Settings
- **Location:**
  - `file: README.md`; `line: 12-12`; `symbol: documented port`
  - `file: app.py`; `line: 85-88`; `symbol: runtime port`
- **Recommendation:** Padronizar configurações via `config/settings.py` e documentar portas e variáveis.

### [LOW] Dead / Unused Imports
- **Location:**
  - `file: models.py`; `line: 1-2`; `symbol: unused sqlite3 import`
- **Recommendation:** Remover imports desnecessários.
